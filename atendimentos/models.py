"""
=============================================================================
LIFE RAINBOW 2.0 - Sistema de Atendimentos em Campo
Modelos dinâmicos e configuráveis para serviços de consultores
=============================================================================
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class TipoServico(models.Model):
    """
    Tipos de serviço configuráveis pelo admin.
    Ex: Pós-Venda, Retorno Pós-Venda, Aluguel Plano, etc.
    """
    CATEGORIA_CHOICES = [
        ('pos_venda', 'Pós-Venda'),
        ('aluguel', 'Aluguel'),
        ('visita', 'Visita'),
        ('manutencao', 'Manutenção'),
        ('outro', 'Outro'),
    ]

    nome = models.CharField(
        max_length=100,
        help_text="Nome do tipo de serviço"
    )
    codigo = models.CharField(
        max_length=50,
        unique=True,
        help_text="Código único (ex: pos_venda, retorno_pos_venda)"
    )
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        default='outro',
        blank=True
    )
    descricao = models.TextField(
        blank=True,
        help_text="Descrição detalhada do serviço"
    )
    cor = models.CharField(
        max_length=7,
        default='#3498db',
        blank=True,
        help_text="Cor para identificação visual (hex)"
    )
    icone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Nome do ícone (Material Icons)"
    )
    ordem = models.PositiveIntegerField(
        default=0,
        help_text="Ordem de exibição"
    )
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tipo de Serviço'
        verbose_name_plural = 'Tipos de Serviço'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome


class CampoServico(models.Model):
    """
    Campos dinâmicos configuráveis por tipo de serviço.
    Permite criar formulários personalizados sem código.
    """
    TIPO_CAMPO_CHOICES = [
        ('texto', 'Texto Curto'),
        ('textarea', 'Texto Longo'),
        ('numero', 'Número'),
        ('decimal', 'Decimal/Valor'),
        ('data', 'Data'),
        ('hora', 'Hora'),
        ('datetime', 'Data e Hora'),
        ('boolean', 'Sim/Não'),
        ('select', 'Seleção Única'),
        ('multiselect', 'Seleção Múltipla'),
        ('foto', 'Foto'),
        ('assinatura', 'Assinatura'),
        ('gps', 'Localização GPS'),
    ]

    tipo_servico = models.ForeignKey(
        TipoServico,
        on_delete=models.CASCADE,
        related_name='campos'
    )
    nome = models.CharField(
        max_length=100,
        help_text="Nome do campo"
    )
    codigo = models.CharField(
        max_length=50,
        help_text="Código único do campo (ex: foto_ficha)"
    )
    tipo_campo = models.CharField(
        max_length=20,
        choices=TIPO_CAMPO_CHOICES,
        default='texto'
    )
    descricao = models.TextField(
        blank=True,
        help_text="Instruções para o consultor"
    )
    placeholder = models.CharField(
        max_length=200,
        blank=True,
        help_text="Texto de exemplo no campo"
    )
    opcoes = models.JSONField(
        default=list,
        blank=True,
        help_text="Opções para campos select/multiselect (lista JSON)"
    )
    valor_padrao = models.CharField(
        max_length=200,
        blank=True,
        help_text="Valor padrão do campo"
    )
    obrigatorio = models.BooleanField(
        default=False,
        help_text="Campo obrigatório?"
    )
    ordem = models.PositiveIntegerField(
        default=0,
        help_text="Ordem de exibição no formulário"
    )
    secao = models.CharField(
        max_length=100,
        blank=True,
        help_text="Agrupa campos em seções (ex: Fotos, Pagamento)"
    )
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Campo de Serviço'
        verbose_name_plural = 'Campos de Serviço'
        ordering = ['tipo_servico', 'ordem', 'nome']
        unique_together = ['tipo_servico', 'codigo']

    def __str__(self):
        return f"{self.tipo_servico.nome} - {self.nome}"


class Atendimento(models.Model):
    """
    Registro de atendimento em campo.
    Integra com Agendamento, Cliente, Equipamento e Financeiro.
    """
    STATUS_CHOICES = [
        ('agendado', 'Agendado'),
        ('em_andamento', 'Em Andamento'),
        ('pausado', 'Pausado'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
    ]

    # Identificação
    numero = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Número único do atendimento"
    )
    tipo_servico = models.ForeignKey(
        TipoServico,
        on_delete=models.PROTECT,
        related_name='atendimentos',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='agendado'
    )

    # Integrações com modelos existentes
    agendamento = models.ForeignKey(
        'agenda.Agendamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='atendimentos',
        help_text="Agendamento que originou este atendimento"
    )
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='atendimentos',
        null=True,
        blank=True
    )
    endereco = models.ForeignKey(
        'clientes.Endereco',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='atendimentos',
        help_text="Endereço do atendimento"
    )
    equipamento = models.ForeignKey(
        'equipamentos.Equipamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='atendimentos',
        help_text="Equipamento Rainbow envolvido"
    )
    contrato_aluguel = models.ForeignKey(
        'alugueis.ContratoAluguel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='atendimentos',
        help_text="Contrato de aluguel relacionado"
    )
    venda = models.ForeignKey(
        'vendas.Venda',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='atendimentos',
        help_text="Venda relacionada (pós-venda)"
    )

    # Consultor/Responsável
    consultor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='atendimentos',
        null=True,
        blank=True
    )

    # Datas e Horários
    data_agendada = models.DateField(
        null=True,
        blank=True
    )
    hora_agendada = models.TimeField(
        null=True,
        blank=True
    )
    data_inicio = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Quando o atendimento foi iniciado"
    )
    data_fim = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Quando o atendimento foi finalizado"
    )

    # Check-in GPS
    checkin_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )
    checkin_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )
    checkin_endereco = models.CharField(
        max_length=500,
        blank=True,
        help_text="Endereço obtido via GPS"
    )
    checkin_timestamp = models.DateTimeField(
        null=True,
        blank=True
    )

    # Checkout GPS
    checkout_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )
    checkout_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )
    checkout_timestamp = models.DateTimeField(
        null=True,
        blank=True
    )

    # Relatório Geral
    relatorio = models.TextField(
        blank=True,
        help_text="Relatório geral do atendimento"
    )
    observacoes_internas = models.TextField(
        blank=True,
        help_text="Observações internas (não visíveis ao cliente)"
    )

    # Satisfação
    satisfacao_nota = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Nota de satisfação (1-5)"
    )
    satisfacao_comentario = models.TextField(
        blank=True,
        help_text="Comentário do cliente sobre satisfação"
    )

    # Financeiro (referências)
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Valor total do atendimento"
    )
    conta_receber = models.ForeignKey(
        'financeiro.ContaReceber',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='atendimentos',
        help_text="Conta a receber gerada"
    )

    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Atendimento'
        verbose_name_plural = 'Atendimentos'
        ordering = ['-data_agendada', '-hora_agendada']

    def __str__(self):
        cliente_nome = self.cliente.nome if self.cliente else 'Sem cliente'
        tipo = self.tipo_servico.nome if self.tipo_servico else 'Sem tipo'
        return f"{self.numero or 'Novo'} - {cliente_nome} ({tipo})"

    def save(self, *args, **kwargs):
        # Gerar número automático se não existir
        if not self.numero:
            ano = timezone.now().year
            ultimo = Atendimento.objects.filter(
                numero__startswith=f'ATD{ano}'
            ).order_by('-numero').first()
            if ultimo and ultimo.numero:
                try:
                    seq = int(ultimo.numero[-5:]) + 1
                except ValueError:
                    seq = 1
            else:
                seq = 1
            self.numero = f'ATD{ano}{seq:05d}'
        super().save(*args, **kwargs)

    def iniciar(self, latitude=None, longitude=None, endereco=''):
        """Inicia o atendimento com check-in GPS."""
        self.status = 'em_andamento'
        self.data_inicio = timezone.now()
        self.checkin_latitude = latitude
        self.checkin_longitude = longitude
        self.checkin_endereco = endereco
        self.checkin_timestamp = timezone.now()
        self.save()

    def finalizar(self, latitude=None, longitude=None):
        """Finaliza o atendimento com checkout GPS."""
        self.status = 'finalizado'
        self.data_fim = timezone.now()
        self.checkout_latitude = latitude
        self.checkout_longitude = longitude
        self.checkout_timestamp = timezone.now()
        self.save()

    @property
    def duracao(self):
        """Retorna a duração do atendimento em minutos."""
        if self.data_inicio and self.data_fim:
            delta = self.data_fim - self.data_inicio
            return int(delta.total_seconds() / 60)
        return None


class RespostaAtendimento(models.Model):
    """
    Armazena as respostas dos campos dinâmicos de cada atendimento.
    """
    atendimento = models.ForeignKey(
        Atendimento,
        on_delete=models.CASCADE,
        related_name='respostas'
    )
    campo = models.ForeignKey(
        CampoServico,
        on_delete=models.CASCADE,
        related_name='respostas'
    )
    valor_texto = models.TextField(
        blank=True,
        help_text="Valor para campos texto"
    )
    valor_numero = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Valor para campos numéricos"
    )
    valor_boolean = models.BooleanField(
        null=True,
        blank=True,
        help_text="Valor para campos sim/não"
    )
    valor_data = models.DateField(
        null=True,
        blank=True,
        help_text="Valor para campos data"
    )
    valor_hora = models.TimeField(
        null=True,
        blank=True,
        help_text="Valor para campos hora"
    )
    valor_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Valor para campos data/hora"
    )
    valor_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Valor para campos complexos (select múltiplo, GPS, etc)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Resposta de Atendimento'
        verbose_name_plural = 'Respostas de Atendimento'
        unique_together = ['atendimento', 'campo']

    def __str__(self):
        return f"{self.atendimento.numero} - {self.campo.nome}"

    @property
    def valor(self):
        """Retorna o valor apropriado baseado no tipo do campo."""
        tipo = self.campo.tipo_campo
        if tipo in ['texto', 'textarea']:
            return self.valor_texto
        elif tipo == 'numero':
            return int(self.valor_numero) if self.valor_numero else None
        elif tipo == 'decimal':
            return self.valor_numero
        elif tipo == 'boolean':
            return self.valor_boolean
        elif tipo == 'data':
            return self.valor_data
        elif tipo == 'hora':
            return self.valor_hora
        elif tipo == 'datetime':
            return self.valor_datetime
        else:
            return self.valor_json


class FotoAtendimento(models.Model):
    """
    Fotos tiradas durante o atendimento.
    Separado para permitir múltiplas fotos por atendimento.
    """
    TIPO_FOTO_CHOICES = [
        ('ficha', 'Ficha/Formulário'),
        ('equipamento', 'Equipamento'),
        ('contrato', 'Contrato'),
        ('ambiente', 'Ambiente'),
        ('problema', 'Problema Identificado'),
        ('antes', 'Antes do Serviço'),
        ('depois', 'Depois do Serviço'),
        ('assinatura', 'Assinatura Cliente'),
        ('outro', 'Outro'),
    ]

    atendimento = models.ForeignKey(
        Atendimento,
        on_delete=models.CASCADE,
        related_name='fotos'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_FOTO_CHOICES,
        default='outro'
    )
    campo = models.ForeignKey(
        CampoServico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fotos',
        help_text="Campo do formulário que solicitou esta foto"
    )
    foto = models.ImageField(
        upload_to='atendimentos/fotos/%Y/%m/'
    )
    descricao = models.CharField(
        max_length=200,
        blank=True,
        help_text="Descrição da foto"
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="Momento em que a foto foi tirada"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Foto de Atendimento'
        verbose_name_plural = 'Fotos de Atendimento'
        ordering = ['atendimento', 'tipo', 'timestamp']

    def __str__(self):
        return f"{self.atendimento.numero} - {self.get_tipo_display()}"
