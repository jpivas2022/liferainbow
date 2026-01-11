"""
=============================================================================
LIFE RAINBOW 2.0 - Signals de Integração Alugueis ↔ Financeiro
=============================================================================

Este módulo implementa a integração automática entre o sistema de Aluguéis
e o módulo Financeiro:

1. Ao criar ParcelaAluguel → Cria automaticamente ContaReceber
2. Ao atualizar status da parcela → Sincroniza ContaReceber
3. Ao cancelar contrato → Cancela ContaReceber pendentes

Autor: Life Rainbow Team
Data: Janeiro 2026
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.db import transaction

logger = logging.getLogger(__name__)


# =============================================================================
# INTEGRAÇÃO FINANCEIRO: Aluguéis → Contas a Receber
# =============================================================================

@receiver(post_save, sender='alugueis.ParcelaAluguel')
def criar_conta_receber_aluguel(sender, instance, created, **kwargs):
    """
    Ao criar uma ParcelaAluguel, cria automaticamente uma ContaReceber.

    A ContaReceber é vinculada ao ContratoAluguel e permite:
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
            contrato_aluguel=instance.contrato,
            documento=f"ALUGUEL-{instance.contrato.numero}-{instance.numero}"
        ).exists()

        if ja_existe:
            logger.info(
                f"ContaReceber já existe para Parcela {instance.numero} do Aluguel #{instance.contrato.numero}"
            )
            return

        with transaction.atomic():
            conta = ContaReceber.objects.create(
                descricao=f"Aluguel #{instance.contrato.numero} - Parcela {instance.numero}/{instance.contrato.duracao_meses} ({instance.mes_referencia})",
                cliente=instance.contrato.cliente,
                valor=instance.valor,
                data_emissao=instance.contrato.data_inicio,
                data_vencimento=instance.data_vencimento,
                status=ContaReceber.STATUS_PENDENTE,
                forma_pagamento='boleto',  # Padrão para aluguéis
                documento=f"ALUGUEL-{instance.contrato.numero}-{instance.numero}",
                contrato_aluguel=instance.contrato,
                consultor=instance.contrato.consultor,
                observacoes=f"Gerado automaticamente do Contrato de Aluguel #{instance.contrato.numero}",
            )

            logger.info(
                f"✅ ContaReceber criada para Aluguel #{instance.contrato.numero} "
                f"Parcela {instance.numero}: R$ {instance.valor}"
            )

    except Exception as e:
        logger.error(
            f"❌ Erro ao criar ContaReceber para Aluguel #{instance.contrato.numero}: {e}"
        )
        raise


@receiver(post_save, sender='alugueis.ParcelaAluguel')
def sincronizar_status_conta_receber_aluguel(sender, instance, **kwargs):
    """
    Ao atualizar status de uma ParcelaAluguel, sincroniza com a ContaReceber correspondente.

    - Parcela paga → ContaReceber paga
    - Parcela atrasada → ContaReceber atrasada
    - Parcela cancelada → ContaReceber cancelada
    """
    try:
        from financeiro.models import ContaReceber

        # Buscar ContaReceber correspondente
        conta = ContaReceber.objects.filter(
            contrato_aluguel=instance.contrato,
            documento=f"ALUGUEL-{instance.contrato.numero}-{instance.numero}"
        ).first()

        if not conta:
            return

        # Mapear status da ParcelaAluguel para ContaReceber
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
            conta.forma_pagamento = instance.forma_pagamento or conta.forma_pagamento
            conta.save()

            logger.info(
                f"✅ ContaReceber sincronizada: Aluguel #{instance.contrato.numero} "
                f"Parcela {instance.numero} → {novo_status}"
            )

    except Exception as e:
        logger.error(
            f"❌ Erro ao sincronizar ContaReceber do Aluguel #{instance.contrato.numero}: {e}"
        )


@receiver(post_save, sender='alugueis.ContratoAluguel')
def cancelar_contas_receber_ao_cancelar_contrato(sender, instance, **kwargs):
    """
    Ao cancelar um ContratoAluguel, cancela todas as ContaReceber pendentes.

    Parcelas já pagas permanecem com status 'paga'.
    """
    if instance.status != 'cancelado':
        return

    try:
        from financeiro.models import ContaReceber

        with transaction.atomic():
            # Buscar todas as ContaReceber pendentes deste contrato
            contas_pendentes = ContaReceber.objects.filter(
                contrato_aluguel=instance,
                status=ContaReceber.STATUS_PENDENTE
            )

            quantidade = contas_pendentes.count()

            if quantidade > 0:
                contas_pendentes.update(
                    status=ContaReceber.STATUS_CANCELADA,
                    observacoes='Cancelado automaticamente - Contrato cancelado'
                )

                logger.info(
                    f"✅ {quantidade} ContaReceber canceladas para "
                    f"Contrato #{instance.numero} (cancelamento do contrato)"
                )

    except Exception as e:
        logger.error(
            f"❌ Erro ao cancelar ContaReceber do Contrato #{instance.numero}: {e}"
        )


@receiver(post_save, sender='alugueis.ContratoAluguel')
def criar_historico_contrato(sender, instance, created, **kwargs):
    """
    Cria registro de histórico para eventos importantes do contrato.
    """
    try:
        from alugueis.models import HistoricoAluguel

        if created:
            HistoricoAluguel.objects.create(
                contrato=instance,
                evento=HistoricoAluguel.EVENTO_CRIACAO,
                descricao=f"Contrato #{instance.numero} criado. "
                          f"Cliente: {instance.cliente.nome}. "
                          f"Valor: R$ {instance.valor_mensal}/mês. "
                          f"Duração: {instance.duracao_meses} meses.",
                automatico=True
            )
            logger.info(f"✅ Histórico de criação registrado para Contrato #{instance.numero}")

    except Exception as e:
        logger.error(f"❌ Erro ao criar histórico do Contrato #{instance.numero}: {e}")


# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def gerar_contas_receber_contrato(contrato):
    """
    Gera ContaReceber para todas as parcelas de um contrato.
    Útil para contratos importados ou criados sem signals.

    Args:
        contrato: Instância do ContratoAluguel

    Returns:
        int: Quantidade de ContaReceber criadas
    """
    from financeiro.models import ContaReceber

    criadas = 0

    for parcela in contrato.parcelas.all():
        # Verificar se já existe
        ja_existe = ContaReceber.objects.filter(
            contrato_aluguel=contrato,
            documento=f"ALUGUEL-{contrato.numero}-{parcela.numero}"
        ).exists()

        if not ja_existe:
            ContaReceber.objects.create(
                descricao=f"Aluguel #{contrato.numero} - Parcela {parcela.numero}/{contrato.duracao_meses}",
                cliente=contrato.cliente,
                valor=parcela.valor,
                data_emissao=contrato.data_inicio,
                data_vencimento=parcela.data_vencimento,
                status=parcela.status,
                forma_pagamento='boleto',
                documento=f"ALUGUEL-{contrato.numero}-{parcela.numero}",
                contrato_aluguel=contrato,
                consultor=contrato.consultor,
                data_pagamento=parcela.data_pagamento,
                valor_pago=parcela.valor_pago,
            )
            criadas += 1

    return criadas


def calcular_resumo_financeiro_aluguel(contrato):
    """
    Calcula resumo financeiro de um contrato de aluguel.

    Args:
        contrato: Instância do ContratoAluguel

    Returns:
        dict: Resumo financeiro
    """
    from django.db.models import Sum

    parcelas = contrato.parcelas.all()

    total_contrato = parcelas.aggregate(total=Sum('valor'))['total'] or 0
    total_pago = parcelas.filter(status='paga').aggregate(total=Sum('valor_pago'))['total'] or 0
    total_pendente = parcelas.filter(status__in=['pendente', 'atrasada']).aggregate(total=Sum('valor'))['total'] or 0
    total_atrasado = parcelas.filter(status='atrasada').aggregate(total=Sum('valor'))['total'] or 0

    return {
        'contrato_numero': contrato.numero,
        'cliente': contrato.cliente.nome,
        'total_contrato': float(total_contrato),
        'total_pago': float(total_pago),
        'total_pendente': float(total_pendente),
        'total_atrasado': float(total_atrasado),
        'percentual_pago': round((total_pago / total_contrato * 100), 1) if total_contrato > 0 else 0,
        'parcelas_pagas': parcelas.filter(status='paga').count(),
        'parcelas_pendentes': parcelas.filter(status='pendente').count(),
        'parcelas_atrasadas': parcelas.filter(status='atrasada').count(),
        'duracao_meses': contrato.duracao_meses,
    }
