"""
=============================================================================
LIFE RAINBOW 2.0 - Módulo de Agenda
Models: Agendamento, FollowUp, Tarefa
=============================================================================
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Agendamento(models.Model):
    """
    Agendamentos de visitas, demonstrações e atendimentos.
    """

    TIPO_DEMONSTRACAO = 'demonstracao'
    TIPO_VISITA = 'visita'
    TIPO_MANUTENCAO = 'manutencao'
    TIPO_ENTREGA = 'entrega'
    TIPO_RETIRADA = 'retirada'
    TIPO_REUNIAO = 'reuniao'
    TIPO_CHOICES = [
        (TIPO_DEMONSTRACAO, 'Demonstração'),
        (TIPO_VISITA, 'Visita'),
        (TIPO_MANUTENCAO, 'Manutenção'),
        (TIPO_ENTREGA, 'Entrega'),
        (TIPO_RETIRADA, 'Retirada'),
        (TIPO_REUNIAO, 'Reunião'),
    ]

    STATUS_AGENDADO = 'agendado'
    STATUS_CONFIRMADO = 'confirmado'
    STATUS_REALIZADO = 'realizado'
    STATUS_CANCELADO = 'cancelado'
    STATUS_REMARCADO = 'remarcado'
    STATUS_NAO_COMPARECEU = 'nao_compareceu'
    STATUS_CHOICES = [
        (STATUS_AGENDADO, 'Agendado'),
        (STATUS_CONFIRMADO, 'Confirmado'),
        (STATUS_REALIZADO, 'Realizado'),
        (STATUS_CANCELADO, 'Cancelado'),
        (STATUS_REMARCADO, 'Remarcado'),
        (STATUS_NAO_COMPARECEU, 'Não Compareceu'),
    ]

    # Identificação
    titulo = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )

    # Cliente
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='agendamentos',
        verbose_name='Cliente'
    )

    # Responsável
    responsavel = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='agendamentos',
        verbose_name='Responsável'
    )

    # Data e Hora
    data = models.DateField(
        verbose_name='Data',
        db_index=True
    )
    hora_inicio = models.TimeField(
        verbose_name='Hora Início'
    )
    hora_fim = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Hora Fim'
    )
    duracao_estimada = models.IntegerField(
        default=60,
        verbose_name='Duração Estimada (min)'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_AGENDADO,
        verbose_name='Status',
        db_index=True
    )

    # Local
    endereco = models.ForeignKey(
        'clientes.Endereco',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Endereço'
    )
    local_descricao = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name='Local/Descrição'
    )

    # Resultado
    resultado = models.TextField(
        null=True,
        blank=True,
        verbose_name='Resultado'
    )
    venda_realizada = models.ForeignKey(
        'vendas.Venda',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Venda Resultante'
    )

    # Notificações
    lembrete_enviado = models.BooleanField(
        default=False,
        verbose_name='Lembrete Enviado'
    )
    confirmacao_enviada = models.BooleanField(
        default=False,
        verbose_name='Confirmação Enviada'
    )

    observacoes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observações'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'
        ordering = ['data', 'hora_inicio']

    def __str__(self):
        return f"{self.titulo} - {self.data.strftime('%d/%m/%Y')} {self.hora_inicio}"


class FollowUp(models.Model):
    """
    Follow-ups e lembretes de acompanhamento.
    Para substituir campos como data_prox_ligacao do sistema legado.
    """

    TIPO_LIGACAO = 'ligacao'
    TIPO_WHATSAPP = 'whatsapp'
    TIPO_EMAIL = 'email'
    TIPO_VISITA = 'visita'
    TIPO_CHOICES = [
        (TIPO_LIGACAO, 'Ligação'),
        (TIPO_WHATSAPP, 'WhatsApp'),
        (TIPO_EMAIL, 'E-mail'),
        (TIPO_VISITA, 'Visita'),
    ]

    STATUS_PENDENTE = 'pendente'
    STATUS_REALIZADO = 'realizado'
    STATUS_CANCELADO = 'cancelado'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_REALIZADO, 'Realizado'),
        (STATUS_CANCELADO, 'Cancelado'),
    ]

    PRIORIDADE_BAIXA = 'baixa'
    PRIORIDADE_MEDIA = 'media'
    PRIORIDADE_ALTA = 'alta'
    PRIORIDADE_URGENTE = 'urgente'
    PRIORIDADE_CHOICES = [
        (PRIORIDADE_BAIXA, 'Baixa'),
        (PRIORIDADE_MEDIA, 'Média'),
        (PRIORIDADE_ALTA, 'Alta'),
        (PRIORIDADE_URGENTE, 'Urgente'),
    ]

    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='follow_ups',
        verbose_name='Cliente'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    assunto = models.CharField(
        max_length=200,
        verbose_name='Assunto'
    )
    descricao = models.TextField(
        null=True,
        blank=True,
        verbose_name='Descrição'
    )

    # Agendamento
    data_prevista = models.DateField(
        verbose_name='Data Prevista',
        db_index=True
    )
    hora_prevista = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Hora Prevista'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDENTE,
        verbose_name='Status'
    )
    prioridade = models.CharField(
        max_length=10,
        choices=PRIORIDADE_CHOICES,
        default=PRIORIDADE_MEDIA,
        verbose_name='Prioridade'
    )

    # Responsável
    responsavel = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='follow_ups',
        verbose_name='Responsável'
    )

    # Resultado
    data_realizacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data/Hora Realização'
    )
    resultado = models.TextField(
        null=True,
        blank=True,
        verbose_name='Resultado'
    )
    proximo_follow_up = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='follow_up_anterior',
        verbose_name='Próximo Follow-up'
    )

    # IA
    gerado_por_ia = models.BooleanField(
        default=False,
        verbose_name='Gerado por IA'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Follow-up'
        verbose_name_plural = 'Follow-ups'
        ordering = ['data_prevista', 'hora_prevista']

    def __str__(self):
        return f"{self.assunto} - {self.cliente.nome} ({self.data_prevista})"


class Tarefa(models.Model):
    """
    Tarefas internas da equipe.
    """

    STATUS_PENDENTE = 'pendente'
    STATUS_ANDAMENTO = 'andamento'
    STATUS_CONCLUIDA = 'concluida'
    STATUS_CANCELADA = 'cancelada'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_ANDAMENTO, 'Em Andamento'),
        (STATUS_CONCLUIDA, 'Concluída'),
        (STATUS_CANCELADA, 'Cancelada'),
    ]

    titulo = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    descricao = models.TextField(
        null=True,
        blank=True,
        verbose_name='Descrição'
    )
    responsavel = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tarefas',
        verbose_name='Responsável'
    )
    data_limite = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data Limite'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDENTE,
        verbose_name='Status'
    )
    prioridade = models.CharField(
        max_length=10,
        choices=FollowUp.PRIORIDADE_CHOICES,
        default=FollowUp.PRIORIDADE_MEDIA,
        verbose_name='Prioridade'
    )

    # Relacionamentos opcionais
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas',
        verbose_name='Cliente'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tarefas_criadas',
        verbose_name='Criado por'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'
        ordering = ['-prioridade', 'data_limite']

    def __str__(self):
        return self.titulo
