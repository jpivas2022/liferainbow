"""
=============================================================================
LIFE RAINBOW 2.0 - Admin de Aluguéis
Configuração do Django Admin para gestão de contratos de aluguel
=============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal

from .models import ContratoAluguel, ParcelaAluguel, HistoricoAluguel


class ParcelaAluguelInline(admin.TabularInline):
    """Inline para parcelas do aluguel."""
    model = ParcelaAluguel
    extra = 0
    fields = ['numero', 'valor', 'data_vencimento', 'data_pagamento', 'valor_pago', 'status']
    readonly_fields = ['numero']

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('numero')


class HistoricoAluguelInline(admin.TabularInline):
    """Inline para histórico do aluguel."""
    model = HistoricoAluguel
    extra = 0
    readonly_fields = ['data_hora', 'usuario']
    fields = ['tipo', 'descricao', 'data_hora', 'usuario']

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ContratoAluguel)
class ContratoAluguelAdmin(admin.ModelAdmin):
    """Admin para contratos de aluguel."""
    list_display = [
        'numero', 'cliente', 'equipamento_serie', 'data_inicio', 'data_fim',
        'valor_mensal_formatado', 'status_badge', 'parcelas_status'
    ]
    list_filter = ['status', 'data_inicio', 'duracao_meses']
    search_fields = ['numero', 'cliente__nome', 'equipamento__numero_serie']
    readonly_fields = ['numero', 'criado_em', 'atualizado_em']
    autocomplete_fields = ['cliente', 'equipamento', 'venda_origem']
    date_hierarchy = 'data_inicio'

    fieldsets = (
        ('Identificação', {
            'fields': ('numero', 'cliente', 'equipamento', 'venda_origem')
        }),
        ('Período', {
            'fields': ('data_inicio', 'data_fim', 'duracao_meses')
        }),
        ('Valores', {
            'fields': ('valor_mensal', 'caucao', 'desconto_mensal')
        }),
        ('Status', {
            'fields': ('status', 'motivo_cancelamento'),
        }),
        ('Entrega', {
            'fields': ('endereco_entrega', 'observacoes'),
            'classes': ('collapse',)
        }),
        ('Datas do Sistema', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    inlines = [ParcelaAluguelInline, HistoricoAluguelInline]

    def equipamento_serie(self, obj):
        return obj.equipamento.numero_serie if obj.equipamento else "-"
    equipamento_serie.short_description = "Equipamento"

    def valor_mensal_formatado(self, obj):
        return f"R$ {obj.valor_mensal:,.2f}"
    valor_mensal_formatado.short_description = "Valor Mensal"

    def status_badge(self, obj):
        cores = {
            'rascunho': '#3498db',
            'ativo': '#27ae60',
            'suspenso': '#f39c12',
            'finalizado': '#95a5a6',
            'cancelado': '#e74c3c',
        }
        cor = cores.get(obj.status, '#3498db')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def parcelas_status(self, obj):
        parcelas = obj.parcelas.all()
        total = parcelas.count()
        pagas = parcelas.filter(status='pago').count()
        atrasadas = parcelas.filter(
            status='pendente',
            data_vencimento__lt=timezone.now().date()
        ).count()

        if atrasadas > 0:
            return format_html(
                '<span style="color: red;">{} atrasada(s)</span> | {}/{}',
                atrasadas, pagas, total
            )
        return f"{pagas}/{total} pagas"
    parcelas_status.short_description = "Parcelas"

    actions = ['gerar_parcelas', 'ativar_contratos', 'cancelar_contratos']

    @admin.action(description="Gerar parcelas para contratos selecionados")
    def gerar_parcelas(self, request, queryset):
        for contrato in queryset:
            if contrato.parcelas.count() == 0:
                contrato.gerar_parcelas()

    @admin.action(description="Ativar contratos selecionados")
    def ativar_contratos(self, request, queryset):
        queryset.filter(status='rascunho').update(status='ativo')

    @admin.action(description="Cancelar contratos selecionados")
    def cancelar_contratos(self, request, queryset):
        queryset.exclude(status='finalizado').update(status='cancelado')


@admin.register(ParcelaAluguel)
class ParcelaAluguelAdmin(admin.ModelAdmin):
    """Admin para parcelas de aluguel (acesso direto)."""
    list_display = [
        'contrato', 'numero', 'valor_formatado', 'data_vencimento',
        'data_pagamento', 'status_badge', 'dias_atraso'
    ]
    list_filter = ['status', 'data_vencimento']
    search_fields = ['contrato__numero', 'contrato__cliente__nome']
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

    def dias_atraso(self, obj):
        if obj.status == 'pendente' and obj.data_vencimento < timezone.now().date():
            dias = (timezone.now().date() - obj.data_vencimento).days
            return format_html('<span style="color: red;">{} dias</span>', dias)
        return "-"
    dias_atraso.short_description = "Atraso"

    actions = ['marcar_como_pago']

    @admin.action(description="Marcar como pago")
    def marcar_como_pago(self, request, queryset):
        for parcela in queryset.filter(status__in=['pendente', 'atrasado']):
            parcela.status = 'pago'
            parcela.data_pagamento = timezone.now().date()
            parcela.valor_pago = parcela.valor
            parcela.save()
