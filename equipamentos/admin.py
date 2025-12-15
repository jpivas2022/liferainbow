"""
=============================================================================
LIFE RAINBOW 2.0 - Admin de Equipamentos
Configuração do Django Admin para gestão de equipamentos Rainbow
=============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta

from .models import ModeloEquipamento, Equipamento, HistoricoManutencao


class HistoricoManutencaoInline(admin.TabularInline):
    """Inline para histórico de manutenção."""
    model = HistoricoManutencao
    extra = 0
    readonly_fields = ['created_at']
    fields = ['tipo', 'status', 'data_agendamento', 'descricao_problema', 'valor_total', 'tecnico', 'created_at']


@admin.register(ModeloEquipamento)
class ModeloEquipamentoAdmin(admin.ModelAdmin):
    """Admin para modelos de equipamento Rainbow."""
    list_display = ['nome', 'codigo', 'categoria', 'preco_venda', 'preco_aluguel_mensal', 'ativo']
    list_filter = ['categoria', 'ativo']
    search_fields = ['nome', 'codigo']
    ordering = ['nome']

    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'codigo', 'categoria', 'descricao')
        }),
        ('Preços', {
            'fields': ('preco_venda', 'preco_aluguel_mensal', 'preco_custo')
        }),
        ('Especificações', {
            'fields': ('voltagem', 'potencia', 'peso'),
            'classes': ('collapse',)
        }),
        ('Manutenção e Garantia', {
            'fields': ('intervalo_manutencao_meses', 'garantia_meses'),
            'classes': ('collapse',)
        }),
        ('Imagem', {
            'fields': ('imagem',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )


@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    """Admin para equipamentos Rainbow."""
    list_display = [
        'numero_serie', 'modelo', 'cliente', 'status_badge',
        'data_aquisicao', 'garantia_status', 'data_ultima_manutencao'
    ]
    list_filter = ['status', 'modelo', 'condicao']
    search_fields = ['numero_serie', 'cliente__nome']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['cliente', 'modelo']
    date_hierarchy = 'data_aquisicao'

    fieldsets = (
        ('Identificação', {
            'fields': ('numero_serie', 'modelo', 'condicao')
        }),
        ('Propriedade', {
            'fields': ('cliente', 'status', 'localizacao')
        }),
        ('Aquisição e Garantia', {
            'fields': ('data_aquisicao', 'data_venda', 'data_fim_garantia')
        }),
        ('Manutenção', {
            'fields': ('data_ultima_manutencao', 'data_proxima_manutencao'),
            'classes': ('collapse',)
        }),
        ('Power Rainbow', {
            'fields': ('possui_power', 'numero_power'),
            'classes': ('collapse',)
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

    inlines = [HistoricoManutencaoInline]

    def status_badge(self, obj):
        cores = {
            'estoque': '#3498db',
            'vendido': '#27ae60',
            'alugado': '#f39c12',
            'manutencao': '#e67e22',
            'demonstracao': '#9b59b6',
            'sucata': '#e74c3c',
        }
        cor = cores.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def garantia_status(self, obj):
        if not obj.data_fim_garantia:
            return format_html('<span style="color: gray;">Sem garantia</span>')

        hoje = timezone.now().date()
        if obj.data_fim_garantia < hoje:
            return format_html(
                '<span style="color: red;">Expirada em {}</span>',
                obj.data_fim_garantia.strftime('%d/%m/%Y')
            )
        elif obj.data_fim_garantia <= hoje + timedelta(days=30):
            return format_html(
                '<span style="color: orange;">Vence em {}</span>',
                obj.data_fim_garantia.strftime('%d/%m/%Y')
            )
        return format_html(
            '<span style="color: green;">Até {}</span>',
            obj.data_fim_garantia.strftime('%d/%m/%Y')
        )
    garantia_status.short_description = "Garantia"


@admin.register(HistoricoManutencao)
class HistoricoManutencaoAdmin(admin.ModelAdmin):
    """Admin para histórico de manutenção."""
    list_display = ['equipamento', 'tipo', 'status', 'descricao_resumida', 'valor_total', 'tecnico', 'data_agendamento']
    list_filter = ['tipo', 'status', 'data_agendamento', 'tecnico']
    search_fields = ['equipamento__numero_serie', 'descricao_problema']
    autocomplete_fields = ['equipamento', 'tecnico']
    date_hierarchy = 'data_agendamento'

    fieldsets = (
        ('Equipamento', {
            'fields': ('equipamento',)
        }),
        ('Manutenção', {
            'fields': ('tipo', 'status', 'data_agendamento', 'data_realizacao', 'tecnico')
        }),
        ('Detalhes', {
            'fields': ('descricao_problema', 'servicos_realizados', 'pecas_substituidas')
        }),
        ('Valores', {
            'fields': ('valor_mao_obra', 'valor_pecas', 'valor_total')
        }),
        ('Garantia', {
            'fields': ('coberto_garantia', 'garantia_servico_dias'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
    )

    def descricao_resumida(self, obj):
        if obj.descricao_problema and len(obj.descricao_problema) > 50:
            return f"{obj.descricao_problema[:50]}..."
        return obj.descricao_problema or "-"
    descricao_resumida.short_description = "Descrição"
