"""
=============================================================================
LIFE RAINBOW 2.0 - Admin de Clientes
Configuração do Django Admin para gestão de clientes
=============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta

from .models import Cliente, Endereco, HistoricoInteracao


class EnderecoInline(admin.TabularInline):
    """Inline para endereços do cliente."""
    model = Endereco
    extra = 1
    fields = ['tipo', 'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'principal']


class HistoricoInteracaoInline(admin.TabularInline):
    """Inline para histórico de interações."""
    model = HistoricoInteracao
    extra = 0
    readonly_fields = ['created_at', 'usuario']
    fields = ['tipo', 'direcao', 'descricao', 'resultado', 'created_at', 'usuario']

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    """Admin para clientes."""
    list_display = [
        'nome', 'telefone', 'email', 'perfil_badge',
        'status_badge', 'possui_rainbow', 'dias_sem_contato', 'consultor_responsavel'
    ]
    list_filter = ['status', 'perfil', 'possui_rainbow', 'segmento', 'consultor_responsavel']
    search_fields = ['nome', 'email', 'telefone', 'cpf_cnpj']
    readonly_fields = ['created_at', 'updated_at', 'data_ultimo_contato']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['consultor_responsavel', 'created_by']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'tipo_pessoa', 'email', 'telefone', 'telefone_secundario', 'whatsapp')
        }),
        ('Documentos', {
            'fields': ('cpf_cnpj', 'inscricao_estadual'),
            'classes': ('collapse',)
        }),
        ('Classificação', {
            'fields': ('perfil', 'status', 'segmento', 'origem', 'consultor_responsavel')
        }),
        ('Rainbow', {
            'fields': ('possui_rainbow', 'data_compra_rainbow', 'poder_compra')
        }),
        ('Acompanhamento', {
            'fields': ('data_proxima_ligacao', 'data_ultimo_contato', 'status_acompanhamento'),
            'classes': ('collapse',)
        }),
        ('Dados Bancários', {
            'fields': ('banco', 'agencia', 'conta'),
            'classes': ('collapse',)
        }),
        ('Marketing', {
            'fields': ('perfil_marketing', 'aceita_whatsapp', 'aceita_email'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes', 'relatorio'),
            'classes': ('collapse',)
        }),
        ('Datas do Sistema', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    inlines = [EnderecoInline, HistoricoInteracaoInline]

    def perfil_badge(self, obj):
        cores = {
            'diamante': '#9b59b6',
            'ouro': '#f39c12',
            'prata': '#95a5a6',
            'bronze': '#cd6133',
            'standard': '#3498db',
        }
        cor = cores.get(obj.perfil, '#3498db')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_perfil_display()
        )
    perfil_badge.short_description = "Perfil"

    def status_badge(self, obj):
        cores = {
            'ativo': '#27ae60',
            'inativo': '#e74c3c',
            'prospecto': '#f39c12',
        }
        cor = cores.get(obj.status, '#3498db')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def dias_sem_contato(self, obj):
        if obj.data_ultimo_contato:
            dias = (timezone.now() - obj.data_ultimo_contato).days
            if dias > 30:
                return format_html(
                    '<span style="color: red; font-weight: bold;">{} dias</span>',
                    dias
                )
            elif dias > 15:
                return format_html(
                    '<span style="color: orange;">{} dias</span>',
                    dias
                )
            return f"{dias} dias"
        return format_html('<span style="color: red;">Nunca</span>')
    dias_sem_contato.short_description = "Último Contato"

    actions = ['marcar_como_ativo', 'marcar_como_inativo']

    @admin.action(description="Marcar selecionados como Ativos")
    def marcar_como_ativo(self, request, queryset):
        queryset.update(status='ativo')

    @admin.action(description="Marcar selecionados como Inativos")
    def marcar_como_inativo(self, request, queryset):
        queryset.update(status='inativo')


@admin.register(Endereco)
class EnderecoAdmin(admin.ModelAdmin):
    """Admin para endereços (acesso direto)."""
    list_display = ['cliente', 'tipo', 'logradouro', 'cidade', 'estado', 'principal']
    list_filter = ['tipo', 'estado', 'principal']
    search_fields = ['cliente__nome', 'logradouro', 'cidade']


@admin.register(HistoricoInteracao)
class HistoricoInteracaoAdmin(admin.ModelAdmin):
    """Admin para histórico de interações."""
    list_display = ['cliente', 'tipo', 'direcao', 'descricao_resumida', 'created_at', 'usuario']
    list_filter = ['tipo', 'direcao', 'created_at']
    search_fields = ['cliente__nome', 'descricao']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

    def descricao_resumida(self, obj):
        if len(obj.descricao) > 50:
            return f"{obj.descricao[:50]}..."
        return obj.descricao
    descricao_resumida.short_description = "Descrição"
