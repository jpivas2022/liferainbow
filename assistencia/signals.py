"""
=============================================================================
LIFE RAINBOW 2.0 - Signals de Integração Assistência ↔ Financeiro/Estoque
=============================================================================

Este módulo implementa a integração automática entre o sistema de Assistência
Técnica e os módulos Financeiro e Estoque:

1. Ao finalizar OS (status='finalizada') → Cria ContaReceber
2. Ao adicionar item com produto → Baixa automática do estoque
3. Ao cancelar OS → Reverte estoque e cancela ContaReceber

Autor: Life Rainbow Team
Data: Janeiro 2026
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.db import transaction

logger = logging.getLogger(__name__)


# =============================================================================
# INTEGRAÇÃO FINANCEIRO: OS → Contas a Receber
# =============================================================================

@receiver(post_save, sender='assistencia.OrdemServico')
def criar_conta_receber_os_finalizada(sender, instance, **kwargs):
    """
    Ao finalizar uma Ordem de Serviço, cria automaticamente uma ContaReceber.

    Apenas processa se:
    - Status mudou para 'finalizada'
    - Não está em garantia (em_garantia=False)
    - Valor total > 0
    """
    # Só criar conta a receber quando status for finalizada
    if instance.status != 'finalizada':
        return

    # Não criar conta para serviços em garantia
    if instance.em_garantia:
        logger.info(
            f"OS #{instance.numero} em garantia - sem cobrança"
        )
        return

    # Não criar conta se valor for zero
    if instance.valor_total <= 0:
        logger.info(
            f"OS #{instance.numero} com valor zero - sem conta a receber"
        )
        return

    try:
        from financeiro.models import ContaReceber

        # Verificar se já existe ContaReceber para esta OS (evitar duplicação)
        ja_existe = ContaReceber.objects.filter(
            ordem_servico=instance,
            documento=f"OS-{instance.numero}"
        ).exists()

        if ja_existe:
            logger.info(
                f"ContaReceber já existe para OS #{instance.numero}"
            )
            return

        with transaction.atomic():
            conta = ContaReceber.objects.create(
                descricao=f"Ordem de Serviço #{instance.numero}",
                cliente=instance.cliente,
                valor=instance.valor_total,
                data_emissao=instance.data_conclusao.date() if instance.data_conclusao else instance.data_abertura.date(),
                data_vencimento=instance.data_conclusao.date() if instance.data_conclusao else instance.data_abertura.date(),
                status=ContaReceber.STATUS_PAGA if instance.pago else ContaReceber.STATUS_PENDENTE,
                forma_pagamento=instance.forma_pagamento,
                documento=f"OS-{instance.numero}",
                ordem_servico=instance,
                consultor=instance.tecnico,
                data_pagamento=instance.data_pagamento if instance.pago else None,
                valor_pago=instance.valor_total if instance.pago else None,
                observacoes=f"Gerado automaticamente da OS #{instance.numero}. "
                            f"Equipamento: {instance.equipamento}. "
                            f"Problema: {instance.descricao_problema[:100]}...",
            )

            logger.info(
                f"✅ ContaReceber criada para OS #{instance.numero}: "
                f"R$ {instance.valor_total}"
            )

    except Exception as e:
        logger.error(
            f"❌ Erro ao criar ContaReceber para OS #{instance.numero}: {e}"
        )
        raise


@receiver(post_save, sender='assistencia.OrdemServico')
def sincronizar_pagamento_conta_receber_os(sender, instance, **kwargs):
    """
    Ao marcar OS como paga, sincroniza com a ContaReceber correspondente.
    """
    if not instance.pago:
        return

    try:
        from financeiro.models import ContaReceber

        # Buscar ContaReceber correspondente
        conta = ContaReceber.objects.filter(
            ordem_servico=instance,
            documento=f"OS-{instance.numero}"
        ).first()

        if not conta:
            return

        if conta.status != ContaReceber.STATUS_PAGA:
            conta.status = ContaReceber.STATUS_PAGA
            conta.data_pagamento = instance.data_pagamento
            conta.valor_pago = instance.valor_total
            conta.forma_pagamento = instance.forma_pagamento
            conta.save()

            logger.info(
                f"✅ ContaReceber sincronizada como paga: OS #{instance.numero}"
            )

    except Exception as e:
        logger.error(
            f"❌ Erro ao sincronizar pagamento da OS #{instance.numero}: {e}"
        )


@receiver(post_save, sender='assistencia.OrdemServico')
def cancelar_conta_receber_ao_cancelar_os(sender, instance, **kwargs):
    """
    Ao cancelar uma OS, cancela a ContaReceber correspondente (se existir).
    """
    if instance.status != 'cancelada':
        return

    try:
        from financeiro.models import ContaReceber

        with transaction.atomic():
            # Buscar ContaReceber pendente
            conta = ContaReceber.objects.filter(
                ordem_servico=instance,
                documento=f"OS-{instance.numero}",
                status=ContaReceber.STATUS_PENDENTE
            ).first()

            if conta:
                conta.status = ContaReceber.STATUS_CANCELADA
                conta.observacoes = (conta.observacoes or '') + '\nCancelado automaticamente - OS cancelada'
                conta.save()

                logger.info(
                    f"✅ ContaReceber cancelada para OS #{instance.numero}"
                )

    except Exception as e:
        logger.error(
            f"❌ Erro ao cancelar ContaReceber da OS #{instance.numero}: {e}"
        )


# =============================================================================
# INTEGRAÇÃO ESTOQUE: Item OS → Movimentação de Estoque
# =============================================================================

@receiver(post_save, sender='assistencia.ItemOrdemServico')
def baixar_estoque_ao_usar_peca(sender, instance, created, **kwargs):
    """
    Ao adicionar um ItemOrdemServico vinculado a um Produto do estoque,
    cria automaticamente uma MovimentacaoEstoque de SAÍDA (uso em OS).

    Apenas processa se:
    - É um novo item (created=True)
    - Tem produto vinculado (instance.produto is not None)
    - OS não está cancelada
    """
    if not created:
        return

    if not instance.produto:
        return

    # Não processar se OS está cancelada
    if instance.ordem_servico.status == 'cancelada':
        return

    try:
        from estoque.models import MovimentacaoEstoque

        with transaction.atomic():
            movimentacao = MovimentacaoEstoque.objects.create(
                produto=instance.produto,
                tipo=MovimentacaoEstoque.TIPO_SAIDA,
                motivo=MovimentacaoEstoque.MOTIVO_USO_INTERNO,
                quantidade=instance.quantidade,
                valor_unitario=instance.valor_unitario,
                ordem_servico=instance.ordem_servico,
                observacoes=f"OS #{instance.ordem_servico.numero} - Uso em assistência técnica",
                usuario=getattr(instance, '_usuario', None),
            )

            logger.info(
                f"✅ Estoque baixado (OS): "
                f"{instance.quantidade}x {instance.produto.nome} "
                f"(OS #{instance.ordem_servico.numero}) - "
                f"Estoque: {movimentacao.estoque_anterior} → {movimentacao.estoque_posterior}"
            )

    except Exception as e:
        logger.error(
            f"❌ Erro ao baixar estoque para OS #{instance.ordem_servico.numero}: {e}"
        )
        raise


@receiver(pre_delete, sender='assistencia.ItemOrdemServico')
def devolver_estoque_ao_remover_item_os(sender, instance, **kwargs):
    """
    Ao deletar um ItemOrdemServico vinculado a um Produto,
    cria automaticamente uma MovimentacaoEstoque de ENTRADA (devolução).

    Não processa se a OS está cancelada (evita duplicação com signal de cancelamento).
    """
    if not instance.produto:
        return

    if instance.ordem_servico.status == 'cancelada':
        return

    try:
        from estoque.models import MovimentacaoEstoque

        with transaction.atomic():
            movimentacao = MovimentacaoEstoque.objects.create(
                produto=instance.produto,
                tipo=MovimentacaoEstoque.TIPO_ENTRADA,
                motivo=MovimentacaoEstoque.MOTIVO_DEVOLUCAO,
                quantidade=instance.quantidade,
                valor_unitario=instance.valor_unitario,
                ordem_servico=instance.ordem_servico,
                observacoes=f"OS #{instance.ordem_servico.numero} - Item removido",
                usuario=getattr(instance, '_usuario', None),
            )

            logger.info(
                f"✅ Estoque devolvido (item OS removido): "
                f"{instance.quantidade}x {instance.produto.nome} - "
                f"Estoque: {movimentacao.estoque_anterior} → {movimentacao.estoque_posterior}"
            )

    except Exception as e:
        logger.error(
            f"❌ Erro ao devolver estoque para OS #{instance.ordem_servico.numero}: {e}"
        )
        raise


@receiver(post_save, sender='assistencia.OrdemServico')
def reverter_estoque_ao_cancelar_os(sender, instance, **kwargs):
    """
    Ao cancelar uma OS, reverte todas as movimentações de estoque.
    """
    if instance.status != 'cancelada':
        return

    itens_com_produto = instance.itens.filter(produto__isnull=False)

    if not itens_com_produto.exists():
        return

    try:
        from estoque.models import MovimentacaoEstoque

        with transaction.atomic():
            for item in itens_com_produto:
                # Verificar se já foi devolvido
                ja_devolvido = MovimentacaoEstoque.objects.filter(
                    ordem_servico=instance,
                    produto=item.produto,
                    tipo=MovimentacaoEstoque.TIPO_ENTRADA,
                    motivo=MovimentacaoEstoque.MOTIVO_DEVOLUCAO,
                    observacoes__icontains='Cancelamento'
                ).exists()

                if ja_devolvido:
                    continue

                movimentacao = MovimentacaoEstoque.objects.create(
                    produto=item.produto,
                    tipo=MovimentacaoEstoque.TIPO_ENTRADA,
                    motivo=MovimentacaoEstoque.MOTIVO_DEVOLUCAO,
                    quantidade=item.quantidade,
                    valor_unitario=item.valor_unitario,
                    ordem_servico=instance,
                    observacoes=f"Cancelamento OS #{instance.numero}",
                    usuario=getattr(instance, '_usuario', None),
                )

                logger.info(
                    f"✅ Estoque revertido (cancelamento OS): "
                    f"{item.quantidade}x {item.produto.nome}"
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

def calcular_resumo_financeiro_os(ordem_servico):
    """
    Calcula resumo financeiro de uma ordem de serviço.

    Args:
        ordem_servico: Instância da OrdemServico

    Returns:
        dict: Resumo financeiro
    """
    return {
        'os_numero': ordem_servico.numero,
        'cliente': ordem_servico.cliente.nome,
        'equipamento': str(ordem_servico.equipamento),
        'valor_mao_obra': float(ordem_servico.valor_mao_obra),
        'valor_pecas': float(ordem_servico.valor_pecas),
        'desconto': float(ordem_servico.desconto),
        'valor_total': float(ordem_servico.valor_total),
        'em_garantia': ordem_servico.em_garantia,
        'pago': ordem_servico.pago,
        'forma_pagamento': ordem_servico.forma_pagamento,
        'status': ordem_servico.status,
    }


def gerar_conta_receber_os_retroativa(ordem_servico):
    """
    Gera ContaReceber para uma OS já finalizada que não teve conta criada.
    Útil para OS importadas ou criadas sem signals.

    Args:
        ordem_servico: Instância da OrdemServico

    Returns:
        ContaReceber ou None
    """
    from financeiro.models import ContaReceber

    if ordem_servico.status != 'finalizada':
        return None

    if ordem_servico.em_garantia:
        return None

    if ordem_servico.valor_total <= 0:
        return None

    # Verificar se já existe
    ja_existe = ContaReceber.objects.filter(
        ordem_servico=ordem_servico,
        documento=f"OS-{ordem_servico.numero}"
    ).exists()

    if ja_existe:
        return None

    return ContaReceber.objects.create(
        descricao=f"Ordem de Serviço #{ordem_servico.numero} (retroativo)",
        cliente=ordem_servico.cliente,
        valor=ordem_servico.valor_total,
        data_emissao=ordem_servico.data_conclusao.date() if ordem_servico.data_conclusao else ordem_servico.data_abertura.date(),
        data_vencimento=ordem_servico.data_conclusao.date() if ordem_servico.data_conclusao else ordem_servico.data_abertura.date(),
        status=ContaReceber.STATUS_PAGA if ordem_servico.pago else ContaReceber.STATUS_PENDENTE,
        forma_pagamento=ordem_servico.forma_pagamento,
        documento=f"OS-{ordem_servico.numero}",
        ordem_servico=ordem_servico,
        consultor=ordem_servico.tecnico,
        data_pagamento=ordem_servico.data_pagamento if ordem_servico.pago else None,
        valor_pago=ordem_servico.valor_total if ordem_servico.pago else None,
    )
