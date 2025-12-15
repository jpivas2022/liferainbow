"""
=============================================================================
LIFE RAINBOW 2.0 - Sistema de Tarefas para Assistência Técnica
Gestão de tarefas dos técnicos com tipos específicos e controle de tempo
=============================================================================
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class TipoTarefaTecnica(models.Model):
    """
    Tipos de tarefas que os técnicos podem realizar.
    Configurável pelo admin.
    """

    CATEGORIA_ORCAMENTO = 'orcamento'
    CATEGORIA_CONSERTO = 'conserto'
    CATEGORIA_LIMPEZA = 'limpeza'
    CATEGORIA_MONTAGEM = 'montagem'
    CATEGORIA_ORGANIZACAO = 'organizacao'
    CATEGORIA_OUTROS = 'outros'
    CATEGORIA_CHOICES = [
        (CATEGORIA_ORCAMENTO, '💰 Orçamento'),
        (CATEGORIA_CONSERTO, '🔧 Conserto'),
        (CATEGORIA_LIMPEZA, '🧼 Limpeza'),
        (CATEGORIA_MONTAGEM, '🔩 Montagem'),
        (CATEGORIA_ORGANIZACAO, '🧹 Organização'),
        (CATEGORIA_OUTROS, '📋 Outros'),
    ]

    codigo = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='Código'
    )
    nome = models.CharField(
        max_length=100,
        verbose_name='Nome'
    )
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        verbose_name='Categoria'
    )
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )

    # Tempo padrão
    tempo_estimado_minutos = models.IntegerField(
        default=30,
        verbose_name='Tempo Estimado (min)',
        help_text='Tempo médio para realizar esta tarefa'
    )

    # Configuração
    requer_equipamento = models.BooleanField(
        default=False,
        verbose_name='Requer Equipamento?',
        help_text='Tarefa precisa estar vinculada a um equipamento'
    )
    requer_os = models.BooleanField(
        default=False,
        verbose_name='Requer OS?',
        help_text='Tarefa precisa estar vinculada a uma Ordem de Serviço'
    )
    pode_ser_recorrente = models.BooleanField(
        default=False,
        verbose_name='Pode ser Recorrente?',
        help_text='Tarefa pode ser agendada para repetir automaticamente'
    )

    # Visual
    icone = models.CharField(
        max_length=10,
        default='📋',
        verbose_name='Ícone'
    )
    cor = models.CharField(
        max_length=7,
        default='#3498db',
        verbose_name='Cor (hex)',
        help_text='Ex: #3498db'
    )

    ativo = models.BooleanField(default=True)
    ordem = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Tipo de Tarefa Técnica'
        verbose_name_plural = 'Tipos de Tarefas Técnicas'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return f"{self.icone} {self.nome}"


class TarefaTecnica(models.Model):
    """
    Tarefa específica para assistentes técnicos.
    Com controle de tempo, vínculo com equipamento/OS e fila de trabalho.
    """

    STATUS_PENDENTE = 'pendente'
    STATUS_FILA = 'fila'
    STATUS_ANDAMENTO = 'andamento'
    STATUS_PAUSADA = 'pausada'
    STATUS_AGUARDANDO = 'aguardando'  # Aguardando peças, aprovação, etc
    STATUS_CONCLUIDA = 'concluida'
    STATUS_CANCELADA = 'cancelada'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_FILA, 'Na Fila'),
        (STATUS_ANDAMENTO, 'Em Andamento'),
        (STATUS_PAUSADA, 'Pausada'),
        (STATUS_AGUARDANDO, 'Aguardando'),
        (STATUS_CONCLUIDA, 'Concluída'),
        (STATUS_CANCELADA, 'Cancelada'),
    ]

    PRIORIDADE_BAIXA = 1
    PRIORIDADE_NORMAL = 2
    PRIORIDADE_ALTA = 3
    PRIORIDADE_URGENTE = 4
    PRIORIDADE_CHOICES = [
        (PRIORIDADE_BAIXA, '🟢 Baixa'),
        (PRIORIDADE_NORMAL, '🟡 Normal'),
        (PRIORIDADE_ALTA, '🟠 Alta'),
        (PRIORIDADE_URGENTE, '🔴 Urgente'),
    ]

    # Identificação
    tipo = models.ForeignKey(
        TipoTarefaTecnica,
        on_delete=models.PROTECT,
        related_name='tarefas',
        verbose_name='Tipo de Tarefa'
    )
    titulo = models.CharField(
        max_length=200,
        verbose_name='Título/Descrição'
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações'
    )

    # Responsável
    tecnico = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tarefas_tecnicas',
        verbose_name='Técnico Responsável'
    )

    # Vínculos (opcionais dependendo do tipo)
    ordem_servico = models.ForeignKey(
        'assistencia.OrdemServico',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tarefas',
        verbose_name='Ordem de Serviço'
    )
    equipamento = models.ForeignKey(
        'equipamentos.Equipamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas_tecnicas',
        verbose_name='Equipamento'
    )
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas_tecnicas',
        verbose_name='Cliente'
    )

    # Agendamento
    data_agendada = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data Agendada',
        db_index=True
    )
    prioridade = models.IntegerField(
        choices=PRIORIDADE_CHOICES,
        default=PRIORIDADE_NORMAL,
        verbose_name='Prioridade',
        db_index=True
    )
    posicao_fila = models.IntegerField(
        default=0,
        verbose_name='Posição na Fila',
        help_text='Ordem de execução na fila do dia'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDENTE,
        verbose_name='Status',
        db_index=True
    )
    motivo_aguardando = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Motivo de Aguardar',
        help_text='Ex: Aguardando peças, Aguardando aprovação cliente'
    )

    # Controle de tempo
    tempo_estimado_minutos = models.IntegerField(
        default=30,
        verbose_name='Tempo Estimado (min)'
    )
    data_inicio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Início da Execução'
    )
    data_conclusao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Conclusão'
    )
    tempo_gasto_minutos = models.IntegerField(
        default=0,
        verbose_name='Tempo Gasto (min)',
        help_text='Tempo total trabalhado na tarefa'
    )

    # Resultado
    resultado = models.TextField(
        blank=True,
        verbose_name='Resultado/Observações Finais'
    )

    # Recorrência
    recorrente = models.BooleanField(
        default=False,
        verbose_name='Tarefa Recorrente?'
    )
    frequencia_recorrencia = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('diaria', 'Diária'),
            ('semanal', 'Semanal'),
            ('quinzenal', 'Quinzenal'),
            ('mensal', 'Mensal'),
        ],
        verbose_name='Frequência'
    )
    dias_semana = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Dias da Semana',
        help_text='Ex: seg,ter,qua,qui,sex'
    )

    # Auditoria
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tarefas_tecnicas_criadas',
        verbose_name='Criado por'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tarefa Técnica'
        verbose_name_plural = 'Tarefas Técnicas'
        ordering = ['-prioridade', 'posicao_fila', 'data_agendada', 'created_at']

    def __str__(self):
        return f"{self.tipo.icone} {self.titulo}"

    def iniciar(self):
        """Inicia a execução da tarefa."""
        if self.status in [self.STATUS_PENDENTE, self.STATUS_FILA, self.STATUS_PAUSADA]:
            self.status = self.STATUS_ANDAMENTO
            if not self.data_inicio:
                self.data_inicio = timezone.now()
            self.save()

    def pausar(self, motivo=''):
        """Pausa a tarefa."""
        if self.status == self.STATUS_ANDAMENTO:
            self.status = self.STATUS_PAUSADA
            self.motivo_aguardando = motivo
            self._calcular_tempo_parcial()
            self.save()

    def aguardar(self, motivo):
        """Coloca tarefa em espera."""
        self.status = self.STATUS_AGUARDANDO
        self.motivo_aguardando = motivo
        self._calcular_tempo_parcial()
        self.save()

    def concluir(self, resultado=''):
        """Conclui a tarefa."""
        self.status = self.STATUS_CONCLUIDA
        self.data_conclusao = timezone.now()
        self.resultado = resultado
        self._calcular_tempo_total()
        self.save()

    def _calcular_tempo_parcial(self):
        """Calcula tempo gasto até agora."""
        if self.data_inicio:
            delta = timezone.now() - self.data_inicio
            self.tempo_gasto_minutos += int(delta.total_seconds() / 60)

    def _calcular_tempo_total(self):
        """Calcula tempo total ao concluir."""
        if self.data_inicio and self.data_conclusao:
            delta = self.data_conclusao - self.data_inicio
            self.tempo_gasto_minutos = int(delta.total_seconds() / 60)

    @property
    def tempo_formatado(self):
        """Retorna tempo gasto formatado (ex: 1h 30min)."""
        if self.tempo_gasto_minutos < 60:
            return f"{self.tempo_gasto_minutos}min"
        horas = self.tempo_gasto_minutos // 60
        minutos = self.tempo_gasto_minutos % 60
        return f"{horas}h {minutos}min" if minutos else f"{horas}h"


class RegistroTempoTarefa(models.Model):
    """
    Registro de tempo trabalhado em uma tarefa.
    Permite pausar e continuar várias vezes.
    """

    tarefa = models.ForeignKey(
        TarefaTecnica,
        on_delete=models.CASCADE,
        related_name='registros_tempo',
        verbose_name='Tarefa'
    )
    tecnico = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Técnico'
    )

    inicio = models.DateTimeField(
        verbose_name='Início'
    )
    fim = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fim'
    )
    duracao_minutos = models.IntegerField(
        default=0,
        verbose_name='Duração (min)'
    )

    observacao = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Observação'
    )

    class Meta:
        verbose_name = 'Registro de Tempo'
        verbose_name_plural = 'Registros de Tempo'
        ordering = ['-inicio']

    def save(self, *args, **kwargs):
        if self.inicio and self.fim:
            delta = self.fim - self.inicio
            self.duracao_minutos = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tarefa} - {self.duracao_minutos}min"
