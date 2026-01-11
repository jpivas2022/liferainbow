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

    # Segmentação do cliente (ex-Perfil)
    SEGMENTACAO_DIAMANTE = 'diamante'
    SEGMENTACAO_OURO = 'ouro'
    SEGMENTACAO_PRATA = 'prata'
    SEGMENTACAO_BRONZE = 'bronze'
    SEGMENTACAO_PRO = 'pro'
    SEGMENTACAO_LHO = 'lho'
    PERFIL_CHOICES = [
        (SEGMENTACAO_DIAMANTE, 'Diamante'),
        (SEGMENTACAO_OURO, 'Ouro'),
        (SEGMENTACAO_PRATA, 'Prata'),
        (SEGMENTACAO_BRONZE, 'Bronze'),
        (SEGMENTACAO_PRO, 'PRO'),
        (SEGMENTACAO_LHO, 'LHO'),
    ]

    # Segmento de mercado
    SEGMENTO_RESIDENCIAL = 'residencial'
    SEGMENTO_COMERCIAL = 'comercial'
    SEGMENTO_CHOICES = [
        (SEGMENTO_RESIDENCIAL, 'Residencial'),
        (SEGMENTO_COMERCIAL, 'Comercial'),
    ]

    # Poder Aquisitivo
    PODER_A = 'a'
    PODER_B_MAIS = 'b_mais'
    PODER_B = 'b'
    PODER_AQUISITIVO_CHOICES = [
        (PODER_A, 'A'),
        (PODER_B_MAIS, 'B+'),
        (PODER_B, 'B'),
    ]

    # Giro da Preventiva (período de retorno)
    GIRO_12_MESES = '12_meses'
    GIRO_15_MESES = '15_meses'
    GIRO_18_MESES = '18_meses'
    GIRO_24_MESES = '24_meses'
    GIRO_CHOICES = [
        (GIRO_12_MESES, '12 meses'),
        (GIRO_15_MESES, '15 meses'),
        (GIRO_18_MESES, '18 meses'),
        (GIRO_24_MESES, '24 meses'),
    ]

    # Produto
    PRODUTO_POS_VENDA = 'pos_venda'
    PRODUTO_PLANO_MENSAL = 'plano_mensal'
    PRODUTO_PLANO_BIMESTRAL = 'plano_bimestral'
    PRODUTO_PLANO_TRIMESTRAL = 'plano_trimestral'
    PRODUTO_AVULSO = 'avulso'
    PRODUTO_OUTRO = 'outro'
    PRODUTO_CHOICES = [
        (PRODUTO_POS_VENDA, 'Pós-venda'),
        (PRODUTO_PLANO_MENSAL, 'Plano Mensal'),
        (PRODUTO_PLANO_BIMESTRAL, 'Plano Bimestral'),
        (PRODUTO_PLANO_TRIMESTRAL, 'Plano Trimestral'),
        (PRODUTO_AVULSO, 'Avulso'),
        (PRODUTO_OUTRO, 'Outro'),
    ]

    # Líquido
    LIQUIDO_NENHUM = 'nenhum'
    LIQUIDO_KIT_ESSENCIAS = 'kit_essencias'
    LIQUIDO_AIR_FRESH = 'air_fresh'
    LIQUIDO_SHAMPOO = 'shampoo'
    LIQUIDO_KIT_AIR_FRESH = 'kit_air_fresh'
    LIQUIDO_TODOS = 'todos'
    LIQUIDO_CHOICES = [
        (LIQUIDO_NENHUM, 'Nenhum'),
        (LIQUIDO_KIT_ESSENCIAS, 'Kit Essências'),
        (LIQUIDO_AIR_FRESH, 'Air Fresh'),
        (LIQUIDO_SHAMPOO, 'Shampoo'),
        (LIQUIDO_KIT_AIR_FRESH, 'Kit / Air Fresh'),
        (LIQUIDO_TODOS, 'Todos'),
    ]

    # Periodicidade de compra de líquidos (em meses)
    PERIODICIDADE_3_MESES = 3
    PERIODICIDADE_4_MESES = 4
    PERIODICIDADE_6_MESES = 6
    PERIODICIDADE_8_MESES = 8
    PERIODICIDADE_12_MESES = 12
    PERIODICIDADE_LIQUIDO_CHOICES = [
        (PERIODICIDADE_3_MESES, '3 meses'),
        (PERIODICIDADE_4_MESES, '4 meses'),
        (PERIODICIDADE_6_MESES, '6 meses'),
        (PERIODICIDADE_8_MESES, '8 meses'),
        (PERIODICIDADE_12_MESES, '12 meses'),
    ]

    # Perfil de MKT
    PERFIL_MKT_LIMPEZA = 'limpeza'
    PERFIL_MKT_ALERGIA = 'alergia'
    PERFIL_MKT_ANIMAIS = 'animais'
    PERFIL_MKT_OUTRO = 'outro'
    PERFIL_MKT_CHOICES = [
        (PERFIL_MKT_LIMPEZA, 'Limpeza'),
        (PERFIL_MKT_ALERGIA, 'Alergia'),
        (PERFIL_MKT_ANIMAIS, 'Animais'),
        (PERFIL_MKT_OUTRO, 'Outro'),
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

    # WhatsApp é o contato principal e deve ser único no sistema
    whatsapp = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        unique=True,
        validators=[telefone_validator],
        verbose_name='WhatsApp',
        help_text='Número único para comunicação via WhatsApp Business',
        db_index=True
    )

    telefone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        validators=[telefone_validator],
        verbose_name='Telefone Principal'
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
        default=SEGMENTACAO_LHO,
        verbose_name='Segmentação'
    )
    segmento = models.CharField(
        max_length=20,
        choices=SEGMENTO_CHOICES,
        default=SEGMENTO_RESIDENCIAL,
        verbose_name='Segmento'
    )
    poder_aquisitivo = models.CharField(
        max_length=20,
        choices=PODER_AQUISITIVO_CHOICES,
        null=True,
        blank=True,
        verbose_name='Aquisitivo'
    )
    giro = models.CharField(
        max_length=20,
        choices=GIRO_CHOICES,
        null=True,
        blank=True,
        verbose_name='Giro da Preventiva'
    )
    produto = models.CharField(
        max_length=20,
        choices=PRODUTO_CHOICES,
        null=True,
        blank=True,
        verbose_name='Produto'
    )
    liquido = models.CharField(
        max_length=20,
        choices=LIQUIDO_CHOICES,
        null=True,
        blank=True,
        verbose_name='Líquido'
    )
    periodicidade_liquido = models.IntegerField(
        choices=PERIODICIDADE_LIQUIDO_CHOICES,
        null=True,
        blank=True,
        verbose_name='Periodicidade Líquido',
        help_text='Período entre compras de líquidos (em meses)'
    )
    perfil_mkt = models.CharField(
        max_length=20,
        choices=PERFIL_MKT_CHOICES,
        null=True,
        blank=True,
        verbose_name='Perfil de MKT'
    )

    # ===== DADOS RAINBOW ESPECÍFICOS =====
    # Nota: Os equipamentos do cliente são gerenciados via equipamentos.Equipamento
    # com relacionamento cliente.equipamentos (ForeignKey)
    possui_rainbow = models.BooleanField(
        default=False,
        verbose_name='Possui Rainbow',
        help_text='Campo legado - usar relacionamento equipamentos'
    )
    data_compra_rainbow = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data da Compra Rainbow',
        help_text='Campo legado - usar relacionamento equipamentos'
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

    # ===== OBSERVAÇÃO GERAL =====
    observacao_geral = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observação Geral',
        help_text='Observação geral sobre o cliente (visível para todos)'
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


class ObservacaoCliente(models.Model):
    """
    Observações dos consultores sobre clientes.
    Permite múltiplas observações com histórico completo.
    Cada observação registra data, hora e quem fez.
    """

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='observacoes_consultor',
        verbose_name='Cliente'
    )
    texto = models.TextField(
        verbose_name='Observação',
        help_text='Texto da observação do consultor'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='observacoes_clientes',
        verbose_name='Consultor'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data/Hora'
    )

    class Meta:
        verbose_name = 'Observação do Cliente'
        verbose_name_plural = 'Observações dos Clientes'
        ordering = ['-created_at']

    def __str__(self):
        data = self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else ''
        return f"Obs. {self.cliente.nome} - {data}"


class ClienteFoto(models.Model):
    """
    Fotos de documentação do cliente.
    Armazena fichas de retirada, fotos da Rainbow e contratos de aluguel.
    """

    # Tipos de foto
    TIPO_FICHA_RETIRADA = 'ficha_retirada'
    TIPO_FOTO_RAINBOW = 'foto_rainbow'
    TIPO_CONTRATO_ALUGUEL = 'contrato_aluguel'
    TIPO_CHOICES = [
        (TIPO_FICHA_RETIRADA, 'Ficha de Retirada'),
        (TIPO_FOTO_RAINBOW, 'Foto da Rainbow'),
        (TIPO_CONTRATO_ALUGUEL, 'Contrato de Aluguel'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='fotos',
        verbose_name='Cliente'
    )
    foto = models.ImageField(
        upload_to='clientes/fotos/%Y/%m/',
        verbose_name='Foto'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de Foto'
    )
    descricao = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Descrição'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Upload'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fotos_clientes_criadas',
        verbose_name='Enviado por'
    )

    class Meta:
        verbose_name = 'Foto do Cliente'
        verbose_name_plural = 'Fotos dos Clientes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cliente.nome}"
