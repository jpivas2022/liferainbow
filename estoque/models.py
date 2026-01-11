"""
=============================================================================
LIFE RAINBOW 2.0 - Módulo de Estoque
Models: Produto, MovimentacaoEstoque, Inventario
=============================================================================
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Produto(models.Model):
    """
    Produtos em estoque (peças, acessórios, consumíveis).
    """

    CATEGORIA_PECA = 'peca'
    CATEGORIA_ACESSORIO = 'acessorio'
    CATEGORIA_CONSUMIVEL = 'consumivel'
    CATEGORIA_LIQUIDO = 'liquido'
    CATEGORIA_FILTRO = 'filtro'
    CATEGORIA_CHOICES = [
        (CATEGORIA_PECA, 'Peça de Reposição'),
        (CATEGORIA_ACESSORIO, 'Acessório'),
        (CATEGORIA_CONSUMIVEL, 'Consumível'),
        (CATEGORIA_LIQUIDO, 'Líquido/Concentrado'),
        (CATEGORIA_FILTRO, 'Filtro'),
    ]

    # Identificação
    nome = models.CharField(
        max_length=150,
        verbose_name='Nome do Produto'
    )
    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código/SKU',
        db_index=True
    )
    codigo_barras = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Código de Barras'
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

    # Estoque
    estoque_atual = models.IntegerField(
        default=0,
        verbose_name='Estoque Atual'
    )
    estoque_minimo = models.IntegerField(
        default=5,
        verbose_name='Estoque Mínimo',
        help_text='Alerta quando chegar a este nível'
    )
    estoque_maximo = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Estoque Máximo'
    )
    localizacao = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Localização no Estoque'
    )

    # Valores
    preco_custo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Preço de Custo'
    )
    preco_venda = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Preço de Venda'
    )

    # Fornecedor
    fornecedor = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name='Fornecedor'
    )

    # Unidade
    unidade = models.CharField(
        max_length=10,
        default='UN',
        verbose_name='Unidade',
        help_text='Ex: UN, CX, KG, L'
    )

    # Imagem
    imagem = models.ImageField(
        upload_to='produtos/',
        null=True,
        blank=True,
        verbose_name='Imagem'
    )

    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    # Controle
    id_legado = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID Sistema Legado'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['nome']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    @property
    def estoque_baixo(self):
        """Verifica se estoque está abaixo do mínimo"""
        return self.estoque_atual <= self.estoque_minimo

    @property
    def valor_estoque(self):
        """Calcula valor total do estoque deste produto"""
        return self.estoque_atual * self.preco_custo


class MovimentacaoEstoque(models.Model):
    """
    Histórico de movimentações de estoque.
    """

    TIPO_ENTRADA = 'entrada'
    TIPO_SAIDA = 'saida'
    TIPO_AJUSTE = 'ajuste'
    TIPO_CHOICES = [
        (TIPO_ENTRADA, 'Entrada'),
        (TIPO_SAIDA, 'Saída'),
        (TIPO_AJUSTE, 'Ajuste'),
    ]

    MOTIVO_COMPRA = 'compra'
    MOTIVO_VENDA = 'venda'
    MOTIVO_DEVOLUCAO = 'devolucao'
    MOTIVO_MANUTENCAO = 'manutencao'
    MOTIVO_USO_INTERNO = 'uso_interno'
    MOTIVO_PERDA = 'perda'
    MOTIVO_INVENTARIO = 'inventario'
    MOTIVO_TRANSFERENCIA = 'transferencia'
    MOTIVO_CHOICES = [
        (MOTIVO_COMPRA, 'Compra'),
        (MOTIVO_VENDA, 'Venda'),
        (MOTIVO_DEVOLUCAO, 'Devolução'),
        (MOTIVO_MANUTENCAO, 'Manutenção/OS'),
        (MOTIVO_USO_INTERNO, 'Uso Interno'),
        (MOTIVO_PERDA, 'Perda/Avaria'),
        (MOTIVO_INVENTARIO, 'Ajuste de Inventário'),
        (MOTIVO_TRANSFERENCIA, 'Transferência'),
    ]

    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='movimentacoes',
        verbose_name='Produto'
    )
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    motivo = models.CharField(
        max_length=20,
        choices=MOTIVO_CHOICES,
        verbose_name='Motivo'
    )
    quantidade = models.IntegerField(
        verbose_name='Quantidade'
    )
    estoque_anterior = models.IntegerField(
        verbose_name='Estoque Anterior'
    )
    estoque_posterior = models.IntegerField(
        verbose_name='Estoque Posterior'
    )

    # Valor unitário no momento
    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor Unitário'
    )

    # Referências
    ordem_servico = models.ForeignKey(
        'assistencia.OrdemServico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Ordem de Serviço'
    )
    venda = models.ForeignKey(
        'vendas.Venda',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Venda'
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

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuário'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimentação de Estoque'
        verbose_name_plural = 'Movimentações de Estoque'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.produto.nome} ({self.quantidade})"

    def save(self, *args, **kwargs):
        # Registrar estoque anterior
        if not self.estoque_anterior:
            self.estoque_anterior = self.produto.estoque_atual

        # Calcular estoque posterior
        if self.tipo == self.TIPO_ENTRADA:
            self.estoque_posterior = self.estoque_anterior + self.quantidade
        elif self.tipo == self.TIPO_SAIDA:
            self.estoque_posterior = self.estoque_anterior - self.quantidade
        else:  # Ajuste
            self.estoque_posterior = self.quantidade

        super().save(*args, **kwargs)

        # Atualizar estoque do produto
        self.produto.estoque_atual = self.estoque_posterior
        self.produto.save()


class Inventario(models.Model):
    """
    Registro de inventários realizados.
    """

    STATUS_ANDAMENTO = 'andamento'
    STATUS_FINALIZADO = 'finalizado'
    STATUS_CANCELADO = 'cancelado'
    STATUS_CHOICES = [
        (STATUS_ANDAMENTO, 'Em Andamento'),
        (STATUS_FINALIZADO, 'Finalizado'),
        (STATUS_CANCELADO, 'Cancelado'),
    ]

    data = models.DateField(
        verbose_name='Data do Inventário'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ANDAMENTO,
        verbose_name='Status'
    )
    responsavel = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Responsável'
    )
    observacoes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observações'
    )

    # Totais
    total_itens = models.IntegerField(
        default=0,
        verbose_name='Total de Itens'
    )
    divergencias = models.IntegerField(
        default=0,
        verbose_name='Divergências Encontradas'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Inventário'
        verbose_name_plural = 'Inventários'
        ordering = ['-data']

    def __str__(self):
        return f"Inventário {self.data.strftime('%d/%m/%Y')}"
