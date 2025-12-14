"""
=============================================================================
LIFE RAINBOW 2.0 - Módulo de Equipamentos
Models: ModeloEquipamento, Equipamento, HistoricoManutencao
=============================================================================
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class ModeloEquipamento(models.Model):
    """
    Catálogo de modelos de equipamentos Rainbow.
    Define especificações técnicas e preços base.
    """

    CATEGORIA_ASPIRADOR = 'aspirador'
    CATEGORIA_LAVADORA = 'lavadora'
    CATEGORIA_ACESSORIO = 'acessorio'
    CATEGORIA_LIQUIDO = 'liquido'
    CATEGORIA_FILTRO = 'filtro'
    CATEGORIA_CHOICES = [
        (CATEGORIA_ASPIRADOR, 'Aspirador Rainbow'),
        (CATEGORIA_LAVADORA, 'Lavadora/Power'),
        (CATEGORIA_ACESSORIO, 'Acessório'),
        (CATEGORIA_LIQUIDO, 'Líquido/Concentrado'),
        (CATEGORIA_FILTRO, 'Filtro'),
    ]

    nome = models.CharField(
        max_length=100,
        verbose_name='Nome do Modelo'
    )
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        verbose_name='Categoria'
    )
    descricao = models.TextField(
        null=True,
        blank=True,
        verbose_name='Descrição'
    )
    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código do Modelo'
    )

    # Preços
    preco_venda = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Preço de Venda'
    )
    preco_aluguel_mensal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Preço Aluguel/Mês'
    )
    preco_custo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Preço de Custo'
    )

    # Especificações
    voltagem = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Voltagem',
        help_text='Ex: 110V, 220V, Bivolt'
    )
    potencia = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Potência (W)'
    )
    peso = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Peso (kg)'
    )

    # Manutenção
    intervalo_manutencao_meses = models.IntegerField(
        default=12,
        verbose_name='Intervalo Manutenção (meses)',
        help_text='Frequência recomendada para manutenção preventiva'
    )
    garantia_meses = models.IntegerField(
        default=12,
        verbose_name='Garantia (meses)'
    )

    # Imagem
    imagem = models.ImageField(
        upload_to='equipamentos/modelos/',
        null=True,
        blank=True,
        verbose_name='Imagem'
    )

    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Modelo de Equipamento'
        verbose_name_plural = 'Modelos de Equipamentos'
        ordering = ['categoria', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.get_categoria_display()})"


class Equipamento(models.Model):
    """
    Equipamentos individuais (com número de série).
    Cada unidade física de Rainbow.
    """

    STATUS_ESTOQUE = 'estoque'
    STATUS_VENDIDO = 'vendido'
    STATUS_ALUGADO = 'alugado'
    STATUS_MANUTENCAO = 'manutencao'
    STATUS_DEMONSTRACAO = 'demonstracao'
    STATUS_SUCATA = 'sucata'
    STATUS_CHOICES = [
        (STATUS_ESTOQUE, 'Em Estoque'),
        (STATUS_VENDIDO, 'Vendido'),
        (STATUS_ALUGADO, 'Alugado'),
        (STATUS_MANUTENCAO, 'Em Manutenção'),
        (STATUS_DEMONSTRACAO, 'Demonstração'),
        (STATUS_SUCATA, 'Sucata/Baixa'),
    ]

    modelo = models.ForeignKey(
        ModeloEquipamento,
        on_delete=models.PROTECT,
        related_name='equipamentos',
        verbose_name='Modelo'
    )
    numero_serie = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Número de Série',
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ESTOQUE,
        verbose_name='Status',
        db_index=True
    )

    # Proprietário atual
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipamentos',
        verbose_name='Cliente/Proprietário'
    )

    # Datas importantes
    data_aquisicao = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Aquisição'
    )
    data_venda = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data da Venda'
    )
    data_fim_garantia = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fim da Garantia'
    )
    data_proxima_manutencao = models.DateField(
        null=True,
        blank=True,
        verbose_name='Próxima Manutenção',
        db_index=True
    )
    data_ultima_manutencao = models.DateField(
        null=True,
        blank=True,
        verbose_name='Última Manutenção'
    )

    # Localização
    localizacao = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Localização',
        help_text='Onde o equipamento está fisicamente'
    )

    # Power (específico Rainbow)
    numero_power = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Número do Power'
    )
    possui_power = models.BooleanField(
        default=False,
        verbose_name='Possui Power'
    )

    # Observações
    observacoes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observações'
    )
    condicao = models.CharField(
        max_length=50,
        default='novo',
        verbose_name='Condição',
        help_text='novo, semi-novo, usado, recondicionado'
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
        verbose_name = 'Equipamento'
        verbose_name_plural = 'Equipamentos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['numero_serie']),
            models.Index(fields=['status']),
            models.Index(fields=['cliente']),
            models.Index(fields=['data_proxima_manutencao']),
        ]

    def __str__(self):
        return f"{self.modelo.nome} - SN: {self.numero_serie}"

    @property
    def em_garantia(self):
        """Verifica se ainda está em garantia"""
        if self.data_fim_garantia:
            return timezone.now().date() <= self.data_fim_garantia
        return False

    @property
    def manutencao_atrasada(self):
        """Verifica se a manutenção está atrasada"""
        if self.data_proxima_manutencao:
            return timezone.now().date() > self.data_proxima_manutencao
        return False

    def agendar_proxima_manutencao(self):
        """Agenda a próxima manutenção baseado no intervalo do modelo"""
        if self.modelo.intervalo_manutencao_meses:
            self.data_ultima_manutencao = timezone.now().date()
            self.data_proxima_manutencao = timezone.now().date() + timedelta(
                days=self.modelo.intervalo_manutencao_meses * 30
            )
            self.save()


class HistoricoManutencao(models.Model):
    """
    Registro de todas as manutenções realizadas em equipamentos.
    """

    TIPO_PREVENTIVA = 'preventiva'
    TIPO_CORRETIVA = 'corretiva'
    TIPO_LIMPEZA = 'limpeza'
    TIPO_REVISAO = 'revisao'
    TIPO_CHOICES = [
        (TIPO_PREVENTIVA, 'Preventiva'),
        (TIPO_CORRETIVA, 'Corretiva'),
        (TIPO_LIMPEZA, 'Limpeza'),
        (TIPO_REVISAO, 'Revisão Geral'),
    ]

    STATUS_AGENDADA = 'agendada'
    STATUS_ANDAMENTO = 'andamento'
    STATUS_CONCLUIDA = 'concluida'
    STATUS_CANCELADA = 'cancelada'
    STATUS_CHOICES = [
        (STATUS_AGENDADA, 'Agendada'),
        (STATUS_ANDAMENTO, 'Em Andamento'),
        (STATUS_CONCLUIDA, 'Concluída'),
        (STATUS_CANCELADA, 'Cancelada'),
    ]

    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.CASCADE,
        related_name='historico_manutencao',
        verbose_name='Equipamento'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de Manutenção'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_AGENDADA,
        verbose_name='Status'
    )

    # Datas
    data_agendamento = models.DateField(
        verbose_name='Data Agendada'
    )
    data_realizacao = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Realização'
    )

    # Detalhes
    descricao_problema = models.TextField(
        null=True,
        blank=True,
        verbose_name='Descrição do Problema'
    )
    servicos_realizados = models.TextField(
        null=True,
        blank=True,
        verbose_name='Serviços Realizados'
    )
    pecas_substituidas = models.TextField(
        null=True,
        blank=True,
        verbose_name='Peças Substituídas'
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
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Valor Total'
    )

    # Responsável
    tecnico = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manutencoes_realizadas',
        verbose_name='Técnico Responsável'
    )

    # Garantia
    coberto_garantia = models.BooleanField(
        default=False,
        verbose_name='Coberto pela Garantia'
    )
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
        verbose_name = 'Histórico de Manutenção'
        verbose_name_plural = 'Histórico de Manutenções'
        ordering = ['-data_agendamento']

    def __str__(self):
        return f"Manutenção {self.get_tipo_display()} - {self.equipamento.numero_serie}"

    def save(self, *args, **kwargs):
        # Calcular valor total
        self.valor_total = self.valor_mao_obra + self.valor_pecas
        super().save(*args, **kwargs)
