"""
=============================================================================
LIFE RAINBOW 2.0 - Signals de Integração Vendas ↔ Estoque
=============================================================================

Este módulo implementa a integração automática entre o sistema de Vendas
e o controle de Estoque:

1. Ao adicionar item com produto à Venda → Baixa automática do estoque
2. Ao remover item da Venda → Devolução automática ao estoque
3. Ao cancelar Venda → Reverte todas as movimentações de estoque

Autor: Life Rainbow Team
Data: Janeiro 2026
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.db import transaction

logger = logging.getLogger(__name__)


# =============================================================================
# SIGNAL: Baixa automática ao adicionar item à Venda
# =============================================================================

@receiver(post_save, sender='vendas.ItemVenda')
def baixar_estoque_ao_vender(sender, instance, created, **kwargs):
    """
    Ao criar um ItemVenda vinculado a um Produto do estoque,
    cria automaticamente uma MovimentacaoEstoque de SAÍDA (venda).

    Apenas processa se:
    - É um novo item (created=True)
    - Tem produto vinculado (instance.produto is not None)
    """
    if not created:
        return

    if not instance.produto:
        # Item é equipamento Rainbow, não produto do estoque
        return

    try:
        # Import aqui para evitar circular imports
        from estoque.models import MovimentacaoEstoque

        with transaction.atomic():
            # Criar movimentação de saída (venda)
            movimentacao = MovimentacaoEstoque.objects.create(
                produto=instance.produto,
                tipo=MovimentacaoEstoque.TIPO_SAIDA,
                motivo=MovimentacaoEstoque.MOTIVO_VENDA,
                quantidade=instance.quantidade,
                valor_unitario=instance.valor_unitario,
                venda=instance.venda,
                observacoes=f"Venda #{instance.venda.numero} - Baixa automática",
                usuario=getattr(instance, '_usuario', None),
            )

            logger.info(
                f"✅ Estoque baixado (venda): "
                f"{instance.quantidade}x {instance.produto.nome} "
                f"(Venda #{instance.venda.numero}) - "
                f"Estoque: {movimentacao.estoque_anterior} → {movimentacao.estoque_posterior}"
            )

    except Exception as e:
        logger.error(
            f"❌ Erro ao baixar estoque para venda #{instance.venda.numero}: {e}"
        )
        raise


# =============================================================================
# SIGNAL: Devolução ao remover item da Venda
# =============================================================================

@receiver(pre_delete, sender='vendas.ItemVenda')
def devolver_estoque_ao_remover_item_venda(sender, instance, **kwargs):
    """
    Ao deletar um ItemVenda vinculado a um Produto,
    cria automaticamente uma MovimentacaoEstoque de ENTRADA (devolução).

    Apenas processa se:
    - Tem produto vinculado
    - A Venda não está cancelada (evita duplicação com signal de cancelamento)
    """
    if not instance.produto:
        return

    # Verificar se a Venda está sendo cancelada (evita duplicação)
    if instance.venda.status == 'cancelada':
        logger.info(
            f"Item removido de Venda cancelada - devolução já processada pelo cancelamento"
        )
        return

    try:
        from estoque.models import MovimentacaoEstoque

        with transaction.atomic():
            # Criar movimentação de entrada (devolução)
            movimentacao = MovimentacaoEstoque.objects.create(
                produto=instance.produto,
                tipo=MovimentacaoEstoque.TIPO_ENTRADA,
                motivo=MovimentacaoEstoque.MOTIVO_DEVOLUCAO,
                quantidade=instance.quantidade,
                valor_unitario=instance.valor_unitario,
                venda=instance.venda,
                observacoes=f"Venda #{instance.venda.numero} - Item removido",
                usuario=getattr(instance, '_usuario', None),
            )

            logger.info(
                f"✅ Estoque devolvido (item removido): "
                f"{instance.quantidade}x {instance.produto.nome} "
                f"(Venda #{instance.venda.numero}) - "
                f"Estoque: {movimentacao.estoque_anterior} → {movimentacao.estoque_posterior}"
            )

    except Exception as e:
        logger.error(
            f"❌ Erro ao devolver estoque para venda #{instance.venda.numero}: {e}"
        )
        raise


# =============================================================================
# SIGNAL: Reverter estoque ao cancelar Venda
# =============================================================================

@receiver(post_save, sender='vendas.Venda')
def reverter_estoque_ao_cancelar_venda(sender, instance, **kwargs):
    """
    Ao mudar status da Venda para 'cancelada', reverte todas as
    movimentações de estoque relacionadas.

    Processa apenas se:
    - Status atual é 'cancelada'
    - Há itens com produtos vinculados
    """
    # Verificar se está sendo cancelada
    if instance.status != 'cancelada':
        return

    # Buscar itens com produtos do estoque
    itens_com_produto = instance.itens.filter(produto__isnull=False)

    if not itens_com_produto.exists():
        logger.info(f"Venda #{instance.numero} cancelada sem itens de estoque")
        return

    try:
        from estoque.models import MovimentacaoEstoque

        with transaction.atomic():
            for item in itens_com_produto:
                # Verificar se já existe movimentação de devolução para este cancelamento
                ja_devolvido = MovimentacaoEstoque.objects.filter(
                    venda=instance,
                    produto=item.produto,
                    tipo=MovimentacaoEstoque.TIPO_ENTRADA,
                    motivo=MovimentacaoEstoque.MOTIVO_DEVOLUCAO,
                    observacoes__icontains='Cancelamento'
                ).exists()

                if ja_devolvido:
                    logger.info(
                        f"Item {item.produto.nome} já devolvido para Venda #{instance.numero}"
                    )
                    continue

                # Criar movimentação de entrada (devolução por cancelamento)
                movimentacao = MovimentacaoEstoque.objects.create(
                    produto=item.produto,
                    tipo=MovimentacaoEstoque.TIPO_ENTRADA,
                    motivo=MovimentacaoEstoque.MOTIVO_DEVOLUCAO,
                    quantidade=item.quantidade,
                    valor_unitario=item.valor_unitario,
                    venda=instance,
                    observacoes=f"Cancelamento Venda #{instance.numero}",
                    usuario=getattr(instance, '_usuario', None),
                )

                logger.info(
                    f"✅ Estoque revertido (cancelamento): "
                    f"{item.quantidade}x {item.produto.nome} "
                    f"(Venda #{instance.numero}) - "
                    f"Estoque: {movimentacao.estoque_anterior} → {movimentacao.estoque_posterior}"
                )

            logger.info(
                f"✅ Venda #{instance.numero} cancelada - "
                f"{itens_com_produto.count()} itens devolvidos ao estoque"
            )

    except Exception as e:
        logger.error(
            f"❌ Erro ao reverter estoque para Venda #{instance.numero}: {e}"
        )
        raise


# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def validar_estoque_para_venda(produto, quantidade):
    """
    Valida se há estoque disponível para a venda.

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


def calcular_impacto_estoque_venda(venda):
    """
    Calcula o impacto total no estoque de uma Venda.

    Args:
        venda: Instância da Venda

    Returns:
        dict: Resumo do impacto no estoque
    """
    itens = venda.itens.filter(produto__isnull=False)

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


# =============================================================================
# INTEGRAÇÃO FINANCEIRO: Vendas → Contas a Receber
# =============================================================================

@receiver(post_save, sender='vendas.Parcela')
def criar_conta_receber_por_parcela(sender, instance, created, **kwargs):
    """
    Ao criar uma Parcela de Venda, cria automaticamente uma ContaReceber.

    A ContaReceber é vinculada à Venda e permite:
    - Rastreamento financeiro completo
    - Relatórios de contas a receber
    - Integração com caixa (Movimentacao)
    """
    if not created:
        return

    try:
        from financeiro.models import ContaReceber

        # Verificar se já existe ContaReceber para esta parcela (evitar duplicação)
        ja_existe = ContaReceber.objects.filter(
            venda=instance.venda,
            documento=f"PARCELA-{instance.venda.numero}-{instance.numero}"
        ).exists()

        if ja_existe:
            logger.info(
                f"ContaReceber já existe para Parcela {instance.numero} da Venda #{instance.venda.numero}"
            )
            return

        with transaction.atomic():
            conta = ContaReceber.objects.create(
                descricao=f"Venda #{instance.venda.numero} - Parcela {instance.numero}/{instance.venda.numero_parcelas}",
                cliente=instance.venda.cliente,
                valor=instance.valor,
                data_emissao=instance.venda.data_venda,
                data_vencimento=instance.data_vencimento,
                status=ContaReceber.STATUS_PENDENTE,
                forma_pagamento=instance.venda.forma_pagamento,
                documento=f"PARCELA-{instance.venda.numero}-{instance.numero}",
                venda=instance.venda,
                consultor=instance.venda.vendedor,
                pontos=instance.venda.pontos / instance.venda.numero_parcelas if instance.venda.numero_parcelas > 0 else 0,
                observacoes=f"Gerado automaticamente da Venda #{instance.venda.numero}",
            )

            logger.info(
                f"✅ ContaReceber criada para Venda #{instance.venda.numero} "
                f"Parcela {instance.numero}: R$ {instance.valor}"
            )

    except Exception as e:
        logger.error(
            f"❌ Erro ao criar ContaReceber para Venda #{instance.venda.numero}: {e}"
        )
        raise


@receiver(post_save, sender='vendas.Parcela')
def sincronizar_status_conta_receber(sender, instance, **kwargs):
    """
    Ao atualizar status de uma Parcela, sincroniza com a ContaReceber correspondente.

    - Parcela paga → ContaReceber paga
    - Parcela cancelada → ContaReceber cancelada
    """
    try:
        from financeiro.models import ContaReceber

        # Buscar ContaReceber correspondente
        conta = ContaReceber.objects.filter(
            venda=instance.venda,
            documento=f"PARCELA-{instance.venda.numero}-{instance.numero}"
        ).first()

        if not conta:
            return

        # Mapear status da Parcela para ContaReceber
        mapeamento_status = {
            'pendente': ContaReceber.STATUS_PENDENTE,
            'paga': ContaReceber.STATUS_PAGA,
            'atrasada': ContaReceber.STATUS_ATRASADA,
            'cancelada': ContaReceber.STATUS_CANCELADA,
        }

        novo_status = mapeamento_status.get(instance.status, ContaReceber.STATUS_PENDENTE)

        if conta.status != novo_status:
            conta.status = novo_status
            conta.data_pagamento = instance.data_pagamento
            conta.valor_pago = instance.valor_pago
            conta.juros = instance.juros
            conta.multa = instance.multa
            conta.save()

            logger.info(
                f"✅ ContaReceber sincronizada: Venda #{instance.venda.numero} "
                f"Parcela {instance.numero} → {novo_status}"
            )

    except Exception as e:
        logger.error(
            f"❌ Erro ao sincronizar ContaReceber da Venda #{instance.venda.numero}: {e}"
        )


@receiver(post_save, sender='vendas.Venda')
def criar_contas_receber_venda_a_vista(sender, instance, created, **kwargs):
    """
    Para vendas à vista (1 parcela), cria automaticamente a ContaReceber
    se não houver parcelas criadas manualmente.

    Útil quando a Venda é criada diretamente sem gerar Parcelas.
    """
    if not created:
        return

    # Verificar se é venda à vista ou se parcelas serão geradas depois
    if instance.numero_parcelas == 1 and not instance.parcelas.exists():
        try:
            from financeiro.models import ContaReceber

            # Verificar se já existe ContaReceber
            ja_existe = ContaReceber.objects.filter(
                venda=instance,
                documento=f"VENDA-{instance.numero}"
            ).exists()

            if ja_existe:
                return

            with transaction.atomic():
                conta = ContaReceber.objects.create(
                    descricao=f"Venda #{instance.numero} - À Vista",
                    cliente=instance.cliente,
                    valor=instance.valor_total,
                    data_emissao=instance.data_venda,
                    data_vencimento=instance.data_primeiro_vencimento or instance.data_venda,
                    status=ContaReceber.STATUS_PENDENTE,
                    forma_pagamento=instance.forma_pagamento,
                    documento=f"VENDA-{instance.numero}",
                    venda=instance,
                    consultor=instance.vendedor,
                    pontos=instance.pontos,
                    observacoes=f"Venda à vista - Gerado automaticamente",
                )

                logger.info(
                    f"✅ ContaReceber criada para Venda à Vista #{instance.numero}: "
                    f"R$ {instance.valor_total}"
                )

        except Exception as e:
            logger.error(
                f"❌ Erro ao criar ContaReceber para Venda à Vista #{instance.numero}: {e}"
            )
