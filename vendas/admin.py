"""
=============================================================================
LIFE RAINBOW 2.0 - Admin de Vendas
Configuração do Django Admin para gestão de vendas
=============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from decimal import Decimal

from .models import Venda, ItemVenda, Parcela


class ItemVendaInline(admin.TabularInline):
    """Inline para itens da venda."""
    model = ItemVenda
    extra = 1
    fields = ['tipo_item', 'equipamento', 'produto', 'descricao', 'quantidade', 'valor_unitario', 'desconto']
    autocomplete_fields = ['equipamento', 'produto']


class ParcelaInline(admin.TabularInline):
    """Inline para parcelas da venda."""
    model = Parcela
    extra = 0
    fields = ['numero', 'valor', 'data_vencimento', 'data_pagamento', 'valor_pago', 'forma_pagamento', 'status']
    readonly_fields = ['numero']


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    """Admin para vendas."""
    list_display = [
        'numero', 'cliente', 'consultor', 'data_venda',
        'valor_total_formatado', 'status_badge', 'tipo_venda', 'saldo_devedor'
    ]
    list_filter = ['status', 'tipo_venda', 'forma_pagamento', 'consultor', 'data_venda']
    search_fields = ['numero', 'cliente__nome', 'consultor__first_name']
    readonly_fields = ['numero', 'data_venda', 'atualizado_em', 'valor_total']
    autocomplete_fields = ['cliente', 'consultor', 'equipamento_principal']
    date_hierarchy = 'data_venda'

    fieldsets = (
        ('Identificação', {
            'fields': ('numero', 'cliente', 'consultor')
        }),
        ('Detalhes da Venda', {
            'fields': ('tipo_venda', 'equipamento_principal', 'forma_pagamento', 'parcelas_total')
        }),
        ('Valores', {
            'fields': ('valor_produtos', 'valor_servicos', 'desconto', 'valor_frete', 'valor_total')
        }),
        ('Status', {
            'fields': ('status', 'data_venda', 'atualizado_em')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
    )

    inlines = [ItemVendaInline, ParcelaInline]

    def valor_total_formatado(self, obj):
        return f"R$ {obj.valor_total:,.2f}"
    valor_total_formatado.short_description = "Valor Total"

    def status_badge(self, obj):
        cores = {
            'orcamento': '#3498db',
            'pendente': '#f39c12',
            'aprovada': '#27ae60',
            'finalizada': '#2ecc71',
            'cancelada': '#e74c3c',
        }
        cor = cores.get(obj.status, '#3498db')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def saldo_devedor(self, obj):
        total_pago = obj.parcelas.filter(status='pago').aggregate(
            total=Sum('valor_pago')
        )['total'] or Decimal('0')
        saldo = obj.valor_total - total_pago

        if saldo > 0:
            return format_html(
                '<span style="color: red;">R$ {:,.2f}</span>',
                saldo
            )
        return format_html('<span style="color: green;">Quitado</span>')
    saldo_devedor.short_description = "Saldo Devedor"

    actions = ['aprovar_vendas', 'cancelar_vendas']

    @admin.action(description="Aprovar vendas selecionadas")
    def aprovar_vendas(self, request, queryset):
        queryset.filter(status='pendente').update(status='aprovada')

    @admin.action(description="Cancelar vendas selecionadas")
    def cancelar_vendas(self, request, queryset):
        queryset.exclude(status='finalizada').update(status='cancelada')


@admin.register(Parcela)
class ParcelaAdmin(admin.ModelAdmin):
    """Admin para parcelas (acesso direto)."""
    list_display = [
        'venda', 'numero', 'valor_formatado', 'data_vencimento',
        'data_pagamento', 'status_badge'
    ]
    list_filter = ['status', 'forma_pagamento', 'data_vencimento']
    search_fields = ['venda__numero', 'venda__cliente__nome']
    date_hierarchy = 'data_vencimento'

    def valor_formatado(self, obj):
        return f"R$ {obj.valor:,.2f}"
    valor_formatado.short_description = "Valor"

    def status_badge(self, obj):
        cores = {
            'pendente': '#f39c12',
            'pago': '#27ae60',
            'atrasado': '#e74c3c',
            'cancelado': '#95a5a6',
        }
        cor = cores.get(obj.status, '#3498db')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    actions = ['marcar_como_pago']

    @admin.action(description="Marcar como pago")
    def marcar_como_pago(self, request, queryset):
        from django.utils import timezone
        for parcela in queryset.filter(status='pendente'):
            parcela.status = 'pago'
            parcela.data_pagamento = timezone.now().date()
            parcela.valor_pago = parcela.valor
            parcela.save()
