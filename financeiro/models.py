"""
=============================================================================
LIFE RAINBOW 2.0 - Módulo Financeiro
Models: ContaReceber, ContaPagar, Movimentacao, Caixa, PlanoConta
=============================================================================
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class PlanoConta(models.Model):
    """
    Plano de contas para categorização financeira.
    """

    TIPO_RECEITA = 'receita'
    TIPO_DESPESA = 'despesa'
    TIPO_CHOICES = [
        (TIPO_RECEITA, 'Receita'),
        (TIPO_DESPESA, 'Despesa'),
    ]

    nome = models.CharField(
        max_length=100,
        verbose_name='Nome da Conta'
    )
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código'
    )
    conta_pai = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcontas',
        verbose_name='Conta Pai'
    )
    descricao = models.TextField(
        null=True,
        blank=True,
        verbose_name='Descrição'
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Plano de Conta'
        verbose_name_plural = 'Plano de Contas'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class ContaReceber(models.Model):
    """
    Contas a receber - valores que a empresa tem a receber.
    """

    STATUS_PENDENTE = 'pendente'
    STATUS_PAGA = 'paga'
    STATUS_ATRASADA = 'atrasada'
    STATUS_CANCELADA = 'cancelada'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_PAGA, 'Paga'),
        (STATUS_ATRASADA, 'Atrasada'),
        (STATUS_CANCELADA, 'Cancelada'),
    ]

    # Identificação
    descricao = models.CharField(
        max_length=200,
        verbose_name='Descrição'
    )
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contas_receber',
        verbose_name='Cliente'
    )

    # Valores
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Valor'
    )
    valor_pago = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor Pago'
    )
    juros = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Juros'
    )
    multa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Multa'
    )
    desconto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Desconto'
    )

    # Datas
    data_emissao = models.DateField(
        default=timezone.now,
        verbose_name='Data de Emissão'
    )
    data_vencimento = models.DateField(
        verbose_name='Data de Vencimento',
        db_index=True
    )
    data_pagamento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Pagamento'
    )

    # Status e Classificação
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDENTE,
        verbose_name='Status',
        db_index=True
    )
    plano_conta = models.ForeignKey(
        PlanoConta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Plano de Conta'
    )
    forma_pagamento = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Forma de Pagamento'
    )
    documento = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Documento/Referência'
    )

    # Origem (venda ou aluguel)
    venda = models.ForeignKey(
        'vendas.Venda',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contas_receber',
        verbose_name='Venda'
    )
    contrato_aluguel = models.ForeignKey(
        'alugueis.ContratoAluguel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contas_receber',
        verbose_name='Contrato de Aluguel'
    )

    # Responsável
    consultor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contas_receber',
        verbose_name='Consultor'
    )

    # Pontuação
    pontos = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Pontos'
    )

    observacoes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observações'
    )

    # Controle
    id_legado = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID Sistema Legado'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conta a Receber'
        verbose_name_plural = 'Contas a Receber'
        ordering = ['data_vencimento']
        indexes = [
            models.Index(fields=['data_vencimento', 'status']),
            models.Index(fields=['cliente']),
        ]

    def __str__(self):
        return f"{self.descricao} - R$ {self.valor}"

    @property
    def dias_atraso(self):
        if self.status == self.STATUS_PENDENTE and self.data_vencimento < timezone.now().date():
            return (timezone.now().date() - self.data_vencimento).days
        return 0


class ContaPagar(models.Model):
    """
    Contas a pagar - despesas e obrigações da empresa.
    """

    STATUS_PENDENTE = 'pendente'
    STATUS_PAGA = 'paga'
    STATUS_ATRASADA = 'atrasada'
    STATUS_CANCELADA = 'cancelada'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_PAGA, 'Paga'),
        (STATUS_ATRASADA, 'Atrasada'),
        (STATUS_CANCELADA, 'Cancelada'),
    ]

    # Identificação
    descricao = models.CharField(
        max_length=200,
        verbose_name='Descrição'
    )
    fornecedor = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name='Fornecedor'
    )

    # Valores
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Valor'
    )
    valor_pago = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor Pago'
    )
    juros = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Juros'
    )
    multa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Multa'
    )
    desconto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Desconto'
    )

    # Datas
    data_emissao = models.DateField(
        default=timezone.now,
        verbose_name='Data de Emissão'
    )
    data_vencimento = models.DateField(
        verbose_name='Data de Vencimento',
        db_index=True
    )
    data_pagamento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Pagamento'
    )

    # Status e Classificação
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDENTE,
        verbose_name='Status',
        db_index=True
    )
    plano_conta = models.ForeignKey(
        PlanoConta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Plano de Conta'
    )
    forma_pagamento = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Forma de Pagamento'
    )
    documento = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Documento/NF'
    )

    observacoes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observações'
    )

    # Controle
    id_legado = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID Sistema Legado'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conta a Pagar'
        verbose_name_plural = 'Contas a Pagar'
        ordering = ['data_vencimento']

    def __str__(self):
        return f"{self.descricao} - R$ {self.valor}"


class Caixa(models.Model):
    """
    Controle de caixa diário.
    """

    STATUS_ABERTO = 'aberto'
    STATUS_FECHADO = 'fechado'
    STATUS_CHOICES = [
        (STATUS_ABERTO, 'Aberto'),
        (STATUS_FECHADO, 'Fechado'),
    ]

    data = models.DateField(
        verbose_name='Data',
        db_index=True
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_ABERTO,
        verbose_name='Status'
    )
    saldo_inicial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Saldo Inicial'
    )
    total_entradas = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Total Entradas'
    )
    total_saidas = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Total Saídas'
    )
    saldo_final = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Saldo Final'
    )

    usuario_abertura = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='caixas_abertos',
        verbose_name='Aberto por'
    )
    usuario_fechamento = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='caixas_fechados',
        verbose_name='Fechado por'
    )
    data_hora_abertura = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data/Hora Abertura'
    )
    data_hora_fechamento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data/Hora Fechamento'
    )

    observacoes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observações'
    )

    class Meta:
        verbose_name = 'Caixa'
        verbose_name_plural = 'Caixas'
        ordering = ['-data']

    def __str__(self):
        return f"Caixa {self.data.strftime('%d/%m/%Y')} - {self.get_status_display()}"

    def calcular_saldo(self):
        """Recalcula o saldo baseado nas movimentações"""
        from django.db.models import Sum

        entradas = self.movimentacoes.filter(
            tipo='entrada'
        ).aggregate(total=Sum('valor'))['total'] or 0

        saidas = self.movimentacoes.filter(
            tipo='saida'
        ).aggregate(total=Sum('valor'))['total'] or 0

        self.total_entradas = entradas
        self.total_saidas = saidas
        self.saldo_final = self.saldo_inicial + entradas - saidas
        self.save()


class Movimentacao(models.Model):
    """
    Movimentações financeiras (entradas e saídas).
    """

    TIPO_ENTRADA = 'entrada'
    TIPO_SAIDA = 'saida'
    TIPO_CHOICES = [
        (TIPO_ENTRADA, 'Entrada'),
        (TIPO_SAIDA, 'Saída'),
    ]

    MOVIMENTO_VENDA = 'venda'
    MOVIMENTO_ALUGUEL = 'aluguel'
    MOVIMENTO_SERVICO = 'servico'
    MOVIMENTO_DESPESA = 'despesa'
    MOVIMENTO_TRANSFERENCIA = 'transferencia'
    MOVIMENTO_AJUSTE = 'ajuste'
    MOVIMENTO_CHOICES = [
        (MOVIMENTO_VENDA, 'Venda'),
        (MOVIMENTO_ALUGUEL, 'Aluguel'),
        (MOVIMENTO_SERVICO, 'Serviço'),
        (MOVIMENTO_DESPESA, 'Despesa'),
        (MOVIMENTO_TRANSFERENCIA, 'Transferência'),
        (MOVIMENTO_AJUSTE, 'Ajuste'),
    ]

    caixa = models.ForeignKey(
        Caixa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes',
        verbose_name='Caixa'
    )
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    movimento = models.CharField(
        max_length=20,
        choices=MOVIMENTO_CHOICES,
        verbose_name='Movimento'
    )
    descricao = models.CharField(
        max_length=200,
        verbose_name='Descrição'
    )
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Valor'
    )
    data = models.DateField(
        default=timezone.now,
        verbose_name='Data',
        db_index=True
    )

    # Classificação
    plano_conta = models.ForeignKey(
        PlanoConta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Plano de Conta'
    )
    forma_pagamento = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Forma de Pagamento'
    )
    documento = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Documento'
    )

    # Referências
    conta_receber = models.ForeignKey(
        ContaReceber,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes',
        verbose_name='Conta a Receber'
    )
    conta_pagar = models.ForeignKey(
        ContaPagar,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes',
        verbose_name='Conta a Pagar'
    )
    venda = models.ForeignKey(
        'vendas.Venda',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes',
        verbose_name='Venda'
    )

    # Responsável
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuário'
    )
    consultor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_consultor',
        verbose_name='Consultor'
    )

    # Pontuação (para vendas)
    pontos = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Pontos'
    )

    observacoes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observações'
    )

    # Controle
    id_legado = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID Sistema Legado'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimentação'
        verbose_name_plural = 'Movimentações'
        ordering = ['-data', '-created_at']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.descricao} - R$ {self.valor}"
