"""
=============================================================================
LIFE RAINBOW 2.0 - Admin de WhatsApp
Configuração do Django Admin para gestão de WhatsApp
=============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Conversa, Mensagem, Template, CampanhaMensagem


class MensagemInline(admin.TabularInline):
    """Inline para mensagens da conversa."""
    model = Mensagem
    extra = 0
    readonly_fields = ['created_at', 'direcao', 'tipo', 'conteudo', 'status']
    fields = ['created_at', 'direcao', 'tipo', 'conteudo', 'status']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Conversa)
class ConversaAdmin(admin.ModelAdmin):
    """Admin para conversas WhatsApp."""
    list_display = [
        'telefone', 'cliente', 'status_badge', 'modo_atendimento',
        'ultima_mensagem', 'created_at', 'updated_at'
    ]
    list_filter = ['status', 'modo_atendimento', 'created_at']
    search_fields = ['telefone', 'cliente__nome', 'nome_contato']
    autocomplete_fields = ['cliente', 'atendente']
    readonly_fields = ['created_at', 'updated_at', 'wa_id']

    inlines = [MensagemInline]

    def status_badge(self, obj):
        cores = {
            'ativa': '#27ae60',
            'aguardando': '#f39c12',
            'encerrada': '#95a5a6',
        }
        cor = cores.get(obj.status, '#3498db')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def ultima_mensagem(self, obj):
        msg = obj.mensagens.order_by('-created_at').first()
        if msg:
            texto = msg.conteudo[:50] + '...' if len(msg.conteudo) > 50 else msg.conteudo
            return f"{msg.created_at.strftime('%d/%m %H:%M')} - {texto}"
        return "-"
    ultima_mensagem.short_description = "Última Mensagem"


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    """Admin para mensagens (acesso direto)."""
    list_display = ['conversa', 'direcao_badge', 'tipo', 'conteudo_resumido', 'status_badge', 'created_at']
    list_filter = ['direcao', 'tipo', 'status', 'created_at']
    search_fields = ['conteudo', 'conversa__telefone']
    readonly_fields = ['created_at', 'wamid']
    date_hierarchy = 'created_at'

    def direcao_badge(self, obj):
        if obj.direcao == 'saida':
            return format_html(
                '<span style="color: blue;">→ Enviada</span>'
            )
        return format_html('<span style="color: green;">← Recebida</span>')
    direcao_badge.short_description = "Direção"

    def conteudo_resumido(self, obj):
        if len(obj.conteudo) > 60:
            return f"{obj.conteudo[:60]}..."
        return obj.conteudo
    conteudo_resumido.short_description = "Conteúdo"

    def status_badge(self, obj):
        cores = {
            'enviando': '#3498db',
            'enviada': '#3498db',
            'entregue': '#27ae60',
            'lida': '#2ecc71',
            'falha': '#e74c3c',
        }
        cor = cores.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    """Admin para templates WhatsApp."""
    list_display = ['nome', 'categoria_badge', 'idioma', 'status_badge', 'custo_estimado', 'ativo']
    list_filter = ['categoria', 'status', 'idioma', 'ativo']
    search_fields = ['nome', 'body_text']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'categoria', 'idioma', 'ativo')
        }),
        ('Conteúdo', {
            'fields': ('header_text', 'body_text', 'footer_text', 'variaveis')
        }),
        ('Botões', {
            'fields': ('botoes',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Uso', {
            'fields': ('descricao_uso',),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def categoria_badge(self, obj):
        cores = {
            'UTILITY': '#3498db',
            'MARKETING': '#9b59b6',
            'AUTHENTICATION': '#27ae60',
        }
        cor = cores.get(obj.categoria, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_categoria_display()
        )
    categoria_badge.short_description = "Categoria"

    def status_badge(self, obj):
        cores = {
            'PENDING': '#f39c12',
            'APPROVED': '#27ae60',
            'REJECTED': '#e74c3c',
        }
        cor = cores.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def custo_estimado(self, obj):
        custos = {
            'UTILITY': 'R$ 0,04',
            'MARKETING': 'R$ 0,38',
            'AUTHENTICATION': 'R$ 0,04',
        }
        return custos.get(obj.categoria, '-')
    custo_estimado.short_description = "Custo/msg"


@admin.register(CampanhaMensagem)
class CampanhaMensagemAdmin(admin.ModelAdmin):
    """Admin para campanhas de mensagem."""
    list_display = [
        'nome', 'template', 'status_badge', 'total_destinatarios',
        'metricas', 'created_by', 'created_at'
    ]
    list_filter = ['status', 'template', 'created_at']
    search_fields = ['nome']
    autocomplete_fields = ['template', 'created_by', 'filtro_consultor']
    readonly_fields = [
        'created_at', 'data_inicio', 'data_conclusao',
        'total_enviados', 'total_entregues', 'total_lidos', 'total_falhas', 'total_respostas'
    ]

    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'descricao', 'template')
        }),
        ('Filtros de Público', {
            'fields': ('filtro_perfil', 'filtro_segmento', 'filtro_consultor'),
            'description': 'Filtros para selecionar destinatários'
        }),
        ('Agendamento', {
            'fields': ('data_agendada',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Custos', {
            'fields': ('custo_estimado', 'custo_real'),
            'classes': ('collapse',)
        }),
        ('Métricas', {
            'fields': (
                'total_destinatarios', 'total_enviados', 'total_entregues',
                'total_lidos', 'total_falhas', 'total_respostas'
            ),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'data_inicio', 'data_conclusao'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        cores = {
            'rascunho': '#95a5a6',
            'agendada': '#3498db',
            'enviando': '#f39c12',
            'concluida': '#27ae60',
            'cancelada': '#e74c3c',
        }
        cor = cores.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def metricas(self, obj):
        if obj.total_enviados > 0:
            taxa_entrega = (obj.total_entregues / obj.total_enviados) * 100
            taxa_leitura = (obj.total_lidos / obj.total_enviados) * 100
            return format_html(
                '📤 {} | ✓ {:.0f}% | 👁 {:.0f}%',
                obj.total_enviados, taxa_entrega, taxa_leitura
            )
        return "-"
    metricas.short_description = "Métricas"

    actions = ['iniciar_campanha', 'cancelar_campanha']

    @admin.action(description="Iniciar/Agendar campanha")
    def iniciar_campanha(self, request, queryset):
        queryset.filter(status='rascunho').update(status='agendada')

    @admin.action(description="Cancelar campanha")
    def cancelar_campanha(self, request, queryset):
        queryset.exclude(status='concluida').update(status='cancelada')
