"""
=============================================================================
LIFE RAINBOW 2.0 - Signals de Integração Estoque ↔ Ordem de Serviço
=============================================================================

Este módulo implementa a integração automática entre o sistema de Ordem de
Serviço e o controle de Estoque:

1. Ao adicionar item com produto à OS → Baixa automática do estoque
2. Ao remover item da OS → Devolução automática ao estoque
3. Ao cancelar OS → Reverte todas as movimentações de estoque

Autor: Life Rainbow Team
Data: Janeiro 2026
"""

import logging
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.db import transaction

from .models import Produto, MovimentacaoEstoque

logger = logging.getLogger(__name__)


# =============================================================================
# SIGNAL: Baixa automática ao adicionar item à OS
# =============================================================================

@receiver(post_save, sender='assistencia.ItemOrdemServico')
def baixar_estoque_ao_adicionar_item(sender, instance, created, **kwargs):
    """
    Ao criar um ItemOrdemServico vinculado a um Produto,
    cria automaticamente uma MovimentacaoEstoque de SAÍDA.

    Apenas processa se:
    - É um novo item (created=True)
    - Tem produto vinculado (instance.produto is not None)
    - Não é edição de item existente
    """
    if not created:
        return

    if not instance.produto:
        logger.info(
            f"Item OS #{instance.ordem_servico.numero} sem produto vinculado - "
            f"sem movimentação de estoque"
        )
        return

    try:
        with transaction.atomic():
            # Criar movimentação de saída
            movimentacao = MovimentacaoEstoque.objects.create(
                produto=instance.produto,
                tipo=MovimentacaoEstoque.TIPO_SAIDA,
                motivo=MovimentacaoEstoque.MOTIVO_MANUTENCAO,
                quantidade=instance.quantidade,
                valor_unitario=instance.valor_unitario,
                ordem_servico=instance.ordem_servico,
                observacoes=f"Baixa automática - Item: {instance.descricao}",
                usuario=getattr(instance, '_usuario', None),
            )

            logger.info(
                f"✅ Estoque baixado automaticamente: "
                f"{instance.quantidade}x {instance.produto.nome} "
                f"(OS #{instance.ordem_servico.numero}) - "
                f"Estoque: {movimentacao.estoque_anterior} → {movimentacao.estoque_posterior}"
            )

    except Exception as e:
        logger.error(
            f"❌ Erro ao baixar estoque para item OS #{instance.ordem_servico.numero}: {e}"
        )
        raise


# =============================================================================
# SIGNAL: Devolução ao remover item da OS
# =============================================================================

@receiver(pre_delete, sender='assistencia.ItemOrdemServico')
def devolver_estoque_ao_remover_item(sender, instance, **kwargs):
    """
    Ao deletar um ItemOrdemServico vinculado a um Produto,
    cria automaticamente uma MovimentacaoEstoque de ENTRADA (devolução).

    Apenas processa se:
    - Tem produto vinculado
    - A OS não está cancelada (evita duplicação com signal de cancelamento)
    """
    if not instance.produto:
        return

    # Verificar se a OS está sendo cancelada (evita duplicação)
    if instance.ordem_servico.status == 'cancelada':
        logger.info(
            f"Item removido de OS cancelada - devolução já processada pelo cancelamento"
        )
        return

    try:
        with transaction.atomic():
            # Criar movimentação de entrada (devolução)
            movimentacao = MovimentacaoEstoque.objects.create(
                produto=instance.produto,
                tipo=MovimentacaoEstoque.TIPO_ENTRADA,
                motivo=MovimentacaoEstoque.MOTIVO_DEVOLUCAO,
                quantidade=instance.quantidade,
                valor_unitario=instance.valor_unitario,
                ordem_servico=instance.ordem_servico,
                observacoes=f"Devolução automática - Item removido: {instance.descricao}",
                usuario=getattr(instance, '_usuario', None),
            )

            logger.info(
                f"✅ Estoque devolvido automaticamente: "
                f"{instance.quantidade}x {instance.produto.nome} "
                f"(OS #{instance.ordem_servico.numero}) - "
                f"Estoque: {movimentacao.estoque_anterior} → {movimentacao.estoque_posterior}"
            )

    except Exception as e:
        logger.error(
            f"❌ Erro ao devolver estoque para item OS #{instance.ordem_servico.numero}: {e}"
        )
        raise


# =============================================================================
# SIGNAL: Reverter estoque ao cancelar OS
# =============================================================================

@receiver(post_save, sender='assistencia.OrdemServico')
def reverter_estoque_ao_cancelar_os(sender, instance, **kwargs):
    """
    Ao mudar status da OS para 'cancelada', reverte todas as
    movimentações de estoque relacionadas.

    Processa apenas se:
    - Status atual é 'cancelada'
    - Há itens com produtos vinculados
    """
    # Verificar se está sendo cancelada
    if instance.status != 'cancelada':
        return

    # Buscar itens com produtos
    itens_com_produto = instance.itens.filter(produto__isnull=False)

    if not itens_com_produto.exists():
        logger.info(f"OS #{instance.numero} cancelada sem itens de estoque")
        return

    try:
        with transaction.atomic():
            for item in itens_com_produto:
                # Verificar se já existe movimentação de devolução para este cancelamento
                ja_devolvido = MovimentacaoEstoque.objects.filter(
                    ordem_servico=instance,
                    produto=item.produto,
                    tipo=MovimentacaoEstoque.TIPO_ENTRADA,
                    motivo=MovimentacaoEstoque.MOTIVO_DEVOLUCAO,
                    observacoes__icontains='Cancelamento OS'
                ).exists()

                if ja_devolvido:
                    logger.info(
                        f"Item {item.produto.nome} já devolvido para OS #{instance.numero}"
                    )
                    continue

                # Criar movimentação de entrada (devolução por cancelamento)
                movimentacao = MovimentacaoEstoque.objects.create(
                    produto=item.produto,
                    tipo=MovimentacaoEstoque.TIPO_ENTRADA,
                    motivo=MovimentacaoEstoque.MOTIVO_DEVOLUCAO,
                    quantidade=item.quantidade,
                    valor_unitario=item.valor_unitario,
                    ordem_servico=instance,
                    observacoes=f"Cancelamento OS #{instance.numero} - Item: {item.descricao}",
                    usuario=getattr(instance, '_usuario', None),
                )

                logger.info(
                    f"✅ Estoque revertido (cancelamento): "
                    f"{item.quantidade}x {item.produto.nome} "
                    f"(OS #{instance.numero}) - "
                    f"Estoque: {movimentacao.estoque_anterior} → {movimentacao.estoque_posterior}"
                )

            logger.info(
                f"✅ OS #{instance.numero} cancelada - "
                f"{itens_com_produto.count()} itens devolvidos ao estoque"
            )

    except Exception as e:
        logger.error(
            f"❌ Erro ao reverter estoque para OS #{instance.numero}: {e}"
        )
        raise


# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def validar_estoque_disponivel(produto, quantidade):
    """
    Valida se há estoque disponível para a quantidade solicitada.

    Args:
        produto: Instância do Produto
        quantidade: Quantidade desejada

    Returns:
        tuple: (bool disponivel, str mensagem)
    """
    if not produto:
        return True, "Produto não vinculado - sem validação de estoque"

    if produto.estoque_atual >= quantidade:
        return True, f"Estoque disponível: {produto.estoque_atual}"

    return False, (
        f"Estoque insuficiente para {produto.nome}: "
        f"disponível {produto.estoque_atual}, solicitado {quantidade}"
    )


def calcular_impacto_estoque(ordem_servico):
    """
    Calcula o impacto total no estoque de uma OS.

    Args:
        ordem_servico: Instância da OrdemServico

    Returns:
        dict: Resumo do impacto no estoque
    """
    itens = ordem_servico.itens.filter(produto__isnull=False)

    impacto = {
        'total_itens': itens.count(),
        'valor_total': sum(item.valor_total for item in itens),
        'produtos': []
    }

    for item in itens:
        impacto['produtos'].append({
            'produto_id': item.produto.id,
            'produto_nome': item.produto.nome,
            'quantidade': item.quantidade,
            'valor_unitario': float(item.valor_unitario),
            'valor_total': float(item.valor_total),
            'estoque_atual': item.produto.estoque_atual,
            'estoque_apos': item.produto.estoque_atual - item.quantidade,
        })

    return impacto
