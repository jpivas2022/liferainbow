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
    fields = ['tipo', 'produto', 'descricao', 'quantidade', 'valor_unitario']
    autocomplete_fields = ['produto']


@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    """Admin para ordens de serviço."""
    list_display = [
        'numero', 'cliente', 'equipamento_serie', 'tipo_servico',
        'data_abertura', 'status_badge', 'urgente_badge', 'valor_total_formatado'
    ]
    list_filter = ['status', 'tipo_servico', 'urgente', 'tecnico', 'data_abertura']
    search_fields = ['numero', 'cliente__nome', 'equipamento__numero_serie', 'defeito_relatado']
    autocomplete_fields = ['cliente', 'equipamento', 'tecnico']
    readonly_fields = ['numero', 'data_abertura', 'atualizado_em', 'valor_total']
    date_hierarchy = 'data_abertura'

    fieldsets = (
        ('Identificação', {
            'fields': ('numero', 'cliente', 'equipamento', 'tipo_servico')
        }),
        ('Problema', {
            'fields': ('defeito_relatado', 'urgente')
        }),
        ('Diagnóstico e Solução', {
            'fields': ('diagnostico', 'servico_executado'),
            'classes': ('collapse',)
        }),
        ('Técnico e Datas', {
            'fields': ('tecnico', 'data_abertura', 'data_previsao', 'data_conclusao')
        }),
        ('Valores', {
            'fields': ('valor_mao_obra', 'valor_pecas', 'desconto', 'valor_total')
        }),
        ('Status', {
            'fields': ('status', 'garantia')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
        ('Datas do Sistema', {
            'fields': ('atualizado_em',),
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
            'em_andamento': '#f39c12',
            'aguardando_peca': '#9b59b6',
            'aguardando_aprovacao': '#e67e22',
            'concluida': '#27ae60',
            'entregue': '#2ecc71',
            'cancelada': '#e74c3c',
        }
        cor = cores.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def urgente_badge(self, obj):
        if obj.urgente:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 11px;">⚠️ URGENTE</span>'
            )
        return "-"
    urgente_badge.short_description = "Urgência"

    def valor_total_formatado(self, obj):
        return f"R$ {obj.valor_total:,.2f}"
    valor_total_formatado.short_description = "Valor Total"

    actions = ['marcar_concluida', 'marcar_entregue']

    @admin.action(description="Marcar como concluída")
    def marcar_concluida(self, request, queryset):
        from django.utils import timezone
        queryset.filter(status__in=['aberta', 'em_andamento']).update(
            status='concluida',
            data_conclusao=timezone.now()
        )

    @admin.action(description="Marcar como entregue")
    def marcar_entregue(self, request, queryset):
        queryset.filter(status='concluida').update(status='entregue')


@admin.register(ItemOrdemServico)
class ItemOrdemServicoAdmin(admin.ModelAdmin):
    """Admin para itens de ordem de serviço (acesso direto)."""
    list_display = ['ordem_servico', 'tipo', 'descricao_resumida', 'quantidade', 'valor_formatado']
    list_filter = ['tipo']
    search_fields = ['ordem_servico__numero', 'descricao']

    def descricao_resumida(self, obj):
        if len(obj.descricao) > 40:
            return f"{obj.descricao[:40]}..."
        return obj.descricao
    descricao_resumida.short_description = "Descrição"

    def valor_formatado(self, obj):
        return f"R$ {obj.valor_unitario * obj.quantidade:,.2f}"
    valor_formatado.short_description = "Valor Total"
