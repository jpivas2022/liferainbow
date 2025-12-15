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
    list_display = ['codigo', 'nome', 'tipo', 'conta_pai', 'ativo']
    list_filter = ['tipo', 'ativo']
    search_fields = ['codigo', 'nome']
    ordering = ['codigo']

    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'nome', 'tipo')
        }),
        ('Hierarquia', {
            'fields': ('conta_pai',)
        }),
        ('Descrição', {
            'fields': ('descricao',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )


@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    """Admin para contas a receber."""
    list_display = [
        'descricao', 'cliente', 'valor_formatado', 'data_vencimento',
        'status_badge', 'dias_atraso_display'
    ]
    list_filter = ['status', 'plano_conta', 'data_vencimento']
    search_fields = ['descricao', 'cliente__nome']
    autocomplete_fields = ['cliente', 'plano_conta', 'venda', 'contrato_aluguel', 'consultor']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'data_vencimento'

    fieldsets = (
        ('Identificação', {
            'fields': ('descricao', 'cliente', 'plano_conta')
        }),
        ('Valores', {
            'fields': ('valor', 'juros', 'multa', 'desconto')
        }),
        ('Datas', {
            'fields': ('data_emissao', 'data_vencimento', 'data_pagamento', 'valor_pago')
        }),
        ('Origem', {
            'fields': ('venda', 'contrato_aluguel'),
            'classes': ('collapse',)
        }),
        ('Responsável', {
            'fields': ('consultor', 'pontos'),
            'classes': ('collapse',)
        }),
        ('Pagamento', {
            'fields': ('forma_pagamento', 'documento')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
        ('Datas do Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

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

    def dias_atraso_display(self, obj):
        dias = obj.dias_atraso
        if dias > 0:
            return format_html('<span style="color: red;">{} dias</span>', dias)
        return "-"
    dias_atraso_display.short_description = "Atraso"

    actions = ['baixar_contas']

    @admin.action(description="Baixar contas selecionadas")
    def baixar_contas(self, request, queryset):
        for conta in queryset.filter(status='pendente'):
            conta.status = 'paga'
            conta.data_pagamento = timezone.now().date()
            conta.valor_pago = conta.valor
            conta.save()


@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    """Admin para contas a pagar."""
    list_display = [
        'descricao', 'fornecedor', 'valor_formatado', 'data_vencimento',
        'status_badge', 'dias_atraso_display'
    ]
    list_filter = ['status', 'plano_conta', 'data_vencimento']
    search_fields = ['descricao', 'fornecedor']
    autocomplete_fields = ['plano_conta']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'data_vencimento'

    fieldsets = (
        ('Identificação', {
            'fields': ('descricao', 'fornecedor', 'plano_conta')
        }),
        ('Valores', {
            'fields': ('valor', 'juros', 'multa', 'desconto')
        }),
        ('Datas', {
            'fields': ('data_emissao', 'data_vencimento', 'data_pagamento', 'valor_pago')
        }),
        ('Pagamento', {
            'fields': ('forma_pagamento', 'documento')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
        ('Datas do Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

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

    def dias_atraso_display(self, obj):
        if obj.status == 'pendente' and obj.data_vencimento < timezone.now().date():
            dias = (timezone.now().date() - obj.data_vencimento).days
            return format_html('<span style="color: red;">{} dias</span>', dias)
        return "-"
    dias_atraso_display.short_description = "Atraso"

    actions = ['pagar_contas']

    @admin.action(description="Pagar contas selecionadas")
    def pagar_contas(self, request, queryset):
        for conta in queryset.filter(status='pendente'):
            conta.status = 'paga'
            conta.data_pagamento = timezone.now().date()
            conta.valor_pago = conta.valor
            conta.save()


@admin.register(Caixa)
class CaixaAdmin(admin.ModelAdmin):
    """Admin para caixas."""
    list_display = ['data', 'status_badge', 'saldo_formatado', 'usuario_abertura', 'total_entradas_fmt', 'total_saidas_fmt']
    list_filter = ['status', 'data']
    search_fields = ['observacoes']
    autocomplete_fields = ['usuario_abertura', 'usuario_fechamento']
    date_hierarchy = 'data'

    fieldsets = (
        ('Caixa', {
            'fields': ('data', 'status')
        }),
        ('Saldos', {
            'fields': ('saldo_inicial', 'total_entradas', 'total_saidas', 'saldo_final')
        }),
        ('Usuários', {
            'fields': ('usuario_abertura', 'usuario_fechamento')
        }),
        ('Datas', {
            'fields': ('data_hora_abertura', 'data_hora_fechamento'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        cor = '#27ae60' if obj.status == 'aberto' else '#95a5a6'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def saldo_formatado(self, obj):
        cor = 'green' if obj.saldo_final >= 0 else 'red'
        return format_html(
            '<span style="color: {};">R$ {:,.2f}</span>',
            cor, obj.saldo_final
        )
    saldo_formatado.short_description = "Saldo Final"

    def total_entradas_fmt(self, obj):
        return format_html('<span style="color: green;">R$ {:,.2f}</span>', obj.total_entradas)
    total_entradas_fmt.short_description = "Entradas"

    def total_saidas_fmt(self, obj):
        return format_html('<span style="color: red;">R$ {:,.2f}</span>', obj.total_saidas)
    total_saidas_fmt.short_description = "Saídas"


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    """Admin para movimentações."""
    list_display = [
        'data', 'caixa', 'tipo_badge', 'movimento',
        'valor_formatado', 'descricao_resumida'
    ]
    list_filter = ['tipo', 'movimento', 'caixa', 'plano_conta', 'data']
    search_fields = ['descricao']
    readonly_fields = ['created_at']
    autocomplete_fields = ['caixa', 'plano_conta', 'conta_receber', 'conta_pagar', 'venda', 'usuario', 'consultor']
    date_hierarchy = 'data'

    fieldsets = (
        ('Movimentação', {
            'fields': ('caixa', 'tipo', 'movimento', 'descricao', 'valor', 'data')
        }),
        ('Classificação', {
            'fields': ('plano_conta', 'forma_pagamento', 'documento')
        }),
        ('Referências', {
            'fields': ('conta_receber', 'conta_pagar', 'venda'),
            'classes': ('collapse',)
        }),
        ('Responsáveis', {
            'fields': ('usuario', 'consultor', 'pontos'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
    )

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
