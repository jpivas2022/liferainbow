"""
=============================================================================
LIFE RAINBOW 2.0 - Módulo de Assistência Técnica
Models: OrdemServico, ItemOrdemServico
=============================================================================
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class OrdemServico(models.Model):
    """
    Ordens de serviço para assistência técnica.
    """

    STATUS_ABERTA = 'aberta'
    STATUS_ANALISE = 'analise'
    STATUS_ORCAMENTO = 'orcamento'
    STATUS_APROVADO = 'aprovado'
    STATUS_EXECUCAO = 'execucao'
    STATUS_FINALIZADA = 'finalizada'
    STATUS_ENTREGUE = 'entregue'
    STATUS_CANCELADA = 'cancelada'
    STATUS_CHOICES = [
        (STATUS_ABERTA, 'Aberta'),
        (STATUS_ANALISE, 'Em Análise'),
        (STATUS_ORCAMENTO, 'Orçamento Enviado'),
        (STATUS_APROVADO, 'Aprovado'),
        (STATUS_EXECUCAO, 'Em Execução'),
        (STATUS_FINALIZADA, 'Finalizada'),
        (STATUS_ENTREGUE, 'Entregue'),
        (STATUS_CANCELADA, 'Cancelada'),
    ]

    PRIORIDADE_BAIXA = 'baixa'
    PRIORIDADE_NORMAL = 'normal'
    PRIORIDADE_ALTA = 'alta'
    PRIORIDADE_URGENTE = 'urgente'
    PRIORIDADE_CHOICES = [
        (PRIORIDADE_BAIXA, 'Baixa'),
        (PRIORIDADE_NORMAL, 'Normal'),
        (PRIORIDADE_ALTA, 'Alta'),
        (PRIORIDADE_URGENTE, 'Urgente'),
    ]

    # Identificação
    numero = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Número OS',
        db_index=True
    )

    # Cliente e Equipamento
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='ordens_servico',
        verbose_name='Cliente'
    )
    equipamento = models.ForeignKey(
        'equipamentos.Equipamento',
        on_delete=models.PROTECT,
        related_name='ordens_servico',
        verbose_name='Equipamento'
    )

    # Problema
    descricao_problema = models.TextField(
        verbose_name='Descrição do Problema'
    )
    diagnostico = models.TextField(
        null=True,
        blank=True,
        verbose_name='Diagnóstico Técnico'
    )

    # Status e Prioridade
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ABERTA,
        verbose_name='Status',
        db_index=True
    )
    prioridade = models.CharField(
        max_length=10,
        choices=PRIORIDADE_CHOICES,
        default=PRIORIDADE_NORMAL,
        verbose_name='Prioridade'
    )

    # Garantia
    em_garantia = models.BooleanField(
        default=False,
        verbose_name='Em Garantia'
    )

    # Datas
    data_abertura = models.DateTimeField(
        default=timezone.now,
        verbose_name='Data de Abertura'
    )
    data_previsao = models.DateField(
        null=True,
        blank=True,
        verbose_name='Previsão de Conclusão'
    )
    data_conclusao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Conclusão'
    )
    data_entrega = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Entrega'
    )

    # Valores
    valor_mao_obra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Valor Mão de Obra'
    )
    valor_pecas = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Valor Peças'
    )
    desconto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Desconto'
    )
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Valor Total'
    )

    # Pagamento
    pago = models.BooleanField(
        default=False,
        verbose_name='Pago'
    )
    data_pagamento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data do Pagamento'
    )
    forma_pagamento = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Forma de Pagamento'
    )

    # Responsáveis
    tecnico = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ordens_servico_tecnico',
        verbose_name='Técnico Responsável'
    )
    atendente = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ordens_servico_atendente',
        verbose_name='Atendente'
    )

    # Serviços realizados
    servicos_realizados = models.TextField(
        null=True,
        blank=True,
        verbose_name='Serviços Realizados'
    )

    # Garantia do serviço
    garantia_servico_dias = models.IntegerField(
        default=90,
        verbose_name='Garantia do Serviço (dias)'
    )

    observacoes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observações'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ordem de Serviço'
        verbose_name_plural = 'Ordens de Serviço'
        ordering = ['-data_abertura']

    def __str__(self):
        return f"OS #{self.numero} - {self.cliente.nome}"

    def save(self, *args, **kwargs):
        # Gerar número da OS automaticamente
        if not self.numero:
            ultimo = OrdemServico.objects.order_by('-id').first()
            novo_id = (ultimo.id + 1) if ultimo else 1
            self.numero = f"OS{timezone.now().year}{novo_id:06d}"

        # Calcular valor total
        self.valor_total = self.valor_mao_obra + self.valor_pecas - self.desconto

        super().save(*args, **kwargs)


class ItemOrdemServico(models.Model):
    """
    Itens/peças utilizados em uma ordem de serviço.
    """

    ordem_servico = models.ForeignKey(
        OrdemServico,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Ordem de Serviço'
    )
    descricao = models.CharField(
        max_length=200,
        verbose_name='Descrição'
    )
    quantidade = models.IntegerField(
        default=1,
        verbose_name='Quantidade'
    )
    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor Unitário'
    )
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor Total'
    )

    # Produto do estoque (opcional)
    produto = models.ForeignKey(
        'estoque.Produto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Produto'
    )

    class Meta:
        verbose_name = 'Item da OS'
        verbose_name_plural = 'Itens da OS'

    def __str__(self):
        return f"{self.quantidade}x {self.descricao}"

    def save(self, *args, **kwargs):
        self.valor_total = self.valor_unitario * self.quantidade
        super().save(*args, **kwargs)
