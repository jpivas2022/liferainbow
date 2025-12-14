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
    readonly_fields = ['data_hora', 'direcao', 'tipo', 'conteudo', 'status']
    fields = ['data_hora', 'direcao', 'tipo', 'conteudo', 'status']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Conversa)
class ConversaAdmin(admin.ModelAdmin):
    """Admin para conversas WhatsApp."""
    list_display = [
        'telefone', 'cliente', 'status_badge', 'ultima_mensagem',
        'iniciada_em', 'atualizada_em'
    ]
    list_filter = ['status', 'iniciada_em']
    search_fields = ['telefone', 'cliente__nome']
    autocomplete_fields = ['cliente', 'atendente']
    readonly_fields = ['iniciada_em', 'atualizada_em', 'waid']

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
        msg = obj.mensagens.order_by('-data_hora').first()
        if msg:
            texto = msg.conteudo[:50] + '...' if len(msg.conteudo) > 50 else msg.conteudo
            return f"{msg.data_hora.strftime('%d/%m %H:%M')} - {texto}"
        return "-"
    ultima_mensagem.short_description = "Última Mensagem"


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    """Admin para mensagens (acesso direto)."""
    list_display = ['conversa', 'direcao_badge', 'tipo', 'conteudo_resumido', 'status_badge', 'data_hora']
    list_filter = ['direcao', 'tipo', 'status', 'data_hora']
    search_fields = ['conteudo', 'conversa__telefone']
    readonly_fields = ['data_hora', 'wamid']
    date_hierarchy = 'data_hora'

    def direcao_badge(self, obj):
        if obj.direcao == 'enviada':
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
            'enviada': '#3498db',
            'entregue': '#27ae60',
            'lida': '#2ecc71',
            'recebida': '#27ae60',
            'erro': '#e74c3c',
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
    list_display = ['nome', 'categoria_badge', 'idioma', 'status_badge', 'custo_estimado']
    list_filter = ['categoria', 'status', 'idioma']
    search_fields = ['nome', 'conteudo']
    readonly_fields = ['criado_em', 'atualizado_em']

    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'categoria', 'idioma')
        }),
        ('Conteúdo', {
            'fields': ('cabecalho', 'conteudo', 'rodape', 'variaveis')
        }),
        ('Botões', {
            'fields': ('botoes',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    def categoria_badge(self, obj):
        cores = {
            'utility': '#3498db',
            'marketing': '#9b59b6',
            'authentication': '#27ae60',
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
            'rascunho': '#f39c12',
            'pendente': '#3498db',
            'aprovado': '#27ae60',
            'rejeitado': '#e74c3c',
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
            'utility': 'R$ 0,04',
            'marketing': 'R$ 0,38',
            'authentication': 'R$ 0,04',
        }
        return custos.get(obj.categoria, '-')
    custo_estimado.short_description = "Custo/msg"


@admin.register(CampanhaMensagem)
class CampanhaMensagemAdmin(admin.ModelAdmin):
    """Admin para campanhas de mensagem."""
    list_display = [
        'nome', 'template', 'status_badge', 'total_destinatarios',
        'metricas', 'criado_por', 'criada_em'
    ]
    list_filter = ['status', 'template', 'criada_em']
    search_fields = ['nome']
    autocomplete_fields = ['template', 'criado_por']
    readonly_fields = [
        'criada_em', 'iniciada_em', 'finalizada_em',
        'total_enviados', 'total_entregues', 'total_lidos', 'total_erros'
    ]

    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'descricao', 'template')
        }),
        ('Destinatários', {
            'fields': ('destinatarios',),
            'description': 'JSON com lista de destinatários e variáveis'
        }),
        ('Agendamento', {
            'fields': ('agendada_para',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Métricas', {
            'fields': (
                'total_enviados', 'total_entregues', 'total_lidos', 'total_erros'
            ),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('criado_por', 'criada_em', 'iniciada_em', 'finalizada_em'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        cores = {
            'rascunho': '#95a5a6',
            'agendada': '#3498db',
            'em_execucao': '#f39c12',
            'pausada': '#e67e22',
            'finalizada': '#27ae60',
            'cancelada': '#e74c3c',
        }
        cor = cores.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def total_destinatarios(self, obj):
        if obj.destinatarios:
            return len(obj.destinatarios)
        return 0
    total_destinatarios.short_description = "Destinatários"

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

    actions = ['iniciar_campanha', 'pausar_campanha', 'cancelar_campanha']

    @admin.action(description="Iniciar campanha")
    def iniciar_campanha(self, request, queryset):
        queryset.filter(status='rascunho').update(status='agendada')

    @admin.action(description="Pausar campanha")
    def pausar_campanha(self, request, queryset):
        queryset.filter(status='em_execucao').update(status='pausada')

    @admin.action(description="Cancelar campanha")
    def cancelar_campanha(self, request, queryset):
        queryset.exclude(status='finalizada').update(status='cancelada')
