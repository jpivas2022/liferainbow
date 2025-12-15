"""
=============================================================================
LIFE RAINBOW 2.0 - Admin de Assistência Técnica
Configuração do Django Admin para gestão de ordens de serviço
=============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from decimal import Decimal

from .models import OrdemServico, ItemOrdemServico


class ItemOrdemServicoInline(admin.TabularInline):
    """Inline para itens da ordem de serviço."""
    model = ItemOrdemServico
    extra = 1
    fields = ['descricao', 'produto', 'quantidade', 'valor_unitario', 'valor_total']
    autocomplete_fields = ['produto']
    readonly_fields = ['valor_total']


@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    """Admin para ordens de serviço."""
    list_display = [
        'numero', 'cliente', 'equipamento_serie', 'prioridade_badge',
        'data_abertura', 'status_badge', 'valor_total_formatado'
    ]
    list_filter = ['status', 'prioridade', 'em_garantia', 'tecnico', 'data_abertura']
    search_fields = ['numero', 'cliente__nome', 'equipamento__numero_serie', 'descricao_problema']
    autocomplete_fields = ['cliente', 'equipamento', 'tecnico', 'atendente']
    readonly_fields = ['numero', 'data_abertura', 'updated_at', 'valor_total']
    date_hierarchy = 'data_abertura'

    fieldsets = (
        ('Identificação', {
            'fields': ('numero', 'cliente', 'equipamento')
        }),
        ('Problema', {
            'fields': ('descricao_problema', 'prioridade', 'em_garantia')
        }),
        ('Diagnóstico e Solução', {
            'fields': ('diagnostico', 'servicos_realizados'),
            'classes': ('collapse',)
        }),
        ('Técnico e Datas', {
            'fields': ('tecnico', 'atendente', 'data_abertura', 'data_previsao', 'data_conclusao', 'data_entrega')
        }),
        ('Valores', {
            'fields': ('valor_mao_obra', 'valor_pecas', 'desconto', 'valor_total')
        }),
        ('Pagamento', {
            'fields': ('pago', 'data_pagamento', 'forma_pagamento'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'garantia_servico_dias')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
        ('Datas do Sistema', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

    inlines = [ItemOrdemServicoInline]

    def equipamento_serie(self, obj):
        return obj.equipamento.numero_serie if obj.equipamento else "-"
    equipamento_serie.short_description = "Equipamento"

    def status_badge(self, obj):
        cores = {
            'aberta': '#3498db',
            'analise': '#9b59b6',
            'orcamento': '#e67e22',
            'aprovado': '#27ae60',
            'execucao': '#f39c12',
            'finalizada': '#2ecc71',
            'entregue': '#27ae60',
            'cancelada': '#e74c3c',
        }
        cor = cores.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def prioridade_badge(self, obj):
        cores = {
            'baixa': '#27ae60',
            'normal': '#3498db',
            'alta': '#e67e22',
            'urgente': '#e74c3c',
        }
        cor = cores.get(obj.prioridade, '#95a5a6')
        icone = '⚠️' if obj.prioridade == 'urgente' else ''
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{} {}</span>',
            cor, icone, obj.get_prioridade_display()
        )
    prioridade_badge.short_description = "Prioridade"

    def valor_total_formatado(self, obj):
        return f"R$ {obj.valor_total:,.2f}"
    valor_total_formatado.short_description = "Valor Total"

    actions = ['marcar_concluida', 'marcar_entregue']

    @admin.action(description="Marcar como concluída")
    def marcar_concluida(self, request, queryset):
        from django.utils import timezone
        queryset.filter(status__in=['aberta', 'analise', 'execucao', 'aprovado']).update(
            status='finalizada',
            data_conclusao=timezone.now()
        )

    @admin.action(description="Marcar como entregue")
    def marcar_entregue(self, request, queryset):
        from django.utils import timezone
        queryset.filter(status='finalizada').update(
            status='entregue',
            data_entrega=timezone.now()
        )


@admin.register(ItemOrdemServico)
class ItemOrdemServicoAdmin(admin.ModelAdmin):
    """Admin para itens de ordem de serviço (acesso direto)."""
    list_display = ['ordem_servico', 'descricao_resumida', 'quantidade', 'valor_formatado']
    list_filter = ['ordem_servico__status']
    search_fields = ['ordem_servico__numero', 'descricao']

    def descricao_resumida(self, obj):
        if len(obj.descricao) > 40:
            return f"{obj.descricao[:40]}..."
        return obj.descricao
    descricao_resumida.short_description = "Descrição"

    def valor_formatado(self, obj):
        return f"R$ {obj.valor_total:,.2f}"
    valor_formatado.short_description = "Valor Total"


# Importar admin de tarefas técnicas
from .admin_tarefas import *  # noqa
