"""
=============================================================================
LIFE RAINBOW 2.0 - Admin de Atendimentos
Configuração intuitiva para gestão de serviços em campo
=============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import TipoServico, CampoServico, Atendimento, RespostaAtendimento, FotoAtendimento


class CampoServicoInline(admin.TabularInline):
    """Inline para configurar campos dentro do tipo de serviço."""
    model = CampoServico
    extra = 1
    fields = ['nome', 'codigo', 'tipo_campo', 'secao', 'ordem', 'obrigatorio', 'ativo']
    ordering = ['ordem']


@admin.register(TipoServico)
class TipoServicoAdmin(admin.ModelAdmin):
    """Admin para tipos de serviço configuráveis."""
    list_display = ['nome', 'codigo', 'categoria', 'cor_badge', 'campos_count', 'ativo']
    list_filter = ['categoria', 'ativo']
    search_fields = ['nome', 'codigo']
    ordering = ['ordem', 'nome']
    inlines = [CampoServicoInline]

    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'codigo', 'categoria', 'descricao')
        }),
        ('Aparência', {
            'fields': ('cor', 'icone', 'ordem'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )

    def cor_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            obj.cor, obj.nome
        )
    cor_badge.short_description = 'Visual'

    def campos_count(self, obj):
        count = obj.campos.filter(ativo=True).count()
        return format_html(
            '<span style="color: {};">{} campos</span>',
            '#27ae60' if count > 0 else '#e74c3c',
            count
        )
    campos_count.short_description = 'Campos'


@admin.register(CampoServico)
class CampoServicoAdmin(admin.ModelAdmin):
    """Admin para campos dinâmicos de serviço."""
    list_display = ['nome', 'tipo_servico', 'tipo_campo_badge', 'secao', 'ordem', 'obrigatorio', 'ativo']
    list_filter = ['tipo_servico', 'tipo_campo', 'secao', 'obrigatorio', 'ativo']
    search_fields = ['nome', 'codigo', 'descricao']
    ordering = ['tipo_servico', 'ordem']
    autocomplete_fields = ['tipo_servico']

    fieldsets = (
        ('Identificação', {
            'fields': ('tipo_servico', 'nome', 'codigo', 'tipo_campo')
        }),
        ('Configuração', {
            'fields': ('descricao', 'placeholder', 'valor_padrao', 'opcoes')
        }),
        ('Organização', {
            'fields': ('secao', 'ordem')
        }),
        ('Validação', {
            'fields': ('obrigatorio', 'ativo')
        }),
    )

    def tipo_campo_badge(self, obj):
        cores = {
            'texto': '#3498db',
            'textarea': '#3498db',
            'numero': '#9b59b6',
            'decimal': '#9b59b6',
            'foto': '#e74c3c',
            'boolean': '#f39c12',
            'select': '#1abc9c',
            'gps': '#2ecc71',
        }
        cor = cores.get(obj.tipo_campo, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_tipo_campo_display()
        )
    tipo_campo_badge.short_description = 'Tipo'


class RespostaAtendimentoInline(admin.TabularInline):
    """Inline para ver respostas do atendimento."""
    model = RespostaAtendimento
    extra = 0
    readonly_fields = ['campo', 'valor_texto', 'valor_numero', 'valor_boolean']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class FotoAtendimentoInline(admin.TabularInline):
    """Inline para ver fotos do atendimento."""
    model = FotoAtendimento
    extra = 0
    readonly_fields = ['foto_preview', 'tipo', 'timestamp']
    fields = ['foto_preview', 'tipo', 'descricao', 'timestamp']

    def foto_preview(self, obj):
        if obj.foto:
            return format_html(
                '<img src="{}" style="max-height: 60px; border-radius: 4px;"/>',
                obj.foto.url
            )
        return '-'
    foto_preview.short_description = 'Preview'


@admin.register(Atendimento)
class AtendimentoAdmin(admin.ModelAdmin):
    """Admin principal para atendimentos."""
    list_display = [
        'numero', 'cliente', 'tipo_servico', 'status_badge',
        'consultor', 'data_agendada', 'duracao_display'
    ]
    list_filter = ['status', 'tipo_servico', 'consultor', 'data_agendada']
    search_fields = ['numero', 'cliente__nome', 'relatorio']
    readonly_fields = ['numero', 'created_at', 'updated_at', 'duracao_display']
    autocomplete_fields = ['cliente', 'endereco', 'equipamento', 'contrato_aluguel', 'venda', 'consultor', 'agendamento']
    date_hierarchy = 'data_agendada'
    inlines = [RespostaAtendimentoInline, FotoAtendimentoInline]

    fieldsets = (
        ('Identificação', {
            'fields': ('numero', 'tipo_servico', 'status')
        }),
        ('Cliente e Equipamento', {
            'fields': ('cliente', 'endereco', 'equipamento')
        }),
        ('Relacionamentos', {
            'fields': ('agendamento', 'contrato_aluguel', 'venda'),
            'classes': ('collapse',)
        }),
        ('Consultor e Agenda', {
            'fields': ('consultor', 'data_agendada', 'hora_agendada')
        }),
        ('Execução', {
            'fields': ('data_inicio', 'data_fim', 'duracao_display'),
            'classes': ('collapse',)
        }),
        ('Check-in', {
            'fields': ('checkin_latitude', 'checkin_longitude', 'checkin_endereco', 'checkin_timestamp'),
            'classes': ('collapse',)
        }),
        ('Checkout', {
            'fields': ('checkout_latitude', 'checkout_longitude', 'checkout_timestamp'),
            'classes': ('collapse',)
        }),
        ('Relatório', {
            'fields': ('relatorio', 'observacoes_internas')
        }),
        ('Satisfação do Cliente', {
            'fields': ('satisfacao_nota', 'satisfacao_comentario'),
            'classes': ('collapse',)
        }),
        ('Financeiro', {
            'fields': ('valor_total', 'conta_receber'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        cores = {
            'agendado': '#3498db',
            'em_andamento': '#f39c12',
            'pausado': '#e67e22',
            'finalizado': '#27ae60',
            'cancelado': '#e74c3c',
        }
        cor = cores.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def duracao_display(self, obj):
        duracao = obj.duracao
        if duracao:
            horas = duracao // 60
            minutos = duracao % 60
            if horas > 0:
                return f'{horas}h {minutos}min'
            return f'{minutos} min'
        return '-'
    duracao_display.short_description = 'Duração'

    actions = ['marcar_finalizado', 'marcar_cancelado']

    @admin.action(description="Marcar como Finalizado")
    def marcar_finalizado(self, request, queryset):
        queryset.update(status='finalizado', data_fim=timezone.now())

    @admin.action(description="Marcar como Cancelado")
    def marcar_cancelado(self, request, queryset):
        queryset.update(status='cancelado')


@admin.register(FotoAtendimento)
class FotoAtendimentoAdmin(admin.ModelAdmin):
    """Admin para fotos de atendimento."""
    list_display = ['atendimento', 'tipo', 'foto_preview', 'descricao', 'timestamp']
    list_filter = ['tipo', 'timestamp']
    search_fields = ['atendimento__numero', 'descricao']
    readonly_fields = ['foto_preview_large', 'created_at']
    autocomplete_fields = ['atendimento', 'campo']

    fieldsets = (
        ('Atendimento', {
            'fields': ('atendimento', 'campo')
        }),
        ('Foto', {
            'fields': ('foto', 'foto_preview_large', 'tipo', 'descricao')
        }),
        ('Localização', {
            'fields': ('latitude', 'longitude', 'timestamp'),
            'classes': ('collapse',)
        }),
    )

    def foto_preview(self, obj):
        if obj.foto:
            return format_html(
                '<img src="{}" style="max-height: 40px; border-radius: 4px;"/>',
                obj.foto.url
            )
        return '-'
    foto_preview.short_description = 'Preview'

    def foto_preview_large(self, obj):
        if obj.foto:
            return format_html(
                '<img src="{}" style="max-height: 300px; border-radius: 8px;"/>',
                obj.foto.url
            )
        return '-'
    foto_preview_large.short_description = 'Foto'
