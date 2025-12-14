"""
=============================================================================
LIFE RAINBOW 2.0 - Admin de Equipamentos
Configuração do Django Admin para gestão de equipamentos Rainbow
=============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import ModeloEquipamento, Equipamento, HistoricoManutencao


class HistoricoManutencaoInline(admin.TabularInline):
    """Inline para histórico de manutenção."""
    model = HistoricoManutencao
    extra = 0
    readonly_fields = ['data_manutencao']
    fields = ['tipo', 'descricao', 'valor', 'tecnico', 'data_manutencao']


@admin.register(ModeloEquipamento)
class ModeloEquipamentoAdmin(admin.ModelAdmin):
    """Admin para modelos de equipamento Rainbow."""
    list_display = ['nome', 'codigo', 'tipo', 'preco_venda', 'preco_aluguel', 'ativo']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome', 'codigo']
    ordering = ['nome']


@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    """Admin para equipamentos Rainbow."""
    list_display = [
        'numero_serie', 'modelo', 'cliente', 'status_badge',
        'data_compra', 'garantia_status', 'ultima_manutencao'
    ]
    list_filter = ['status', 'modelo', 'origem']
    search_fields = ['numero_serie', 'cliente__nome']
    readonly_fields = ['data_cadastro', 'atualizado_em']
    autocomplete_fields = ['cliente', 'modelo']
    date_hierarchy = 'data_compra'

    fieldsets = (
        ('Identificação', {
            'fields': ('numero_serie', 'modelo', 'cor')
        }),
        ('Propriedade', {
            'fields': ('cliente', 'status', 'origem')
        }),
        ('Compra e Garantia', {
            'fields': ('data_compra', 'valor_compra', 'garantia_ate')
        }),
        ('Manutenção', {
            'fields': ('ultima_manutencao', 'proxima_manutencao', 'horas_uso'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
        ('Datas do Sistema', {
            'fields': ('data_cadastro', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    inlines = [HistoricoManutencaoInline]

    def status_badge(self, obj):
        cores = {
            'ativo': '#27ae60',
            'em_manutencao': '#f39c12',
            'inativo': '#e74c3c',
            'devolvido': '#95a5a6',
        }
        cor = cores.get(obj.status, '#3498db')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def garantia_status(self, obj):
        if not obj.garantia_ate:
            return format_html('<span style="color: gray;">Sem garantia</span>')

        hoje = timezone.now().date()
        if obj.garantia_ate < hoje:
            return format_html(
                '<span style="color: red;">Expirada em {}</span>',
                obj.garantia_ate.strftime('%d/%m/%Y')
            )
        elif obj.garantia_ate <= hoje + timezone.timedelta(days=30):
            return format_html(
                '<span style="color: orange;">Vence em {}</span>',
                obj.garantia_ate.strftime('%d/%m/%Y')
            )
        return format_html(
            '<span style="color: green;">Até {}</span>',
            obj.garantia_ate.strftime('%d/%m/%Y')
        )
    garantia_status.short_description = "Garantia"


@admin.register(HistoricoManutencao)
class HistoricoManutencaoAdmin(admin.ModelAdmin):
    """Admin para histórico de manutenção."""
    list_display = ['equipamento', 'tipo', 'descricao_resumida', 'valor', 'tecnico', 'data_manutencao']
    list_filter = ['tipo', 'data_manutencao', 'tecnico']
    search_fields = ['equipamento__numero_serie', 'descricao']
    date_hierarchy = 'data_manutencao'

    def descricao_resumida(self, obj):
        if len(obj.descricao) > 50:
            return f"{obj.descricao[:50]}..."
        return obj.descricao
    descricao_resumida.short_description = "Descrição"
