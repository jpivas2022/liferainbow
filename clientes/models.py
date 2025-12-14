"""
=============================================================================
LIFE RAINBOW 2.0 - Módulo de Clientes
Models: Cliente, Endereco, Contato, HistoricoInteracao
=============================================================================
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone


class Cliente(models.Model):
    """
    Modelo principal de Cliente.
    Migrado do sistema legado com melhorias estruturais.
    """

    # Tipos de pessoa
    PESSOA_FISICA = 'PF'
    PESSOA_JURIDICA = 'PJ'
    TIPO_PESSOA_CHOICES = [
        (PESSOA_FISICA, 'Pessoa Física'),
        (PESSOA_JURIDICA, 'Pessoa Jurídica'),
    ]

    # Status do cliente
    STATUS_ATIVO = 'ativo'
    STATUS_INATIVO = 'inativo'
    STATUS_PROSPECTO = 'prospecto'
    STATUS_CHOICES = [
        (STATUS_ATIVO, 'Ativo'),
        (STATUS_INATIVO, 'Inativo'),
        (STATUS_PROSPECTO, 'Prospecto'),
    ]

    # Perfil/Categoria do cliente (Rainbow específico)
    PERFIL_DIAMANTE = 'diamante'
    PERFIL_OURO = 'ouro'
    PERFIL_PRATA = 'prata'
    PERFIL_BRONZE = 'bronze'
    PERFIL_STANDARD = 'standard'
    PERFIL_CHOICES = [
        (PERFIL_DIAMANTE, 'Diamante'),
        (PERFIL_OURO, 'Ouro'),
        (PERFIL_PRATA, 'Prata'),
        (PERFIL_BRONZE, 'Bronze'),
        (PERFIL_STANDARD, 'Standard'),
    ]

    # Segmento de mercado
    SEGMENTO_RESIDENCIAL = 'residencial'
    SEGMENTO_COMERCIAL = 'comercial'
    SEGMENTO_INDUSTRIAL = 'industrial'
    SEGMENTO_CHOICES = [
        (SEGMENTO_RESIDENCIAL, 'Residencial'),
        (SEGMENTO_COMERCIAL, 'Comercial'),
        (SEGMENTO_INDUSTRIAL, 'Industrial'),
    ]

    # ===== DADOS BÁSICOS =====
    nome = models.CharField(
        max_length=150,
        verbose_name='Nome Completo',
        db_index=True
    )
    tipo_pessoa = models.CharField(
        max_length=2,
        choices=TIPO_PESSOA_CHOICES,
        default=PESSOA_FISICA,
        verbose_name='Tipo de Pessoa'
    )
    cpf_cnpj = models.CharField(
        max_length=18,
        unique=True,
        null=True,
        blank=True,
        verbose_name='CPF/CNPJ',
        help_text='Formato: 000.000.000-00 ou 00.000.000/0000-00'
    )
    inscricao_estadual = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Inscrição Estadual'
    )

    # ===== CONTATO PRINCIPAL =====
    telefone_validator = RegexValidator(
        regex=r'^\+?1?\d{10,15}$',
        message='Número de telefone deve conter 10-15 dígitos.'
    )
    telefone = models.CharField(
        max_length=20,
        validators=[telefone_validator],
        verbose_name='Telefone Principal',
        db_index=True
    )
    telefone_secundario = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Telefone Secundário'
    )
    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name='E-mail'
    )
    whatsapp = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='WhatsApp',
        help_text='Número para comunicação via WhatsApp Business'
    )

    # ===== CLASSIFICAÇÃO =====
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ATIVO,
        verbose_name='Status',
        db_index=True
    )
    perfil = models.CharField(
        max_length=20,
        choices=PERFIL_CHOICES,
        default=PERFIL_STANDARD,
        verbose_name='Perfil/Categoria'
    )
    segmento = models.CharField(
        max_length=20,
        choices=SEGMENTO_CHOICES,
        default=SEGMENTO_RESIDENCIAL,
        verbose_name='Segmento'
    )

    # ===== DADOS RAINBOW ESPECÍFICOS =====
    poder_compra = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Poder de Compra Estimado'
    )
    possui_rainbow = models.BooleanField(
        default=False,
        verbose_name='Possui Rainbow'
    )
    data_compra_rainbow = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data da Compra Rainbow'
    )

    # ===== ACOMPANHAMENTO =====
    consultor_responsavel = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes',
        verbose_name='Consultor Responsável'
    )
    data_proxima_ligacao = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data Próxima Ligação',
        db_index=True
    )
    data_ultimo_contato = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Último Contato'
    )
    status_acompanhamento = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Status do Acompanhamento'
    )

    # ===== OBSERVAÇÕES =====
    observacoes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observações'
    )
    relatorio = models.TextField(
        null=True,
        blank=True,
        verbose_name='Relatório de Atendimento'
    )

    # ===== DADOS BANCÁRIOS (para reembolsos) =====
    banco = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Banco'
    )
    agencia = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name='Agência'
    )
    conta = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Conta'
    )

    # ===== MARKETING =====
    origem = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Origem do Lead',
        help_text='Como o cliente chegou até nós'
    )
    perfil_marketing = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Perfil de Marketing'
    )
    aceita_whatsapp = models.BooleanField(
        default=True,
        verbose_name='Aceita WhatsApp Marketing'
    )
    aceita_email = models.BooleanField(
        default=True,
        verbose_name='Aceita E-mail Marketing'
    )

    # ===== CONTROLE =====
    id_legado = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID Sistema Legado',
        help_text='ID do cliente no sistema PHP antigo'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes_criados',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['telefone']),
            models.Index(fields=['cpf_cnpj']),
            models.Index(fields=['status', 'perfil']),
            models.Index(fields=['consultor_responsavel', 'data_proxima_ligacao']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.nome} ({self.telefone})"

    @property
    def endereco_principal(self):
        """Retorna o endereço principal do cliente"""
        return self.enderecos.filter(principal=True).first()

    @property
    def dias_sem_contato(self):
        """Calcula dias desde o último contato"""
        if self.data_ultimo_contato:
            return (timezone.now() - self.data_ultimo_contato).days
        return None


class Endereco(models.Model):
    """
    Endereços dos clientes.
    Um cliente pode ter múltiplos endereços.
    """

    TIPO_RESIDENCIAL = 'residencial'
    TIPO_COMERCIAL = 'comercial'
    TIPO_ENTREGA = 'entrega'
    TIPO_COBRANCA = 'cobranca'
    TIPO_CHOICES = [
        (TIPO_RESIDENCIAL, 'Residencial'),
        (TIPO_COMERCIAL, 'Comercial'),
        (TIPO_ENTREGA, 'Entrega'),
        (TIPO_COBRANCA, 'Cobrança'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='enderecos',
        verbose_name='Cliente'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default=TIPO_RESIDENCIAL,
        verbose_name='Tipo de Endereço'
    )
    principal = models.BooleanField(
        default=False,
        verbose_name='Endereço Principal'
    )

    # Endereço completo
    cep = models.CharField(max_length=10, verbose_name='CEP')
    logradouro = models.CharField(max_length=200, verbose_name='Logradouro')
    numero = models.CharField(max_length=20, verbose_name='Número')
    complemento = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Complemento'
    )
    bairro = models.CharField(max_length=100, verbose_name='Bairro')
    cidade = models.CharField(max_length=100, verbose_name='Cidade', db_index=True)
    estado = models.CharField(max_length=2, verbose_name='Estado')
    pais = models.CharField(max_length=50, default='Brasil', verbose_name='País')

    # Coordenadas para mapa
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name='Latitude'
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name='Longitude'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Endereço'
        verbose_name_plural = 'Endereços'
        ordering = ['-principal', 'tipo']

    def __str__(self):
        return f"{self.logradouro}, {self.numero} - {self.cidade}/{self.estado}"

    def save(self, *args, **kwargs):
        # Garantir apenas um endereço principal por cliente
        if self.principal:
            Endereco.objects.filter(
                cliente=self.cliente,
                principal=True
            ).exclude(pk=self.pk).update(principal=False)
        super().save(*args, **kwargs)


class HistoricoInteracao(models.Model):
    """
    Histórico de todas as interações com o cliente.
    Registra ligações, visitas, WhatsApp, e-mails, etc.
    """

    TIPO_LIGACAO = 'ligacao'
    TIPO_WHATSAPP = 'whatsapp'
    TIPO_EMAIL = 'email'
    TIPO_VISITA = 'visita'
    TIPO_REUNIAO = 'reuniao'
    TIPO_DEMONSTRACAO = 'demonstracao'
    TIPO_CHOICES = [
        (TIPO_LIGACAO, 'Ligação Telefônica'),
        (TIPO_WHATSAPP, 'WhatsApp'),
        (TIPO_EMAIL, 'E-mail'),
        (TIPO_VISITA, 'Visita'),
        (TIPO_REUNIAO, 'Reunião'),
        (TIPO_DEMONSTRACAO, 'Demonstração'),
    ]

    DIRECAO_ENTRADA = 'entrada'
    DIRECAO_SAIDA = 'saida'
    DIRECAO_CHOICES = [
        (DIRECAO_ENTRADA, 'Recebida'),
        (DIRECAO_SAIDA, 'Realizada'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='historico_interacoes',
        verbose_name='Cliente'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de Interação'
    )
    direcao = models.CharField(
        max_length=10,
        choices=DIRECAO_CHOICES,
        default=DIRECAO_SAIDA,
        verbose_name='Direção'
    )

    # Detalhes
    descricao = models.TextField(verbose_name='Descrição/Resumo')
    resultado = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Resultado'
    )
    proxima_acao = models.TextField(
        null=True,
        blank=True,
        verbose_name='Próxima Ação'
    )
    data_proxima_acao = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data Próxima Ação'
    )

    # Responsável
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Responsável'
    )

    # IA
    gerado_por_ia = models.BooleanField(
        default=False,
        verbose_name='Gerado por IA'
    )
    whatsapp_message_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='ID Mensagem WhatsApp'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')

    class Meta:
        verbose_name = 'Histórico de Interação'
        verbose_name_plural = 'Histórico de Interações'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cliente.nome} ({self.created_at.strftime('%d/%m/%Y')})"
