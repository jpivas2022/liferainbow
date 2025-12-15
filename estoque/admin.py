"""
=============================================================================
LIFE RAINBOW 2.0 - Admin de Estoque
Configuração do Django Admin para gestão de estoque
=============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import F

from .models import Produto, MovimentacaoEstoque, Inventario


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    """Admin para produtos."""
    list_display = [
        'codigo', 'nome', 'categoria', 'quantidade_badge',
        'preco_venda_formatado', 'ativo'
    ]
    list_filter = ['categoria', 'ativo']
    search_fields = ['codigo', 'nome', 'codigo_barras']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['nome']

    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'codigo_barras', 'nome', 'descricao')
        }),
        ('Classificação', {
            'fields': ('categoria', 'fornecedor', 'unidade')
        }),
        ('Estoque', {
            'fields': ('estoque_atual', 'estoque_minimo', 'estoque_maximo', 'localizacao')
        }),
        ('Preços', {
            'fields': ('preco_custo', 'preco_venda')
        }),
        ('Imagem', {
            'fields': ('imagem',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Datas do Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def quantidade_badge(self, obj):
        if obj.estoque_atual <= obj.estoque_minimo:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; '
                'padding: 3px 8px; border-radius: 3px;">{} ⚠️</span>',
                obj.estoque_atual
            )
        elif obj.estoque_atual <= obj.estoque_minimo * 1.5:
            return format_html(
                '<span style="background-color: #f39c12; color: white; '
                'padding: 3px 8px; border-radius: 3px;">{}</span>',
                obj.estoque_atual
            )
        return format_html(
            '<span style="background-color: #27ae60; color: white; '
            'padding: 3px 8px; border-radius: 3px;">{}</span>',
            obj.estoque_atual
        )
    quantidade_badge.short_description = "Quantidade"

    def preco_venda_formatado(self, obj):
        return f"R$ {obj.preco_venda:,.2f}"
    preco_venda_formatado.short_description = "Preço Venda"

    actions = ['ativar_produtos', 'desativar_produtos']

    @admin.action(description="Ativar produtos selecionados")
    def ativar_produtos(self, request, queryset):
        queryset.update(ativo=True)

    @admin.action(description="Desativar produtos selecionados")
    def desativar_produtos(self, request, queryset):
        queryset.update(ativo=False)


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    """Admin para movimentações de estoque."""
    list_display = [
        'created_at', 'produto', 'tipo_badge', 'motivo', 'quantidade_badge',
        'valor_formatado', 'usuario'
    ]
    list_filter = ['tipo', 'motivo', 'created_at', 'produto__categoria']
    search_fields = ['produto__nome', 'produto__codigo', 'documento']
    autocomplete_fields = ['produto', 'usuario', 'ordem_servico', 'venda']
    readonly_fields = ['created_at', 'estoque_anterior', 'estoque_posterior']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Produto', {
            'fields': ('produto',)
        }),
        ('Movimentação', {
            'fields': ('tipo', 'motivo', 'quantidade')
        }),
        ('Estoque', {
            'fields': ('estoque_anterior', 'estoque_posterior'),
            'classes': ('collapse',)
        }),
        ('Valores', {
            'fields': ('valor_unitario',)
        }),
        ('Referências', {
            'fields': ('ordem_servico', 'venda', 'documento'),
            'classes': ('collapse',)
        }),
        ('Responsável', {
            'fields': ('usuario',)
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
    )

    def tipo_badge(self, obj):
        cores = {
            'entrada': '#27ae60',
            'saida': '#e74c3c',
            'ajuste': '#f39c12',
        }
        cor = cores.get(obj.tipo, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_tipo_display()
        )
    tipo_badge.short_description = "Tipo"

    def quantidade_badge(self, obj):
        sinal = '+' if obj.tipo == 'entrada' else '-'
        cor = 'green' if obj.tipo == 'entrada' else 'red'
        if obj.tipo == 'ajuste':
            sinal = '±'
            cor = 'orange'
        return format_html(
            '<span style="color: {};">{}{}</span>',
            cor, sinal, obj.quantidade
        )
    quantidade_badge.short_description = "Qtd"

    def valor_formatado(self, obj):
        if obj.valor_unitario:
            return f"R$ {obj.valor_unitario:,.2f}"
        return "-"
    valor_formatado.short_description = "Valor Unit."


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    """Admin para inventários."""
    list_display = [
        'data', 'status_badge', 'responsavel', 'total_itens', 'divergencias'
    ]
    list_filter = ['status', 'data']
    search_fields = ['observacoes']
    autocomplete_fields = ['responsavel']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'data'

    fieldsets = (
        ('Inventário', {
            'fields': ('data', 'status', 'responsavel')
        }),
        ('Totais', {
            'fields': ('total_itens', 'divergencias')
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

    def status_badge(self, obj):
        cores = {
            'andamento': '#f39c12',
            'finalizado': '#27ae60',
            'cancelado': '#95a5a6',
        }
        cor = cores.get(obj.status, '#3498db')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"
