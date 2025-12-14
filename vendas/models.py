"""
=============================================================================
LIFE RAINBOW 2.0 - Módulo de Vendas
Models: Venda, ItemVenda, Parcela
=============================================================================
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class Venda(models.Model):
    """
    Registro de vendas de equipamentos e acessórios Rainbow.
    """

    STATUS_PENDENTE = 'pendente'
    STATUS_PARCIAL = 'parcial'
    STATUS_CONCLUIDA = 'concluida'
    STATUS_CANCELADA = 'cancelada'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_PARCIAL, 'Parcialmente Paga'),
        (STATUS_CONCLUIDA, 'Concluída'),
        (STATUS_CANCELADA, 'Cancelada'),
    ]

    PAGAMENTO_DINHEIRO = 'dinheiro'
    PAGAMENTO_PIX = 'pix'
    PAGAMENTO_CARTAO_CREDITO = 'credito'
    PAGAMENTO_CARTAO_DEBITO = 'debito'
    PAGAMENTO_BOLETO = 'boleto'
    PAGAMENTO_TRANSFERENCIA = 'transferencia'
    PAGAMENTO_CHEQUE = 'cheque'
    PAGAMENTO_FINANCIAMENTO = 'financiamento'
    PAGAMENTO_CHOICES = [
        (PAGAMENTO_DINHEIRO, 'Dinheiro'),
        (PAGAMENTO_PIX, 'PIX'),
        (PAGAMENTO_CARTAO_CREDITO, 'Cartão de Crédito'),
        (PAGAMENTO_CARTAO_DEBITO, 'Cartão de Débito'),
        (PAGAMENTO_BOLETO, 'Boleto'),
        (PAGAMENTO_TRANSFERENCIA, 'Transferência'),
        (PAGAMENTO_CHEQUE, 'Cheque'),
        (PAGAMENTO_FINANCIAMENTO, 'Financiamento'),
    ]

    ENTREGA_RETIRADA = 'retirada'
    ENTREGA_DOMICILIO = 'domicilio'
    ENTREGA_CORREIOS = 'correios'
    ENTREGA_TRANSPORTADORA = 'transportadora'
    ENTREGA_CHOICES = [
        (ENTREGA_RETIRADA, 'Retirada no Local'),
        (ENTREGA_DOMICILIO, 'Entrega em Domicílio'),
        (ENTREGA_CORREIOS, 'Correios'),
        (ENTREGA_TRANSPORTADORA, 'Transportadora'),
    ]

    # Identificação
    numero = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Número da Venda',
        db_index=True
    )

    # Cliente
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='vendas',
        verbose_name='Cliente'
    )

    # Vendedor
    vendedor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='vendas_realizadas',
        verbose_name='Vendedor/Consultor'
    )

    # Status e Datas
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDENTE,
        verbose_name='Status',
        db_index=True
    )
    data_venda = models.DateField(
        default=timezone.now,
        verbose_name='Data da Venda',
        db_index=True
    )
    data_entrega = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Entrega'
    )
    entregue = models.BooleanField(
        default=False,
        verbose_name='Entregue'
    )
    tipo_entrega = models.CharField(
        max_length=20,
        choices=ENTREGA_CHOICES,
        default=ENTREGA_DOMICILIO,
        verbose_name='Tipo de Entrega'
    )

    # Valores
    valor_produtos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Valor dos Produtos'
    )
    valor_custo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Valor de Custo'
    )
    desconto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Desconto'
    )
    acrescimo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Acréscimo'
    )
    valor_frete = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Valor do Frete'
    )
    valor_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Valor Total'
    )

    # Pagamento
    forma_pagamento = models.CharField(
        max_length=20,
        choices=PAGAMENTO_CHOICES,
        default=PAGAMENTO_PIX,
        verbose_name='Forma de Pagamento'
    )
    numero_parcelas = models.IntegerField(
        default=1,
        verbose_name='Número de Parcelas'
    )
    data_primeiro_vencimento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data 1º Vencimento'
    )

    # Pontos/Comissão
    pontos = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Pontos',
        help_text='Pontos para comissão do vendedor'
    )
    comissao = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Comissão'
    )

    # Notas
    nota_fiscal = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Número NF'
    )
    observacoes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observações'
    )

    # Origem
    lancamento = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Lançamento/Campanha',
        help_text='Origem da venda (ex: Demonstração, Indicação)'
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
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'
        ordering = ['-data_venda', '-created_at']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['cliente']),
            models.Index(fields=['status']),
            models.Index(fields=['data_venda']),
            models.Index(fields=['vendedor']),
        ]

    def __str__(self):
        return f"Venda #{self.numero} - {self.cliente.nome}"

    def save(self, *args, **kwargs):
        # Gerar número da venda automaticamente
        if not self.numero:
            ultimo = Venda.objects.order_by('-id').first()
            novo_id = (ultimo.id + 1) if ultimo else 1
            self.numero = f"V{timezone.now().year}{novo_id:06d}"

        # Calcular valor total
        self.valor_total = (
            self.valor_produtos
            - self.desconto
            + self.acrescimo
            + self.valor_frete
        )

        super().save(*args, **kwargs)

    @property
    def lucro(self):
        """Calcula o lucro da venda"""
        return self.valor_total - self.valor_custo

    @property
    def margem_lucro(self):
        """Calcula a margem de lucro percentual"""
        if self.valor_total > 0:
            return (self.lucro / self.valor_total) * 100
        return 0


class ItemVenda(models.Model):
    """
    Itens individuais de uma venda.
    """

    venda = models.ForeignKey(
        Venda,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Venda'
    )
    equipamento = models.ForeignKey(
        'equipamentos.Equipamento',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='itens_venda',
        verbose_name='Equipamento (c/ série)'
    )
    modelo = models.ForeignKey(
        'equipamentos.ModeloEquipamento',
        on_delete=models.PROTECT,
        related_name='itens_venda',
        verbose_name='Modelo'
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
    valor_custo_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Custo Unitário'
    )
    desconto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Desconto'
    )
    valor_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Valor Total'
    )

    observacoes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observações'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Item da Venda'
        verbose_name_plural = 'Itens da Venda'

    def __str__(self):
        return f"{self.quantidade}x {self.modelo.nome}"

    def save(self, *args, **kwargs):
        # Calcular valor total do item
        self.valor_total = (self.valor_unitario * self.quantidade) - self.desconto
        super().save(*args, **kwargs)


class Parcela(models.Model):
    """
    Parcelas de pagamento de uma venda.
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

    venda = models.ForeignKey(
        Venda,
        on_delete=models.CASCADE,
        related_name='parcelas',
        verbose_name='Venda'
    )
    numero = models.IntegerField(
        verbose_name='Nº Parcela'
    )
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor'
    )
    data_vencimento = models.DateField(
        verbose_name='Data Vencimento',
        db_index=True
    )
    data_pagamento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data Pagamento'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDENTE,
        verbose_name='Status'
    )
    forma_pagamento = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Forma de Pagamento Utilizada'
    )
    valor_pago = models.DecimalField(
        max_digits=10,
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

    observacoes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observações'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Parcela'
        verbose_name_plural = 'Parcelas'
        ordering = ['venda', 'numero']
        unique_together = ['venda', 'numero']

    def __str__(self):
        return f"Parcela {self.numero}/{self.venda.numero_parcelas} - Venda #{self.venda.numero}"

    @property
    def dias_atraso(self):
        """Calcula dias de atraso"""
        if self.status == self.STATUS_PENDENTE and self.data_vencimento < timezone.now().date():
            return (timezone.now().date() - self.data_vencimento).days
        return 0
