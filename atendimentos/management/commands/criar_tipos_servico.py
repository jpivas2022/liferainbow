"""
=============================================================================
LIFE RAINBOW 2.0 - Criar Tipos de Serviço Iniciais
Popula os 7 tipos de serviço e seus campos configuráveis
=============================================================================
"""

from django.core.management.base import BaseCommand
from atendimentos.models import TipoServico, CampoServico


class Command(BaseCommand):
    help = 'Cria os tipos de serviço iniciais e seus campos'

    def handle(self, *args, **options):
        self.stdout.write('Criando tipos de serviço...\n')

        # =================================================================
        # 1. PÓS-VENDA
        # =================================================================
        pos_venda, created = TipoServico.objects.get_or_create(
            codigo='pos_venda',
            defaults={
                'nome': 'Pós-Venda',
                'categoria': 'pos_venda',
                'descricao': 'Visita de pós-venda para cliente que comprou Rainbow',
                'cor': '#27ae60',
                'icone': 'check_circle',
                'ordem': 1,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Criado: {pos_venda.nome}'))
            self._criar_campos_pos_venda(pos_venda)
        else:
            self.stdout.write(f'  → Já existe: {pos_venda.nome}')

        # =================================================================
        # 2. RETORNO PÓS-VENDA
        # =================================================================
        retorno_pos_venda, created = TipoServico.objects.get_or_create(
            codigo='retorno_pos_venda',
            defaults={
                'nome': 'Retorno Pós-Venda',
                'categoria': 'pos_venda',
                'descricao': 'Retorno para buscar Rainbow que estava emprestada durante pós-venda',
                'cor': '#f39c12',
                'icone': 'refresh',
                'ordem': 2,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Criado: {retorno_pos_venda.nome}'))
            self._criar_campos_retorno_pos_venda(retorno_pos_venda)
        else:
            self.stdout.write(f'  → Já existe: {retorno_pos_venda.nome}')

        # =================================================================
        # 3. ALUGUEL PLANO
        # =================================================================
        aluguel_plano, created = TipoServico.objects.get_or_create(
            codigo='aluguel_plano',
            defaults={
                'nome': 'Aluguel Plano',
                'categoria': 'aluguel',
                'descricao': 'Entrega de Rainbow para aluguel mensal com contrato',
                'cor': '#3498db',
                'icone': 'calendar_today',
                'ordem': 3,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Criado: {aluguel_plano.nome}'))
            self._criar_campos_aluguel_plano(aluguel_plano)
        else:
            self.stdout.write(f'  → Já existe: {aluguel_plano.nome}')

        # =================================================================
        # 4. RETORNO ALUGUEL PLANO
        # =================================================================
        retorno_aluguel_plano, created = TipoServico.objects.get_or_create(
            codigo='retorno_aluguel_plano',
            defaults={
                'nome': 'Retorno Aluguel Plano',
                'categoria': 'aluguel',
                'descricao': 'Recolher Rainbow de aluguel mensal e receber pagamento',
                'cor': '#9b59b6',
                'icone': 'assignment_return',
                'ordem': 4,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Criado: {retorno_aluguel_plano.nome}'))
            self._criar_campos_retorno_aluguel_plano(retorno_aluguel_plano)
        else:
            self.stdout.write(f'  → Já existe: {retorno_aluguel_plano.nome}')

        # =================================================================
        # 5. ALUGUEL AVULSO
        # =================================================================
        aluguel_avulso, created = TipoServico.objects.get_or_create(
            codigo='aluguel_avulso',
            defaults={
                'nome': 'Aluguel Avulso',
                'categoria': 'aluguel',
                'descricao': 'Aluguel pontual da Rainbow (não mensal)',
                'cor': '#1abc9c',
                'icone': 'event_available',
                'ordem': 5,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Criado: {aluguel_avulso.nome}'))
            self._criar_campos_aluguel_avulso(aluguel_avulso)
        else:
            self.stdout.write(f'  → Já existe: {aluguel_avulso.nome}')

        # =================================================================
        # 6. RECOLHER ALUGUEL AVULSO
        # =================================================================
        recolher_avulso, created = TipoServico.objects.get_or_create(
            codigo='recolher_aluguel_avulso',
            defaults={
                'nome': 'Recolher Aluguel Avulso',
                'categoria': 'aluguel',
                'descricao': 'Recolher Rainbow de aluguel avulso e finalizar contrato',
                'cor': '#e74c3c',
                'icone': 'assignment_returned',
                'ordem': 6,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Criado: {recolher_avulso.nome}'))
            self._criar_campos_recolher_avulso(recolher_avulso)
        else:
            self.stdout.write(f'  → Já existe: {recolher_avulso.nome}')

        # =================================================================
        # 7. VISITA GERAL
        # =================================================================
        visita_geral, created = TipoServico.objects.get_or_create(
            codigo='visita_geral',
            defaults={
                'nome': 'Visita Geral',
                'categoria': 'visita',
                'descricao': 'Visita para entrega de produtos, cobranças, treinamentos ou resolver problemas',
                'cor': '#34495e',
                'icone': 'home',
                'ordem': 7,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Criado: {visita_geral.nome}'))
            self._criar_campos_visita_geral(visita_geral)
        else:
            self.stdout.write(f'  → Já existe: {visita_geral.nome}')

        # Resumo
        total = TipoServico.objects.count()
        total_campos = CampoServico.objects.count()
        self.stdout.write(self.style.SUCCESS(f'\n✅ Total: {total} tipos de serviço, {total_campos} campos'))

    # =====================================================================
    # CAMPOS POR TIPO DE SERVIÇO
    # =====================================================================

    def _criar_campos_pos_venda(self, tipo):
        """Campos para Pós-Venda"""
        campos = [
            # Seção: Fotos
            {'codigo': 'foto_ficha', 'nome': 'Foto da Ficha', 'tipo_campo': 'foto', 'secao': 'Fotos', 'ordem': 1},
            {'codigo': 'foto_equipamento', 'nome': 'Foto do Equipamento com Peças', 'tipo_campo': 'foto', 'secao': 'Fotos', 'ordem': 2},
            # Seção: Avaliação
            {'codigo': 'satisfacao', 'nome': 'Satisfação do Cliente', 'tipo_campo': 'select', 'secao': 'Avaliação', 'ordem': 3,
             'opcoes': ['Muito Satisfeito', 'Satisfeito', 'Neutro', 'Insatisfeito', 'Muito Insatisfeito']},
            # Seção: Relatório
            {'codigo': 'relatorio_geral', 'nome': 'Relatório Geral', 'tipo_campo': 'textarea', 'secao': 'Relatório', 'ordem': 4},
        ]
        self._criar_campos(tipo, campos)

    def _criar_campos_retorno_pos_venda(self, tipo):
        """Campos para Retorno Pós-Venda"""
        campos = [
            # Seção: Fotos
            {'codigo': 'foto_ficha', 'nome': 'Foto da Ficha', 'tipo_campo': 'foto', 'secao': 'Fotos', 'ordem': 1},
            {'codigo': 'foto_equipamento', 'nome': 'Foto do Equipamento', 'tipo_campo': 'foto', 'secao': 'Fotos', 'ordem': 2},
            # Seção: Equipamento
            {'codigo': 'rainbow_retornada', 'nome': 'Rainbow Retornada?', 'tipo_campo': 'boolean', 'secao': 'Equipamento', 'ordem': 3},
            {'codigo': 'numero_serie', 'nome': 'Número de Série', 'tipo_campo': 'texto', 'secao': 'Equipamento', 'ordem': 4},
            # Seção: Pagamento
            {'codigo': 'pagamento_realizado', 'nome': 'Pagamento Realizado?', 'tipo_campo': 'boolean', 'secao': 'Pagamento', 'ordem': 5},
            {'codigo': 'valor_pagamento', 'nome': 'Valor do Pagamento', 'tipo_campo': 'decimal', 'secao': 'Pagamento', 'ordem': 6},
            {'codigo': 'forma_pagamento', 'nome': 'Forma de Pagamento', 'tipo_campo': 'select', 'secao': 'Pagamento', 'ordem': 7,
             'opcoes': ['Dinheiro', 'PIX', 'Cartão Débito', 'Cartão Crédito', 'Boleto', 'Transferência']},
        ]
        self._criar_campos(tipo, campos)

    def _criar_campos_aluguel_plano(self, tipo):
        """Campos para Aluguel Plano"""
        campos = [
            # Seção: Fotos
            {'codigo': 'foto_rainbow_montada', 'nome': 'Foto Rainbow Montada', 'tipo_campo': 'foto', 'secao': 'Fotos', 'ordem': 1},
            # Seção: Equipamento
            {'codigo': 'numero_rainbow', 'nome': 'Número da Rainbow', 'tipo_campo': 'texto', 'secao': 'Equipamento', 'ordem': 2},
            {'codigo': 'possui_power', 'nome': 'Possui Power?', 'tipo_campo': 'boolean', 'secao': 'Equipamento', 'ordem': 3},
            {'codigo': 'numero_power', 'nome': 'Número do Power', 'tipo_campo': 'texto', 'secao': 'Equipamento', 'ordem': 4},
            # Seção: Uso
            {'codigo': 'discos_usados', 'nome': 'Discos Usados', 'tipo_campo': 'numero', 'secao': 'Uso', 'ordem': 5},
            # Seção: Relatório
            {'codigo': 'relatorio', 'nome': 'Relatório', 'tipo_campo': 'textarea', 'secao': 'Relatório', 'ordem': 6},
        ]
        self._criar_campos(tipo, campos)

    def _criar_campos_retorno_aluguel_plano(self, tipo):
        """Campos para Retorno Aluguel Plano"""
        campos = [
            # Seção: Equipamento
            {'codigo': 'rainbow_recolhida', 'nome': 'Rainbow Recolhida?', 'tipo_campo': 'boolean', 'secao': 'Equipamento', 'ordem': 1},
            {'codigo': 'estado_equipamento', 'nome': 'Estado do Equipamento', 'tipo_campo': 'select', 'secao': 'Equipamento', 'ordem': 2,
             'opcoes': ['Excelente', 'Bom', 'Regular', 'Necessita Manutenção', 'Danificado']},
            # Seção: Contrato
            {'codigo': 'contrato_finalizado', 'nome': 'Contrato Finalizado?', 'tipo_campo': 'boolean', 'secao': 'Contrato', 'ordem': 3},
            # Seção: Pagamento
            {'codigo': 'pagamento_pendente', 'nome': 'Há Pagamento Pendente?', 'tipo_campo': 'boolean', 'secao': 'Pagamento', 'ordem': 4},
            {'codigo': 'valor_recebido', 'nome': 'Valor Recebido', 'tipo_campo': 'decimal', 'secao': 'Pagamento', 'ordem': 5},
            {'codigo': 'forma_pagamento', 'nome': 'Forma de Pagamento', 'tipo_campo': 'select', 'secao': 'Pagamento', 'ordem': 6,
             'opcoes': ['Dinheiro', 'PIX', 'Cartão Débito', 'Cartão Crédito', 'Boleto', 'Transferência']},
        ]
        self._criar_campos(tipo, campos)

    def _criar_campos_aluguel_avulso(self, tipo):
        """Campos para Aluguel Avulso"""
        campos = [
            # Seção: Fotos
            {'codigo': 'foto_rainbow', 'nome': 'Foto da Rainbow', 'tipo_campo': 'foto', 'secao': 'Fotos', 'ordem': 1},
            {'codigo': 'foto_contrato', 'nome': 'Foto do Contrato', 'tipo_campo': 'foto', 'secao': 'Fotos', 'ordem': 2},
            # Seção: Equipamento
            {'codigo': 'numero_rainbow', 'nome': 'Número da Rainbow', 'tipo_campo': 'texto', 'secao': 'Equipamento', 'ordem': 3},
            {'codigo': 'possui_power', 'nome': 'Possui Power?', 'tipo_campo': 'boolean', 'secao': 'Equipamento', 'ordem': 4},
            {'codigo': 'numero_power', 'nome': 'Número do Power', 'tipo_campo': 'texto', 'secao': 'Equipamento', 'ordem': 5},
            # Seção: Uso
            {'codigo': 'discos_entregues', 'nome': 'Discos Entregues', 'tipo_campo': 'numero', 'secao': 'Uso', 'ordem': 6},
            # Seção: Pagamento
            {'codigo': 'valor_aluguel', 'nome': 'Valor do Aluguel', 'tipo_campo': 'decimal', 'secao': 'Pagamento', 'ordem': 7},
            {'codigo': 'pagamento_adiantado', 'nome': 'Pagamento Adiantado?', 'tipo_campo': 'boolean', 'secao': 'Pagamento', 'ordem': 8},
            {'codigo': 'forma_pagamento', 'nome': 'Forma de Pagamento', 'tipo_campo': 'select', 'secao': 'Pagamento', 'ordem': 9,
             'opcoes': ['Dinheiro', 'PIX', 'Cartão Débito', 'Cartão Crédito', 'Boleto', 'Transferência']},
            # Seção: Relatório
            {'codigo': 'relatorio', 'nome': 'Relatório', 'tipo_campo': 'textarea', 'secao': 'Relatório', 'ordem': 10},
        ]
        self._criar_campos(tipo, campos)

    def _criar_campos_recolher_avulso(self, tipo):
        """Campos para Recolher Aluguel Avulso"""
        campos = [
            # Seção: Equipamento
            {'codigo': 'rainbow_recolhida', 'nome': 'Rainbow Recolhida?', 'tipo_campo': 'boolean', 'secao': 'Equipamento', 'ordem': 1},
            {'codigo': 'estado_equipamento', 'nome': 'Estado do Equipamento', 'tipo_campo': 'select', 'secao': 'Equipamento', 'ordem': 2,
             'opcoes': ['Excelente', 'Bom', 'Regular', 'Necessita Manutenção', 'Danificado']},
            # Seção: Contrato
            {'codigo': 'contrato_conferido', 'nome': 'Contrato Conferido?', 'tipo_campo': 'boolean', 'secao': 'Contrato', 'ordem': 3},
            # Seção: Pagamento
            {'codigo': 'pagamento_final', 'nome': 'Pagamento Final Realizado?', 'tipo_campo': 'boolean', 'secao': 'Pagamento', 'ordem': 4},
            {'codigo': 'valor_final', 'nome': 'Valor Final', 'tipo_campo': 'decimal', 'secao': 'Pagamento', 'ordem': 5},
            {'codigo': 'forma_pagamento', 'nome': 'Forma de Pagamento', 'tipo_campo': 'select', 'secao': 'Pagamento', 'ordem': 6,
             'opcoes': ['Dinheiro', 'PIX', 'Cartão Débito', 'Cartão Crédito', 'Boleto', 'Transferência']},
        ]
        self._criar_campos(tipo, campos)

    def _criar_campos_visita_geral(self, tipo):
        """Campos para Visita Geral"""
        campos = [
            # Seção: Motivo
            {'codigo': 'motivo_visita', 'nome': 'Motivo da Visita', 'tipo_campo': 'multiselect', 'secao': 'Motivo', 'ordem': 1,
             'opcoes': ['Entrega de Produtos', 'Cobrança', 'Treinamento', 'Resolver Problema', 'Manutenção', 'Outro']},
            # Seção: Produtos
            {'codigo': 'produtos_entregues', 'nome': 'Produtos Entregues', 'tipo_campo': 'textarea', 'secao': 'Produtos', 'ordem': 2},
            # Seção: Cobrança
            {'codigo': 'cobranca_realizada', 'nome': 'Cobrança Realizada?', 'tipo_campo': 'boolean', 'secao': 'Cobrança', 'ordem': 3},
            {'codigo': 'valor_cobrado', 'nome': 'Valor Cobrado', 'tipo_campo': 'decimal', 'secao': 'Cobrança', 'ordem': 4},
            {'codigo': 'forma_pagamento', 'nome': 'Forma de Pagamento', 'tipo_campo': 'select', 'secao': 'Cobrança', 'ordem': 5,
             'opcoes': ['Dinheiro', 'PIX', 'Cartão Débito', 'Cartão Crédito', 'Boleto', 'Transferência', 'Não Pagou']},
            # Seção: Treinamento
            {'codigo': 'treinamento_realizado', 'nome': 'Treinamento Realizado?', 'tipo_campo': 'boolean', 'secao': 'Treinamento', 'ordem': 6},
            {'codigo': 'tipo_treinamento', 'nome': 'Tipo de Treinamento', 'tipo_campo': 'texto', 'secao': 'Treinamento', 'ordem': 7},
            # Seção: Problema
            {'codigo': 'problema_identificado', 'nome': 'Problema Identificado?', 'tipo_campo': 'boolean', 'secao': 'Problema', 'ordem': 8},
            {'codigo': 'descricao_problema', 'nome': 'Descrição do Problema', 'tipo_campo': 'textarea', 'secao': 'Problema', 'ordem': 9},
            {'codigo': 'problema_resolvido', 'nome': 'Problema Resolvido?', 'tipo_campo': 'boolean', 'secao': 'Problema', 'ordem': 10},
            # Seção: Relatório
            {'codigo': 'relatorio_geral', 'nome': 'Relatório Geral', 'tipo_campo': 'textarea', 'secao': 'Relatório', 'ordem': 11},
        ]
        self._criar_campos(tipo, campos)

    def _criar_campos(self, tipo_servico, campos):
        """Cria os campos para um tipo de serviço"""
        for campo_data in campos:
            opcoes = campo_data.pop('opcoes', [])
            CampoServico.objects.get_or_create(
                tipo_servico=tipo_servico,
                codigo=campo_data['codigo'],
                defaults={
                    **campo_data,
                    'opcoes': opcoes,
                    'obrigatorio': False,  # Todos opcionais por padrão
                }
            )
