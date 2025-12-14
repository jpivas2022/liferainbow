"""
=============================================================================
LIFE RAINBOW 2.0 - Módulo de Aluguéis
Models: ContratoAluguel, ParcelaAluguel, HistoricoAluguel
NOTA: Estrutura normalizada para substituir colunas um_aluguel...aluguel_doze
=============================================================================
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class ContratoAluguel(models.Model):
    """
    Contrato de aluguel de equipamentos Rainbow.
    Substitui estrutura de campos aluguel_um a aluguel_doze.
    """

    STATUS_ATIVO = 'ativo'
    STATUS_ENCERRADO = 'encerrado'
    STATUS_SUSPENSO = 'suspenso'
    STATUS_CONVERTIDO = 'convertido'  # Convertido em venda
    STATUS_CANCELADO = 'cancelado'
    STATUS_CHOICES = [
        (STATUS_ATIVO, 'Ativo'),
        (STATUS_ENCERRADO, 'Encerrado'),
        (STATUS_SUSPENSO, 'Suspenso'),
        (STATUS_CONVERTIDO, 'Convertido em Venda'),
        (STATUS_CANCELADO, 'Cancelado'),
    ]

    TIPO_MENSAL = 'mensal'
    TIPO_SEMANAL = 'semanal'
    TIPO_DIARIO = 'diario'
    TIPO_CHOICES = [
        (TIPO_MENSAL, 'Mensal'),
        (TIPO_SEMANAL, 'Semanal'),
        (TIPO_DIARIO, 'Diário'),
    ]

    # Identificação
    numero = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Número do Contrato',
        db_index=True
    )

    # Partes
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='contratos_aluguel',
        verbose_name='Cliente/Locatário'
    )
    equipamento = models.ForeignKey(
        'equipamentos.Equipamento',
        on_delete=models.PROTECT,
        related_name='contratos_aluguel',
        verbose_name='Equipamento'
    )
    consultor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='contratos_aluguel',
        verbose_name='Consultor'
    )

    # Período
    data_inicio = models.DateField(
        verbose_name='Data de Início',
        db_index=True
    )
    data_fim_prevista = models.DateField(
        verbose_name='Data Fim Prevista',
        help_text='Data prevista para encerramento/renovação'
    )
    data_fim_real = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data Fim Real'
    )
    duracao_meses = models.IntegerField(
        default=12,
        verbose_name='Duração (meses)'
    )

    # Valores
    valor_mensal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor Mensal'
    )
    valor_caucao = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Valor Caução',
        help_text='Valor depositado como garantia'
    )
    dia_vencimento = models.IntegerField(
        default=10,
        verbose_name='Dia Vencimento',
        help_text='Dia do mês para vencimento das parcelas'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ATIVO,
        verbose_name='Status',
        db_index=True
    )
    tipo_periodicidade = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default=TIPO_MENSAL,
        verbose_name='Periodicidade'
    )

    # Conversão em venda
    venda_conversao = models.ForeignKey(
        'vendas.Venda',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contratos_convertidos',
        verbose_name='Venda (se convertido)'
    )
    valor_residual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor Residual',
        help_text='Valor para compra do equipamento'
    )

    # Entrega/Devolução
    endereco_entrega = models.ForeignKey(
        'clientes.Endereco',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Endereço de Entrega'
    )
    data_entrega = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data da Entrega'
    )
    entregue = models.BooleanField(
        default=False,
        verbose_name='Entregue'
    )
    data_devolucao = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data da Devolução'
    )
    devolvido = models.BooleanField(
        default=False,
        verbose_name='Devolvido'
    )

    # Termos
    termos_aceitos = models.BooleanField(
        default=False,
        verbose_name='Termos Aceitos'
    )
    documento_contrato = models.FileField(
        upload_to='contratos/alugueis/',
        null=True,
        blank=True,
        verbose_name='Documento do Contrato'
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
        verbose_name = 'Contrato de Aluguel'
        verbose_name_plural = 'Contratos de Aluguel'
        ordering = ['-data_inicio']

    def __str__(self):
        return f"Contrato #{self.numero} - {self.cliente.nome}"

    def save(self, *args, **kwargs):
        # Gerar número do contrato automaticamente
        if not self.numero:
            ultimo = ContratoAluguel.objects.order_by('-id').first()
            novo_id = (ultimo.id + 1) if ultimo else 1
            self.numero = f"A{timezone.now().year}{novo_id:06d}"

        # Calcular data fim prevista se não informada
        if not self.data_fim_prevista and self.data_inicio and self.duracao_meses:
            self.data_fim_prevista = self.data_inicio + relativedelta(months=self.duracao_meses)

        super().save(*args, **kwargs)

    def gerar_parcelas(self):
        """
        Gera todas as parcelas do contrato.
        Substitui os campos um_aluguel...aluguel_doze
        """
        from datetime import date

        # Limpar parcelas existentes não pagas
        self.parcelas.filter(status=ParcelaAluguel.STATUS_PENDENTE).delete()

        for i in range(self.duracao_meses):
            # Calcular data de vencimento
            data_vencimento = self.data_inicio + relativedelta(months=i)
            data_vencimento = data_vencimento.replace(day=min(self.dia_vencimento, 28))

            # Verificar se parcela já existe
            if not self.parcelas.filter(numero=i + 1).exists():
                ParcelaAluguel.objects.create(
                    contrato=self,
                    numero=i + 1,
                    valor=self.valor_mensal,
                    data_vencimento=data_vencimento,
                    mes_referencia=data_vencimento.strftime('%m/%Y')
                )

    @property
    def meses_pagos(self):
        """Retorna quantidade de meses pagos"""
        return self.parcelas.filter(status=ParcelaAluguel.STATUS_PAGA).count()

    @property
    def meses_pendentes(self):
        """Retorna quantidade de meses pendentes"""
        return self.parcelas.filter(status=ParcelaAluguel.STATUS_PENDENTE).count()

    @property
    def valor_total_pago(self):
        """Valor total já pago"""
        from django.db.models import Sum
        return self.parcelas.filter(
            status=ParcelaAluguel.STATUS_PAGA
        ).aggregate(total=Sum('valor_pago'))['total'] or 0

    @property
    def proxima_parcela_vencer(self):
        """Retorna a próxima parcela a vencer"""
        return self.parcelas.filter(
            status=ParcelaAluguel.STATUS_PENDENTE,
            data_vencimento__gte=timezone.now().date()
        ).order_by('data_vencimento').first()


class ParcelaAluguel(models.Model):
    """
    Parcelas mensais de um contrato de aluguel.
    Estrutura normalizada substituindo um_aluguel...aluguel_doze
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

    contrato = models.ForeignKey(
        ContratoAluguel,
        on_delete=models.CASCADE,
        related_name='parcelas',
        verbose_name='Contrato'
    )
    numero = models.IntegerField(
        verbose_name='Nº Parcela'
    )
    mes_referencia = models.CharField(
        max_length=7,
        verbose_name='Mês Referência',
        help_text='Formato: MM/YYYY'
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
    valor_pago = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor Pago'
    )
    forma_pagamento = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Forma de Pagamento'
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

    # Boleto/PIX
    codigo_pix = models.TextField(
        null=True,
        blank=True,
        verbose_name='Código PIX'
    )
    linha_digitavel = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Linha Digitável'
    )

    observacoes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observações'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Parcela de Aluguel'
        verbose_name_plural = 'Parcelas de Aluguel'
        ordering = ['contrato', 'numero']
        unique_together = ['contrato', 'numero']
        indexes = [
            models.Index(fields=['data_vencimento', 'status']),
        ]

    def __str__(self):
        return f"Parcela {self.numero}/{self.contrato.duracao_meses} - {self.contrato.numero}"

    @property
    def dias_atraso(self):
        """Calcula dias de atraso"""
        if self.status in [self.STATUS_PENDENTE, self.STATUS_ATRASADA]:
            if self.data_vencimento < timezone.now().date():
                return (timezone.now().date() - self.data_vencimento).days
        return 0

    def calcular_valor_com_multa(self, taxa_juros_dia=0.033, taxa_multa=2.0):
        """
        Calcula valor com juros e multa por atraso.
        Taxa padrão: 0.033% ao dia (1% ao mês) + 2% multa
        """
        if self.dias_atraso > 0:
            self.juros = self.valor * (taxa_juros_dia / 100) * self.dias_atraso
            self.multa = self.valor * (taxa_multa / 100)
            return self.valor + self.juros + self.multa
        return self.valor


class HistoricoAluguel(models.Model):
    """
    Registro de eventos do contrato de aluguel.
    """

    EVENTO_CRIACAO = 'criacao'
    EVENTO_ENTREGA = 'entrega'
    EVENTO_PAGAMENTO = 'pagamento'
    EVENTO_ATRASO = 'atraso'
    EVENTO_COBRANCA = 'cobranca'
    EVENTO_RENOVACAO = 'renovacao'
    EVENTO_SUSPENSAO = 'suspensao'
    EVENTO_REATIVACAO = 'reativacao'
    EVENTO_DEVOLUCAO = 'devolucao'
    EVENTO_CONVERSAO = 'conversao'
    EVENTO_ENCERRAMENTO = 'encerramento'
    EVENTO_CHOICES = [
        (EVENTO_CRIACAO, 'Criação do Contrato'),
        (EVENTO_ENTREGA, 'Entrega do Equipamento'),
        (EVENTO_PAGAMENTO, 'Pagamento Recebido'),
        (EVENTO_ATRASO, 'Atraso Detectado'),
        (EVENTO_COBRANCA, 'Cobrança Enviada'),
        (EVENTO_RENOVACAO, 'Renovação'),
        (EVENTO_SUSPENSAO, 'Suspensão'),
        (EVENTO_REATIVACAO, 'Reativação'),
        (EVENTO_DEVOLUCAO, 'Devolução do Equipamento'),
        (EVENTO_CONVERSAO, 'Conversão em Venda'),
        (EVENTO_ENCERRAMENTO, 'Encerramento'),
    ]

    contrato = models.ForeignKey(
        ContratoAluguel,
        on_delete=models.CASCADE,
        related_name='historico',
        verbose_name='Contrato'
    )
    evento = models.CharField(
        max_length=20,
        choices=EVENTO_CHOICES,
        verbose_name='Evento'
    )
    descricao = models.TextField(
        verbose_name='Descrição'
    )
    parcela = models.ForeignKey(
        ParcelaAluguel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Parcela Relacionada'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuário'
    )
    automatico = models.BooleanField(
        default=False,
        verbose_name='Evento Automático',
        help_text='Gerado automaticamente pelo sistema/IA'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico de Aluguel'
        verbose_name_plural = 'Históricos de Aluguel'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_evento_display()} - {self.contrato.numero}"
