"""
=============================================================================
LIFE RAINBOW 2.0 - Admin de Tarefas Técnicas
Painel de gestão de tarefas dos assistentes técnicos
=============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import date, timedelta

from .models_tarefas import TipoTarefaTecnica, TarefaTecnica, RegistroTempoTarefa


@admin.register(TipoTarefaTecnica)
class TipoTarefaTecnicaAdmin(admin.ModelAdmin):
    """Admin para tipos de tarefas técnicas."""
    list_display = [
        'icone_nome', 'codigo', 'categoria_badge', 'tempo_estimado_minutos',
        'requer_equipamento', 'requer_os', 'pode_ser_recorrente', 'ativo'
    ]
    list_filter = ['categoria', 'ativo', 'requer_equipamento', 'requer_os']
    search_fields = ['nome', 'codigo', 'descricao']
    list_editable = ['ativo', 'tempo_estimado_minutos']
    ordering = ['ordem', 'nome']

    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'nome', 'categoria', 'descricao')
        }),
        ('Configuração', {
            'fields': ('tempo_estimado_minutos', 'requer_equipamento', 'requer_os', 'pode_ser_recorrente')
        }),
        ('Visual', {
            'fields': ('icone', 'cor', 'ordem', 'ativo')
        }),
    )

    def icone_nome(self, obj):
        return format_html(
            '<span style="font-size: 16px;">{}</span> {}',
            obj.icone, obj.nome
        )
    icone_nome.short_description = 'Tipo'

    def categoria_badge(self, obj):
        cores = {
            'orcamento': '#9b59b6',
            'conserto': '#e74c3c',
            'limpeza': '#3498db',
            'montagem': '#f39c12',
            'organizacao': '#27ae60',
            'outros': '#95a5a6',
        }
        cor = cores.get(obj.categoria, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_categoria_display()
        )
    categoria_badge.short_description = 'Categoria'


class RegistroTempoInline(admin.TabularInline):
    """Inline para registros de tempo."""
    model = RegistroTempoTarefa
    extra = 0
    fields = ['inicio', 'fim', 'duracao_minutos', 'tecnico', 'observacao']
    readonly_fields = ['duracao_minutos']


@admin.register(TarefaTecnica)
class TarefaTecnicaAdmin(admin.ModelAdmin):
    """Admin para tarefas técnicas."""
    list_display = [
        'tipo_titulo', 'tecnico', 'data_agendada', 'prioridade_badge',
        'status_badge', 'tempo_display', 'cliente_os'
    ]
    list_filter = [
        'status', 'prioridade', 'tecnico', 'tipo__categoria',
        'data_agendada', 'recorrente'
    ]
    search_fields = [
        'titulo', 'cliente__nome', 'equipamento__numero_serie',
        'ordem_servico__numero'
    ]
    autocomplete_fields = ['tecnico', 'ordem_servico', 'equipamento', 'cliente', 'criado_por']
    readonly_fields = [
        'tempo_gasto_minutos', 'data_inicio', 'data_conclusao',
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'data_agendada'
    inlines = [RegistroTempoInline]

    fieldsets = (
        ('Tarefa', {
            'fields': ('tipo', 'titulo', 'observacoes', 'tecnico')
        }),
        ('Vínculos', {
            'fields': ('ordem_servico', 'equipamento', 'cliente'),
            'classes': ('collapse',)
        }),
        ('Agendamento', {
            'fields': ('data_agendada', 'prioridade', 'posicao_fila', 'tempo_estimado_minutos')
        }),
        ('Status', {
            'fields': ('status', 'motivo_aguardando')
        }),
        ('Execução', {
            'fields': ('data_inicio', 'data_conclusao', 'tempo_gasto_minutos', 'resultado'),
            'classes': ('collapse',)
        }),
        ('Recorrência', {
            'fields': ('recorrente', 'frequencia_recorrencia', 'dias_semana'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('criado_por', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def tipo_titulo(self, obj):
        return format_html(
            '<span style="font-size: 14px;">{}</span> <strong>{}</strong>',
            obj.tipo.icone, obj.titulo[:50]
        )
    tipo_titulo.short_description = 'Tarefa'

    def prioridade_badge(self, obj):
        cores = {
            1: ('#27ae60', '🟢'),
            2: ('#f39c12', '🟡'),
            3: ('#e67e22', '🟠'),
            4: ('#e74c3c', '🔴'),
        }
        cor, emoji = cores.get(obj.prioridade, ('#95a5a6', '⚪'))
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{} {}</span>',
            cor, emoji, obj.get_prioridade_display().split(' ')[1]
        )
    prioridade_badge.short_description = 'Prioridade'

    def status_badge(self, obj):
        cores = {
            'pendente': '#95a5a6',
            'fila': '#3498db',
            'andamento': '#9b59b6',
            'pausada': '#f39c12',
            'aguardando': '#e67e22',
            'concluida': '#27ae60',
            'cancelada': '#e74c3c',
        }
        cor = cores.get(obj.status, '#95a5a6')
        texto = obj.get_status_display()
        if obj.status == 'aguardando' and obj.motivo_aguardando:
            texto = f"{texto}: {obj.motivo_aguardando[:20]}"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, texto
        )
    status_badge.short_description = 'Status'

    def tempo_display(self, obj):
        if obj.status == 'concluida':
            return format_html(
                '<span style="color: #27ae60;">✅ {}</span>',
                obj.tempo_formatado
            )
        elif obj.tempo_gasto_minutos > 0:
            return format_html(
                '<span style="color: #f39c12;">⏱️ {}</span>',
                obj.tempo_formatado
            )
        return f"Est: {obj.tempo_estimado_minutos}min"
    tempo_display.short_description = 'Tempo'

    def cliente_os(self, obj):
        partes = []
        if obj.cliente:
            partes.append(obj.cliente.nome[:20])
        if obj.ordem_servico:
            partes.append(f"OS-{obj.ordem_servico.numero}")
        if obj.equipamento:
            partes.append(f"#{obj.equipamento.numero_serie[:10]}")
        return ' | '.join(partes) if partes else '-'
    cliente_os.short_description = 'Cliente/OS/Equip.'

    # Ações em lote
    actions = [
        'iniciar_tarefas', 'pausar_tarefas', 'concluir_tarefas',
        'mover_para_fila', 'atribuir_para_hoje'
    ]

    @admin.action(description="▶️ Iniciar tarefas selecionadas")
    def iniciar_tarefas(self, request, queryset):
        count = 0
        for tarefa in queryset.filter(status__in=['pendente', 'fila', 'pausada']):
            tarefa.iniciar()
            count += 1
        self.message_user(request, f"{count} tarefa(s) iniciada(s).")

    @admin.action(description="⏸️ Pausar tarefas selecionadas")
    def pausar_tarefas(self, request, queryset):
        count = 0
        for tarefa in queryset.filter(status='andamento'):
            tarefa.pausar()
            count += 1
        self.message_user(request, f"{count} tarefa(s) pausada(s).")

    @admin.action(description="✅ Concluir tarefas selecionadas")
    def concluir_tarefas(self, request, queryset):
        count = 0
        for tarefa in queryset.exclude(status__in=['concluida', 'cancelada']):
            tarefa.concluir()
            count += 1
        self.message_user(request, f"{count} tarefa(s) concluída(s).")

    @admin.action(description="📋 Mover para fila de hoje")
    def mover_para_fila(self, request, queryset):
        queryset.filter(status='pendente').update(
            status='fila',
            data_agendada=date.today()
        )

    @admin.action(description="📅 Agendar para hoje")
    def atribuir_para_hoje(self, request, queryset):
        queryset.update(data_agendada=date.today())


@admin.register(RegistroTempoTarefa)
class RegistroTempoTarefaAdmin(admin.ModelAdmin):
    """Admin para registros de tempo (acesso direto)."""
    list_display = ['tarefa', 'tecnico', 'inicio', 'fim', 'duracao_formatada']
    list_filter = ['tecnico', 'inicio']
    search_fields = ['tarefa__titulo', 'observacao']
    date_hierarchy = 'inicio'

    def duracao_formatada(self, obj):
        if obj.duracao_minutos < 60:
            return f"{obj.duracao_minutos}min"
        horas = obj.duracao_minutos // 60
        minutos = obj.duracao_minutos % 60
        return f"{horas}h {minutos}min"
    duracao_formatada.short_description = 'Duração'
