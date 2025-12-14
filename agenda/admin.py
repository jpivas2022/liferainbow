"""
=============================================================================
LIFE RAINBOW 2.0 - Admin de Agenda
Configuração do Django Admin para gestão de agendamentos e tarefas
=============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import Agendamento, FollowUp, Tarefa


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    """Admin para agendamentos."""
    list_display = [
        'titulo', 'cliente', 'tipo_badge', 'data_hora',
        'duracao', 'responsavel', 'status_badge'
    ]
    list_filter = ['tipo', 'status', 'responsavel', 'data_hora']
    search_fields = ['titulo', 'cliente__nome', 'descricao']
    autocomplete_fields = ['cliente', 'responsavel', 'venda', 'contrato_aluguel', 'ordem_servico']
    readonly_fields = ['criado_em', 'atualizado_em']
    date_hierarchy = 'data_hora'

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'tipo', 'cliente', 'responsavel')
        }),
        ('Data e Hora', {
            'fields': ('data_hora', 'duracao')
        }),
        ('Local', {
            'fields': ('local', 'endereco'),
            'classes': ('collapse',)
        }),
        ('Vínculos', {
            'fields': ('venda', 'contrato_aluguel', 'ordem_servico'),
            'classes': ('collapse',)
        }),
        ('Detalhes', {
            'fields': ('descricao', 'status', 'resultado')
        }),
        ('Lembrete', {
            'fields': ('lembrete_enviado', 'enviar_lembrete_minutos'),
            'classes': ('collapse',)
        }),
        ('Datas do Sistema', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    def tipo_badge(self, obj):
        cores = {
            'visita': '#3498db',
            'demonstracao': '#9b59b6',
            'entrega': '#27ae60',
            'retirada': '#e67e22',
            'manutencao': '#f39c12',
            'reuniao': '#1abc9c',
            'outro': '#95a5a6',
        }
        cor = cores.get(obj.tipo, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_tipo_display()
        )
    tipo_badge.short_description = "Tipo"

    def status_badge(self, obj):
        cores = {
            'agendado': '#3498db',
            'confirmado': '#27ae60',
            'realizado': '#2ecc71',
            'cancelado': '#e74c3c',
            'reagendado': '#f39c12',
        }
        cor = cores.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    actions = ['marcar_realizado', 'cancelar_agendamentos']

    @admin.action(description="Marcar como realizado")
    def marcar_realizado(self, request, queryset):
        queryset.update(status='realizado')

    @admin.action(description="Cancelar agendamentos")
    def cancelar_agendamentos(self, request, queryset):
        queryset.exclude(status='realizado').update(status='cancelado')


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    """Admin para follow-ups."""
    list_display = [
        'cliente', 'tipo', 'data_prevista', 'prioridade_badge',
        'responsavel', 'concluido_badge'
    ]
    list_filter = ['tipo', 'prioridade', 'concluido', 'responsavel']
    search_fields = ['cliente__nome', 'descricao']
    autocomplete_fields = ['cliente', 'responsavel']
    readonly_fields = ['criado_em']
    date_hierarchy = 'data_prevista'

    def prioridade_badge(self, obj):
        cores = {
            'baixa': '#27ae60',
            'media': '#f39c12',
            'alta': '#e67e22',
            'urgente': '#e74c3c',
        }
        cor = cores.get(obj.prioridade, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_prioridade_display()
        )
    prioridade_badge.short_description = "Prioridade"

    def concluido_badge(self, obj):
        if obj.concluido:
            return format_html(
                '<span style="color: green;">✓ Concluído</span>'
            )
        return format_html('<span style="color: orange;">Pendente</span>')
    concluido_badge.short_description = "Status"

    actions = ['marcar_concluido']

    @admin.action(description="Marcar como concluído")
    def marcar_concluido(self, request, queryset):
        queryset.update(concluido=True, data_conclusao=timezone.now())


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    """Admin para tarefas."""
    list_display = [
        'titulo', 'responsavel', 'data_prazo', 'prioridade_badge',
        'status_badge', 'criado_por'
    ]
    list_filter = ['status', 'prioridade', 'responsavel', 'criado_por']
    search_fields = ['titulo', 'descricao']
    autocomplete_fields = ['responsavel', 'criado_por', 'cliente']
    readonly_fields = ['criado_em', 'atualizado_em']
    date_hierarchy = 'data_prazo'

    fieldsets = (
        ('Tarefa', {
            'fields': ('titulo', 'descricao', 'responsavel', 'cliente')
        }),
        ('Prazo e Prioridade', {
            'fields': ('data_prazo', 'prioridade', 'status')
        }),
        ('Resultado', {
            'fields': ('resultado',),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('criado_por', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    def prioridade_badge(self, obj):
        cores = {
            'baixa': '#27ae60',
            'media': '#f39c12',
            'alta': '#e67e22',
            'urgente': '#e74c3c',
        }
        cor = cores.get(obj.prioridade, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_prioridade_display()
        )
    prioridade_badge.short_description = "Prioridade"

    def status_badge(self, obj):
        cores = {
            'pendente': '#f39c12',
            'em_andamento': '#3498db',
            'concluida': '#27ae60',
            'cancelada': '#e74c3c',
        }
        cor = cores.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    actions = ['marcar_concluida', 'iniciar_tarefa']

    @admin.action(description="Marcar como concluída")
    def marcar_concluida(self, request, queryset):
        queryset.update(status='concluida')

    @admin.action(description="Iniciar tarefa")
    def iniciar_tarefa(self, request, queryset):
        queryset.filter(status='pendente').update(status='em_andamento')
