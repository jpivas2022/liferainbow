"""
=============================================================================
LIFE RAINBOW 2.0 - Admin Financeiro
Configuração do Django Admin para gestão financeira
=============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal

from .models import PlanoConta, ContaReceber, ContaPagar, Caixa, Movimentacao


@admin.register(PlanoConta)
class PlanoContaAdmin(admin.ModelAdmin):
    """Admin para plano de contas."""
    list_display = ['codigo', 'nome', 'tipo', 'pai', 'ativo']
    list_filter = ['tipo', 'ativo']
    search_fields = ['codigo', 'nome']
    ordering = ['codigo']


@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    """Admin para contas a receber."""
    list_display = [
        'descricao', 'cliente', 'valor_formatado', 'data_vencimento',
        'status_badge', 'dias_atraso'
    ]
    list_filter = ['status', 'categoria', 'data_vencimento']
    search_fields = ['descricao', 'cliente__nome']
    autocomplete_fields = ['cliente', 'categoria', 'venda', 'contrato_aluguel']
    readonly_fields = ['criado_em', 'atualizado_em']
    date_hierarchy = 'data_vencimento'

    fieldsets = (
        ('Identificação', {
            'fields': ('descricao', 'cliente', 'categoria')
        }),
        ('Valores', {
            'fields': ('valor', 'data_vencimento', 'valor_pago', 'data_pagamento')
        }),
        ('Origem', {
            'fields': ('venda', 'contrato_aluguel'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'observacao')
        }),
        ('Datas do Sistema', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    def valor_formatado(self, obj):
        return f"R$ {obj.valor:,.2f}"
    valor_formatado.short_description = "Valor"

    def status_badge(self, obj):
        cores = {
            'pendente': '#f39c12',
            'pago': '#27ae60',
            'parcial': '#3498db',
            'cancelado': '#95a5a6',
        }
        cor = cores.get(obj.status, '#3498db')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def dias_atraso(self, obj):
        if obj.status == 'pendente' and obj.data_vencimento < timezone.now().date():
            dias = (timezone.now().date() - obj.data_vencimento).days
            return format_html('<span style="color: red;">{} dias</span>', dias)
        return "-"
    dias_atraso.short_description = "Atraso"

    actions = ['baixar_contas']

    @admin.action(description="Baixar contas selecionadas")
    def baixar_contas(self, request, queryset):
        for conta in queryset.filter(status='pendente'):
            conta.status = 'pago'
            conta.data_pagamento = timezone.now().date()
            conta.valor_pago = conta.valor
            conta.save()


@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    """Admin para contas a pagar."""
    list_display = [
        'descricao', 'fornecedor', 'valor_formatado', 'data_vencimento',
        'status_badge', 'dias_atraso'
    ]
    list_filter = ['status', 'categoria', 'data_vencimento']
    search_fields = ['descricao', 'fornecedor']
    autocomplete_fields = ['categoria']
    readonly_fields = ['criado_em', 'atualizado_em']
    date_hierarchy = 'data_vencimento'

    fieldsets = (
        ('Identificação', {
            'fields': ('descricao', 'fornecedor', 'categoria')
        }),
        ('Valores', {
            'fields': ('valor', 'data_vencimento', 'valor_pago', 'data_pagamento')
        }),
        ('Status', {
            'fields': ('status', 'observacao')
        }),
        ('Datas do Sistema', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    def valor_formatado(self, obj):
        return f"R$ {obj.valor:,.2f}"
    valor_formatado.short_description = "Valor"

    def status_badge(self, obj):
        cores = {
            'pendente': '#f39c12',
            'pago': '#27ae60',
            'parcial': '#3498db',
            'cancelado': '#95a5a6',
        }
        cor = cores.get(obj.status, '#3498db')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def dias_atraso(self, obj):
        if obj.status == 'pendente' and obj.data_vencimento < timezone.now().date():
            dias = (timezone.now().date() - obj.data_vencimento).days
            return format_html('<span style="color: red;">{} dias</span>', dias)
        return "-"
    dias_atraso.short_description = "Atraso"

    actions = ['pagar_contas']

    @admin.action(description="Pagar contas selecionadas")
    def pagar_contas(self, request, queryset):
        for conta in queryset.filter(status='pendente'):
            conta.status = 'pago'
            conta.data_pagamento = timezone.now().date()
            conta.valor_pago = conta.valor
            conta.save()


@admin.register(Caixa)
class CaixaAdmin(admin.ModelAdmin):
    """Admin para caixas."""
    list_display = ['nome', 'tipo', 'saldo_formatado', 'responsavel', 'ativo']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome']

    def saldo_formatado(self, obj):
        cor = 'green' if obj.saldo >= 0 else 'red'
        return format_html(
            '<span style="color: {};">R$ {:,.2f}</span>',
            cor, obj.saldo
        )
    saldo_formatado.short_description = "Saldo"


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    """Admin para movimentações."""
    list_display = [
        'data_hora', 'caixa', 'tipo_badge', 'categoria',
        'valor_formatado', 'descricao_resumida'
    ]
    list_filter = ['tipo', 'caixa', 'categoria', 'data_hora']
    search_fields = ['descricao']
    readonly_fields = ['data_hora', 'saldo_anterior', 'saldo_posterior']
    autocomplete_fields = ['caixa', 'categoria', 'conta_receber', 'conta_pagar']
    date_hierarchy = 'data_hora'

    def tipo_badge(self, obj):
        cor = '#27ae60' if obj.tipo == 'entrada' else '#e74c3c'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_tipo_display()
        )
    tipo_badge.short_description = "Tipo"

    def valor_formatado(self, obj):
        sinal = '+' if obj.tipo == 'entrada' else '-'
        cor = 'green' if obj.tipo == 'entrada' else 'red'
        return format_html(
            '<span style="color: {};">{} R$ {:,.2f}</span>',
            cor, sinal, obj.valor
        )
    valor_formatado.short_description = "Valor"

    def descricao_resumida(self, obj):
        if len(obj.descricao) > 40:
            return f"{obj.descricao[:40]}..."
        return obj.descricao
    descricao_resumida.short_description = "Descrição"
