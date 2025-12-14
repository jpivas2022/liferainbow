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
    list_filter = ['categoria', 'ativo', 'tipo']
    search_fields = ['codigo', 'nome', 'codigo_barras']
    readonly_fields = ['criado_em', 'atualizado_em']
    ordering = ['nome']

    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'codigo_barras', 'nome', 'descricao')
        }),
        ('Classificação', {
            'fields': ('categoria', 'tipo', 'marca', 'modelo_compativel')
        }),
        ('Estoque', {
            'fields': ('quantidade_atual', 'estoque_minimo', 'estoque_maximo', 'localizacao')
        }),
        ('Preços', {
            'fields': ('preco_custo', 'preco_venda', 'margem_lucro')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Datas do Sistema', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    def quantidade_badge(self, obj):
        if obj.quantidade_atual <= obj.estoque_minimo:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; '
                'padding: 3px 8px; border-radius: 3px;">{} ⚠️</span>',
                obj.quantidade_atual
            )
        elif obj.quantidade_atual <= obj.estoque_minimo * 1.5:
            return format_html(
                '<span style="background-color: #f39c12; color: white; '
                'padding: 3px 8px; border-radius: 3px;">{}</span>',
                obj.quantidade_atual
            )
        return format_html(
            '<span style="background-color: #27ae60; color: white; '
            'padding: 3px 8px; border-radius: 3px;">{}</span>',
            obj.quantidade_atual
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
        'data_hora', 'produto', 'tipo_badge', 'quantidade_badge',
        'custo_formatado', 'usuario'
    ]
    list_filter = ['tipo', 'data_hora', 'produto__categoria']
    search_fields = ['produto__nome', 'produto__codigo', 'motivo']
    autocomplete_fields = ['produto', 'usuario', 'ordem_servico', 'venda']
    readonly_fields = ['data_hora', 'quantidade_anterior', 'quantidade_posterior']
    date_hierarchy = 'data_hora'

    def tipo_badge(self, obj):
        cores = {
            'entrada': '#27ae60',
            'saida': '#e74c3c',
            'ajuste': '#f39c12',
            'devolucao': '#3498db',
            'transferencia': '#9b59b6',
        }
        cor = cores.get(obj.tipo, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_tipo_display()
        )
    tipo_badge.short_description = "Tipo"

    def quantidade_badge(self, obj):
        sinal = '+' if obj.tipo in ['entrada', 'devolucao'] else '-'
        cor = 'green' if obj.tipo in ['entrada', 'devolucao'] else 'red'
        if obj.tipo == 'ajuste':
            sinal = '±'
            cor = 'orange'
        return format_html(
            '<span style="color: {};">{}{}</span>',
            cor, sinal, obj.quantidade
        )
    quantidade_badge.short_description = "Qtd"

    def custo_formatado(self, obj):
        if obj.custo_unitario:
            return f"R$ {obj.custo_unitario:,.2f}"
        return "-"
    custo_formatado.short_description = "Custo Unit."


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    """Admin para inventários."""
    list_display = [
        'produto', 'data_inventario', 'quantidade_sistema', 'quantidade_contada',
        'diferenca_badge', 'realizado_por'
    ]
    list_filter = ['data_inventario', 'ajuste_realizado']
    search_fields = ['produto__nome', 'produto__codigo']
    autocomplete_fields = ['produto', 'realizado_por']
    readonly_fields = ['diferenca']
    date_hierarchy = 'data_inventario'

    def diferenca_badge(self, obj):
        if obj.diferenca == 0:
            return format_html('<span style="color: green;">OK</span>')
        elif obj.diferenca > 0:
            return format_html(
                '<span style="color: blue;">+{}</span>',
                obj.diferenca
            )
        else:
            return format_html(
                '<span style="color: red;">{}</span>',
                obj.diferenca
            )
    diferenca_badge.short_description = "Diferença"

    actions = ['aplicar_ajuste']

    @admin.action(description="Aplicar ajuste de estoque")
    def aplicar_ajuste(self, request, queryset):
        for inv in queryset.filter(ajuste_realizado=False):
            if inv.diferenca != 0:
                # Criar movimentação de ajuste
                MovimentacaoEstoque.objects.create(
                    produto=inv.produto,
                    tipo='ajuste',
                    quantidade=abs(inv.diferenca),
                    quantidade_anterior=inv.quantidade_sistema,
                    quantidade_posterior=inv.quantidade_contada,
                    motivo=f"Ajuste de inventário - {inv.observacao or 'Sem observação'}",
                    usuario=request.user
                )
                # Atualizar produto
                inv.produto.quantidade_atual = inv.quantidade_contada
                inv.produto.save()
                # Marcar como ajustado
                inv.ajuste_realizado = True
                inv.save()
