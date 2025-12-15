"""
=============================================================================
LIFE RAINBOW 2.0 - Criar Tipos de Tarefa Padrão
Popula os tipos de tarefas técnicas para os assistentes
=============================================================================
"""

from django.core.management.base import BaseCommand
from assistencia.models_tarefas import TipoTarefaTecnica


class Command(BaseCommand):
    help = 'Cria os tipos de tarefas técnicas padrão'

    def handle(self, *args, **options):
        tipos_tarefa = [
            # ORÇAMENTOS
            {
                'codigo': 'orcamento_geral',
                'nome': 'Fazer Orçamento',
                'categoria': 'orcamento',
                'descricao': 'Avaliar equipamento e criar orçamento para o cliente',
                'tempo_estimado_minutos': 30,
                'requer_equipamento': True,
                'requer_os': True,
                'pode_ser_recorrente': False,
                'icone': '💰',
                'cor': '#9b59b6',
                'ordem': 1,
            },
            {
                'codigo': 'orcamento_revisao',
                'nome': 'Orçamento de Revisão',
                'categoria': 'orcamento',
                'descricao': 'Orçamento para revisão completa do equipamento',
                'tempo_estimado_minutos': 45,
                'requer_equipamento': True,
                'requer_os': True,
                'pode_ser_recorrente': False,
                'icone': '📋',
                'cor': '#9b59b6',
                'ordem': 2,
            },

            # CONSERTOS
            {
                'codigo': 'conserto_motor',
                'nome': 'Conserto Motor',
                'categoria': 'conserto',
                'descricao': 'Reparo ou substituição de motor',
                'tempo_estimado_minutos': 120,
                'requer_equipamento': True,
                'requer_os': True,
                'pode_ser_recorrente': False,
                'icone': '⚡',
                'cor': '#e74c3c',
                'ordem': 10,
            },
            {
                'codigo': 'conserto_bacia',
                'nome': 'Conserto Bacia',
                'categoria': 'conserto',
                'descricao': 'Reparo ou substituição de bacia',
                'tempo_estimado_minutos': 60,
                'requer_equipamento': True,
                'requer_os': True,
                'pode_ser_recorrente': False,
                'icone': '🔧',
                'cor': '#e74c3c',
                'ordem': 11,
            },
            {
                'codigo': 'conserto_mangueira',
                'nome': 'Conserto Mangueira',
                'categoria': 'conserto',
                'descricao': 'Reparo ou substituição de mangueira',
                'tempo_estimado_minutos': 30,
                'requer_equipamento': True,
                'requer_os': True,
                'pode_ser_recorrente': False,
                'icone': '🔧',
                'cor': '#e74c3c',
                'ordem': 12,
            },
            {
                'codigo': 'conserto_geral',
                'nome': 'Conserto Geral',
                'categoria': 'conserto',
                'descricao': 'Conserto diversos não especificado',
                'tempo_estimado_minutos': 60,
                'requer_equipamento': True,
                'requer_os': True,
                'pode_ser_recorrente': False,
                'icone': '🛠️',
                'cor': '#e74c3c',
                'ordem': 19,
            },

            # LIMPEZA
            {
                'codigo': 'lavar_rainbow',
                'nome': 'Lavar Rainbow',
                'categoria': 'limpeza',
                'descricao': 'Lavagem completa do Rainbow',
                'tempo_estimado_minutos': 45,
                'requer_equipamento': True,
                'requer_os': False,
                'pode_ser_recorrente': False,
                'icone': '🧼',
                'cor': '#3498db',
                'ordem': 20,
            },
            {
                'codigo': 'limpar_rainbow_aluguel',
                'nome': 'Limpar Rainbow de Aluguel',
                'categoria': 'limpeza',
                'descricao': 'Limpeza completa do Rainbow retornado de aluguel',
                'tempo_estimado_minutos': 60,
                'requer_equipamento': True,
                'requer_os': False,
                'pode_ser_recorrente': False,
                'icone': '🧹',
                'cor': '#3498db',
                'ordem': 21,
            },
            {
                'codigo': 'limpar_lavadora',
                'nome': 'Limpar Lavadora/AquaMate',
                'categoria': 'limpeza',
                'descricao': 'Limpeza de lavadora ou AquaMate',
                'tempo_estimado_minutos': 30,
                'requer_equipamento': True,
                'requer_os': False,
                'pode_ser_recorrente': False,
                'icone': '💧',
                'cor': '#3498db',
                'ordem': 22,
            },
            {
                'codigo': 'limpar_filtros',
                'nome': 'Limpar/Trocar Filtros',
                'categoria': 'limpeza',
                'descricao': 'Limpeza ou troca de filtros HEPA',
                'tempo_estimado_minutos': 20,
                'requer_equipamento': True,
                'requer_os': False,
                'pode_ser_recorrente': False,
                'icone': '🌀',
                'cor': '#3498db',
                'ordem': 23,
            },

            # MONTAGEM
            {
                'codigo': 'montar_rainbow',
                'nome': 'Montar Rainbow',
                'categoria': 'montagem',
                'descricao': 'Montagem completa do Rainbow após manutenção',
                'tempo_estimado_minutos': 60,
                'requer_equipamento': True,
                'requer_os': False,
                'pode_ser_recorrente': False,
                'icone': '🔩',
                'cor': '#f39c12',
                'ordem': 30,
            },
            {
                'codigo': 'desmontar_rainbow',
                'nome': 'Desmontar Rainbow',
                'categoria': 'montagem',
                'descricao': 'Desmontagem do Rainbow para manutenção',
                'tempo_estimado_minutos': 30,
                'requer_equipamento': True,
                'requer_os': False,
                'pode_ser_recorrente': False,
                'icone': '🔧',
                'cor': '#f39c12',
                'ordem': 31,
            },
            {
                'codigo': 'revisao_geral',
                'nome': 'Revisão Geral',
                'categoria': 'montagem',
                'descricao': 'Revisão completa do equipamento',
                'tempo_estimado_minutos': 90,
                'requer_equipamento': True,
                'requer_os': True,
                'pode_ser_recorrente': False,
                'icone': '🔍',
                'cor': '#f39c12',
                'ordem': 32,
            },
            {
                'codigo': 'teste_funcionamento',
                'nome': 'Teste de Funcionamento',
                'categoria': 'montagem',
                'descricao': 'Testar equipamento após manutenção',
                'tempo_estimado_minutos': 15,
                'requer_equipamento': True,
                'requer_os': False,
                'pode_ser_recorrente': False,
                'icone': '✅',
                'cor': '#f39c12',
                'ordem': 33,
            },

            # ORGANIZAÇÃO
            {
                'codigo': 'organizacao_assistencia',
                'nome': 'Organização da Assistência',
                'categoria': 'organizacao',
                'descricao': 'Organizar e limpar área da assistência técnica',
                'tempo_estimado_minutos': 20,
                'requer_equipamento': False,
                'requer_os': False,
                'pode_ser_recorrente': True,
                'icone': '🧹',
                'cor': '#27ae60',
                'ordem': 40,
            },
            {
                'codigo': 'organizacao_escritorio',
                'nome': 'Organização do Escritório',
                'categoria': 'organizacao',
                'descricao': 'Organizar e limpar área do escritório',
                'tempo_estimado_minutos': 15,
                'requer_equipamento': False,
                'requer_os': False,
                'pode_ser_recorrente': True,
                'icone': '🗂️',
                'cor': '#27ae60',
                'ordem': 41,
            },
            {
                'codigo': 'organizacao_estoque',
                'nome': 'Organização do Estoque',
                'categoria': 'organizacao',
                'descricao': 'Organizar peças e materiais no estoque',
                'tempo_estimado_minutos': 30,
                'requer_equipamento': False,
                'requer_os': False,
                'pode_ser_recorrente': True,
                'icone': '📦',
                'cor': '#27ae60',
                'ordem': 42,
            },

            # OUTROS
            {
                'codigo': 'preparar_entrega',
                'nome': 'Preparar para Entrega',
                'categoria': 'outros',
                'descricao': 'Preparar equipamento para entrega ao cliente',
                'tempo_estimado_minutos': 15,
                'requer_equipamento': True,
                'requer_os': False,
                'pode_ser_recorrente': False,
                'icone': '📦',
                'cor': '#95a5a6',
                'ordem': 50,
            },
            {
                'codigo': 'embalar_equipamento',
                'nome': 'Embalar Equipamento',
                'categoria': 'outros',
                'descricao': 'Embalar equipamento para transporte',
                'tempo_estimado_minutos': 20,
                'requer_equipamento': True,
                'requer_os': False,
                'pode_ser_recorrente': False,
                'icone': '🎁',
                'cor': '#95a5a6',
                'ordem': 51,
            },
        ]

        criados = 0
        atualizados = 0

        for tipo_data in tipos_tarefa:
            codigo = tipo_data.pop('codigo')
            obj, created = TipoTarefaTecnica.objects.update_or_create(
                codigo=codigo,
                defaults=tipo_data
            )
            # Restaurar codigo para exibição
            tipo_data['codigo'] = codigo

            if created:
                criados += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ Criado: {obj.icone} {obj.nome}")
                )
            else:
                atualizados += 1
                self.stdout.write(
                    self.style.WARNING(f"  🔄 Atualizado: {obj.icone} {obj.nome}")
                )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f"✅ Tipos de tarefa: {criados} criados, {atualizados} atualizados")
        )
