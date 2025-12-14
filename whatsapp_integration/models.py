"""
=============================================================================
LIFE RAINBOW 2.0 - Integração WhatsApp Business API
Models: Conversa, Mensagem, Template, CampanhaMensagem
=============================================================================
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Conversa(models.Model):
    """
    Representa uma conversa/thread com um cliente no WhatsApp.
    """

    STATUS_ATIVA = 'ativa'
    STATUS_AGUARDANDO = 'aguardando'
    STATUS_ENCERRADA = 'encerrada'
    STATUS_CHOICES = [
        (STATUS_ATIVA, 'Ativa'),
        (STATUS_AGUARDANDO, 'Aguardando Resposta'),
        (STATUS_ENCERRADA, 'Encerrada'),
    ]

    MODO_IA = 'ia'
    MODO_HUMANO = 'humano'
    MODO_HIBRIDO = 'hibrido'
    MODO_CHOICES = [
        (MODO_IA, 'Atendimento IA'),
        (MODO_HUMANO, 'Atendimento Humano'),
        (MODO_HIBRIDO, 'Híbrido'),
    ]

    # Cliente
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversas_whatsapp',
        verbose_name='Cliente'
    )
    telefone = models.CharField(
        max_length=20,
        verbose_name='Telefone',
        db_index=True
    )
    nome_contato = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name='Nome do Contato'
    )

    # WhatsApp IDs
    wa_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='WhatsApp ID',
        db_index=True
    )

    # Status e Modo
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ATIVA,
        verbose_name='Status'
    )
    modo_atendimento = models.CharField(
        max_length=10,
        choices=MODO_CHOICES,
        default=MODO_IA,
        verbose_name='Modo de Atendimento'
    )

    # Atendente humano (se modo humano/híbrido)
    atendente = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversas_atendidas',
        verbose_name='Atendente'
    )

    # Janela de 24h
    ultima_mensagem_cliente = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última Msg do Cliente',
        help_text='Para controle da janela de 24h'
    )
    janela_ativa = models.BooleanField(
        default=False,
        verbose_name='Janela 24h Ativa'
    )

    # Contexto para IA
    contexto_ia = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Contexto IA',
        help_text='Histórico/contexto para a IA'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conversa WhatsApp'
        verbose_name_plural = 'Conversas WhatsApp'
        ordering = ['-updated_at']

    def __str__(self):
        nome = self.nome_contato or self.telefone
        return f"Conversa com {nome}"

    def atualizar_janela(self):
        """Atualiza status da janela de 24h"""
        if self.ultima_mensagem_cliente:
            delta = timezone.now() - self.ultima_mensagem_cliente
            self.janela_ativa = delta.total_seconds() < 86400  # 24h em segundos
        else:
            self.janela_ativa = False
        self.save()


class Mensagem(models.Model):
    """
    Mensagens individuais em uma conversa.
    """

    TIPO_TEXTO = 'text'
    TIPO_IMAGEM = 'image'
    TIPO_AUDIO = 'audio'
    TIPO_VIDEO = 'video'
    TIPO_DOCUMENTO = 'document'
    TIPO_LOCALIZACAO = 'location'
    TIPO_CONTATO = 'contacts'
    TIPO_TEMPLATE = 'template'
    TIPO_INTERATIVO = 'interactive'
    TIPO_CHOICES = [
        (TIPO_TEXTO, 'Texto'),
        (TIPO_IMAGEM, 'Imagem'),
        (TIPO_AUDIO, 'Áudio'),
        (TIPO_VIDEO, 'Vídeo'),
        (TIPO_DOCUMENTO, 'Documento'),
        (TIPO_LOCALIZACAO, 'Localização'),
        (TIPO_CONTATO, 'Contato'),
        (TIPO_TEMPLATE, 'Template'),
        (TIPO_INTERATIVO, 'Interativo'),
    ]

    DIRECAO_ENTRADA = 'entrada'
    DIRECAO_SAIDA = 'saida'
    DIRECAO_CHOICES = [
        (DIRECAO_ENTRADA, 'Recebida'),
        (DIRECAO_SAIDA, 'Enviada'),
    ]

    STATUS_ENVIANDO = 'enviando'
    STATUS_ENVIADA = 'enviada'
    STATUS_ENTREGUE = 'entregue'
    STATUS_LIDA = 'lida'
    STATUS_FALHA = 'falha'
    STATUS_CHOICES = [
        (STATUS_ENVIANDO, 'Enviando'),
        (STATUS_ENVIADA, 'Enviada'),
        (STATUS_ENTREGUE, 'Entregue'),
        (STATUS_LIDA, 'Lida'),
        (STATUS_FALHA, 'Falha'),
    ]

    conversa = models.ForeignKey(
        Conversa,
        on_delete=models.CASCADE,
        related_name='mensagens',
        verbose_name='Conversa'
    )

    # WhatsApp IDs
    wamid = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        verbose_name='WhatsApp Message ID',
        db_index=True
    )

    # Tipo e Direção
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default=TIPO_TEXTO,
        verbose_name='Tipo'
    )
    direcao = models.CharField(
        max_length=10,
        choices=DIRECAO_CHOICES,
        verbose_name='Direção'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ENVIANDO,
        verbose_name='Status'
    )

    # Conteúdo
    conteudo = models.TextField(
        verbose_name='Conteúdo',
        help_text='Texto da mensagem ou URL da mídia'
    )
    media_url = models.URLField(
        null=True,
        blank=True,
        verbose_name='URL da Mídia'
    )
    media_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Media ID WhatsApp'
    )
    mime_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='MIME Type'
    )

    # Template usado (se for mensagem de template)
    template = models.ForeignKey(
        'Template',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Template'
    )

    # Remetente
    enviado_por_ia = models.BooleanField(
        default=False,
        verbose_name='Enviado por IA'
    )
    enviado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Enviado por'
    )

    # Datas
    data_envio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Envio'
    )
    data_entrega = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Entrega'
    )
    data_leitura = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Leitura'
    )

    # Erro
    erro_mensagem = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mensagem de Erro'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_direcao_display()} - {self.conteudo[:50]}..."


class Template(models.Model):
    """
    Templates de mensagem aprovados pelo WhatsApp.
    """

    CATEGORIA_UTILITY = 'UTILITY'
    CATEGORIA_MARKETING = 'MARKETING'
    CATEGORIA_AUTHENTICATION = 'AUTHENTICATION'
    CATEGORIA_CHOICES = [
        (CATEGORIA_UTILITY, 'Utility (R$0.04)'),
        (CATEGORIA_MARKETING, 'Marketing (R$0.38)'),
        (CATEGORIA_AUTHENTICATION, 'Authentication'),
    ]

    STATUS_APROVADO = 'APPROVED'
    STATUS_PENDENTE = 'PENDING'
    STATUS_REJEITADO = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_APROVADO, 'Aprovado'),
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_REJEITADO, 'Rejeitado'),
    ]

    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome do Template'
    )
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        verbose_name='Categoria'
    )
    idioma = models.CharField(
        max_length=10,
        default='pt_BR',
        verbose_name='Idioma'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDENTE,
        verbose_name='Status'
    )

    # Conteúdo
    header_text = models.CharField(
        max_length=60,
        null=True,
        blank=True,
        verbose_name='Header (texto)'
    )
    body_text = models.TextField(
        verbose_name='Body (texto)',
        help_text='Use {{1}}, {{2}} para variáveis'
    )
    footer_text = models.CharField(
        max_length=60,
        null=True,
        blank=True,
        verbose_name='Footer (texto)'
    )

    # Botões
    botoes = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Botões',
        help_text='Lista de botões do template'
    )

    # Variáveis
    variaveis = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Variáveis',
        help_text='Lista de variáveis esperadas'
    )

    # Uso
    descricao_uso = models.TextField(
        null=True,
        blank=True,
        verbose_name='Descrição de Uso',
        help_text='Quando usar este template'
    )

    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Template de Mensagem'
        verbose_name_plural = 'Templates de Mensagem'
        ordering = ['categoria', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.get_categoria_display()})"


class CampanhaMensagem(models.Model):
    """
    Campanhas de envio em massa via WhatsApp.
    """

    STATUS_RASCUNHO = 'rascunho'
    STATUS_AGENDADA = 'agendada'
    STATUS_ENVIANDO = 'enviando'
    STATUS_CONCLUIDA = 'concluida'
    STATUS_CANCELADA = 'cancelada'
    STATUS_CHOICES = [
        (STATUS_RASCUNHO, 'Rascunho'),
        (STATUS_AGENDADA, 'Agendada'),
        (STATUS_ENVIANDO, 'Enviando'),
        (STATUS_CONCLUIDA, 'Concluída'),
        (STATUS_CANCELADA, 'Cancelada'),
    ]

    nome = models.CharField(
        max_length=100,
        verbose_name='Nome da Campanha'
    )
    descricao = models.TextField(
        null=True,
        blank=True,
        verbose_name='Descrição'
    )
    template = models.ForeignKey(
        Template,
        on_delete=models.PROTECT,
        verbose_name='Template'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_RASCUNHO,
        verbose_name='Status'
    )

    # Agendamento
    data_agendada = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data Agendada'
    )
    data_inicio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Início'
    )
    data_conclusao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Conclusão'
    )

    # Filtros de público
    filtro_perfil = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Filtro por Perfil',
        help_text='Ex: ["diamante", "ouro"]'
    )
    filtro_segmento = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Filtro por Segmento'
    )
    filtro_consultor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campanhas_whatsapp',
        verbose_name='Filtro por Consultor'
    )

    # Estatísticas
    total_destinatarios = models.IntegerField(
        default=0,
        verbose_name='Total Destinatários'
    )
    total_enviados = models.IntegerField(
        default=0,
        verbose_name='Total Enviados'
    )
    total_entregues = models.IntegerField(
        default=0,
        verbose_name='Total Entregues'
    )
    total_lidos = models.IntegerField(
        default=0,
        verbose_name='Total Lidos'
    )
    total_falhas = models.IntegerField(
        default=0,
        verbose_name='Total Falhas'
    )
    total_respostas = models.IntegerField(
        default=0,
        verbose_name='Total Respostas'
    )

    # Custo
    custo_estimado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Custo Estimado'
    )
    custo_real = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Custo Real'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='campanhas_criadas',
        verbose_name='Criado por'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Campanha de Mensagem'
        verbose_name_plural = 'Campanhas de Mensagem'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nome} ({self.get_status_display()})"

    @property
    def taxa_entrega(self):
        if self.total_enviados > 0:
            return (self.total_entregues / self.total_enviados) * 100
        return 0

    @property
    def taxa_leitura(self):
        if self.total_entregues > 0:
            return (self.total_lidos / self.total_entregues) * 100
        return 0

    @property
    def taxa_resposta(self):
        if self.total_lidos > 0:
            return (self.total_respostas / self.total_lidos) * 100
        return 0
