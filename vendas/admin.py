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
    fields = [
        'modelo', 'equipamento', 'produto',  # produto = item do estoque
        'quantidade', 'valor_unitario', 'desconto', 'valor_total'
    ]
    autocomplete_fields = ['equipamento', 'modelo', 'produto']
    readonly_fields = ['valor_total']

    class Media:
        js = ('admin/js/item_venda_estoque.js',)  # Script para validar estoque (futuro)


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
        'numero', 'cliente', 'vendedor', 'data_venda',
        'valor_total_formatado', 'status_badge', 'forma_pagamento', 'saldo_devedor'
    ]
    list_filter = ['status', 'forma_pagamento', 'vendedor', 'data_venda', 'tipo_entrega']
    search_fields = ['numero', 'cliente__nome', 'vendedor__first_name']
    readonly_fields = ['numero', 'created_at', 'updated_at', 'valor_total']
    autocomplete_fields = ['cliente', 'vendedor']
    date_hierarchy = 'data_venda'

    fieldsets = (
        ('Identificação', {
            'fields': ('numero', 'cliente', 'vendedor')
        }),
        ('Detalhes da Venda', {
            'fields': ('forma_pagamento', 'numero_parcelas', 'data_primeiro_vencimento')
        }),
        ('Valores', {
            'fields': ('valor_produtos', 'desconto', 'acrescimo', 'valor_frete', 'valor_total')
        }),
        ('Entrega', {
            'fields': ('tipo_entrega', 'data_entrega', 'entregue'),
            'classes': ('collapse',)
        }),
        ('Comissão', {
            'fields': ('pontos', 'comissao'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'data_venda', 'nota_fiscal')
        }),
        ('Observações', {
            'fields': ('observacoes', 'lancamento'),
            'classes': ('collapse',)
        }),
        ('Datas do Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [ItemVendaInline, ParcelaInline]

    def valor_total_formatado(self, obj):
        return f"R$ {obj.valor_total:,.2f}"
    valor_total_formatado.short_description = "Valor Total"

    def status_badge(self, obj):
        cores = {
            'pendente': '#f39c12',
            'parcial': '#3498db',
            'concluida': '#27ae60',
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
        total_pago = obj.parcelas.filter(status='paga').aggregate(
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

    actions = ['marcar_concluida', 'cancelar_vendas']

    @admin.action(description="Marcar vendas como concluídas")
    def marcar_concluida(self, request, queryset):
        queryset.filter(status='pendente').update(status='concluida')

    @admin.action(description="Cancelar vendas selecionadas")
    def cancelar_vendas(self, request, queryset):
        queryset.exclude(status='concluida').update(status='cancelada')


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
            'paga': '#27ae60',
            'atrasada': '#e74c3c',
            'cancelada': '#95a5a6',
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
            parcela.status = 'paga'
            parcela.data_pagamento = timezone.now().date()
            parcela.valor_pago = parcela.valor
            parcela.save()
