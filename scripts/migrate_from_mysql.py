#!/usr/bin/env python
"""
=============================================================================
LIFE RAINBOW 2.0 - Script de Migração do MySQL para PostgreSQL
Migra dados do sistema PHP/MySQL antigo para o novo sistema Django/PostgreSQL
=============================================================================

USO:
    python scripts/migrate_from_mysql.py --mysql-host=localhost --mysql-db=lfrainbo_life

REQUISITOS:
    - MySQL Connector: pip install mysql-connector-python
    - Django configurado e migrações aplicadas
    - Acesso ao banco MySQL de origem

ESTRUTURA MIGRADA:
    - clientes → Cliente, Endereco
    - produtos → Produto
    - equipamentos → ModeloEquipamento, Equipamento
    - vendas → Venda, ItemVenda, Parcela
    - alugueis → ContratoAluguel, ParcelaAluguel (NORMALIZADO!)
    - agenda → Agendamento
    - ordens_servico → OrdemServico
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

import mysql.connector
from django.contrib.auth.models import User
from django.utils import timezone

# Imports dos modelos
from clientes.models import Cliente, Endereco
from equipamentos.models import ModeloEquipamento, Equipamento
from vendas.models import Venda, ItemVenda, Parcela
from alugueis.models import ContratoAluguel, ParcelaAluguel
from financeiro.models import PlanoConta, ContaReceber, ContaPagar
from agenda.models import Agendamento
from assistencia.models import OrdemServico
from estoque.models import Produto

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MySQLMigrator:
    """Classe principal para migração do MySQL para PostgreSQL."""

    def __init__(self, mysql_config: dict, dry_run: bool = False):
        self.mysql_config = mysql_config
        self.dry_run = dry_run
        self.connection = None
        self.stats = {
            'clientes': {'total': 0, 'migrated': 0, 'errors': 0},
            'equipamentos': {'total': 0, 'migrated': 0, 'errors': 0},
            'vendas': {'total': 0, 'migrated': 0, 'errors': 0},
            'alugueis': {'total': 0, 'migrated': 0, 'errors': 0},
            'agenda': {'total': 0, 'migrated': 0, 'errors': 0},
        }
        # Mapeamento de IDs antigos para novos
        self.id_map = {
            'clientes': {},
            'equipamentos': {},
            'vendas': {},
            'alugueis': {},
        }

    def connect(self):
        """Conecta ao banco MySQL."""
        try:
            self.connection = mysql.connector.connect(**self.mysql_config)
            logger.info(f"✅ Conectado ao MySQL: {self.mysql_config['database']}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao MySQL: {e}")
            return False

    def disconnect(self):
        """Desconecta do MySQL."""
        if self.connection:
            self.connection.close()
            logger.info("🔌 Desconectado do MySQL")

    def execute_query(self, query: str) -> list:
        """Executa query e retorna resultados como lista de dicts."""
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results

    def safe_decimal(self, value, default=Decimal('0')):
        """Converte valor para Decimal de forma segura."""
        if value is None:
            return default
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return default

    def safe_date(self, value):
        """Converte valor para date de forma segura."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                return None
        return value

    def safe_datetime(self, value):
        """Converte valor para datetime timezone-aware."""
        if value is None:
            return None
        if isinstance(value, datetime):
            if timezone.is_naive(value):
                return timezone.make_aware(value)
            return value
        if isinstance(value, str):
            try:
                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                return timezone.make_aware(dt)
            except ValueError:
                return None
        return None

    # =========================================================================
    # MIGRAÇÃO DE CLIENTES
    # =========================================================================

    def migrate_clientes(self):
        """Migra tabela de clientes."""
        logger.info("📋 Iniciando migração de CLIENTES...")

        query = """
        SELECT
            id, nome, email, telefone, telefone_secundario, whatsapp,
            cpf, data_nascimento, profissao,
            endereco, numero, complemento, bairro, cidade, estado, cep,
            origem, observacoes, data_cadastro, ultimo_contato,
            possui_rainbow, modelo_rainbow, data_compra_rainbow,
            perfil, status
        FROM clientes
        ORDER BY id
        """

        try:
            rows = self.execute_query(query)
            self.stats['clientes']['total'] = len(rows)
            logger.info(f"   Encontrados {len(rows)} clientes")

            for row in rows:
                try:
                    if self.dry_run:
                        logger.info(f"   [DRY RUN] Cliente: {row['nome']}")
                        self.stats['clientes']['migrated'] += 1
                        continue

                    # Criar cliente
                    cliente = Cliente.objects.create(
                        nome=row['nome'] or 'Sem Nome',
                        email=row['email'] or '',
                        telefone=row['telefone'] or '',
                        telefone_secundario=row['telefone_secundario'] or '',
                        whatsapp=row['whatsapp'] or row['telefone'] or '',
                        cpf=row['cpf'] or '',
                        data_nascimento=self.safe_date(row.get('data_nascimento')),
                        profissao=row.get('profissao', ''),
                        cidade=row.get('cidade', ''),
                        estado=row.get('estado', ''),
                        origem=self._map_origem(row.get('origem')),
                        observacoes=row.get('observacoes', ''),
                        possui_rainbow=bool(row.get('possui_rainbow')),
                        modelo_rainbow=row.get('modelo_rainbow', ''),
                        data_compra_rainbow=self.safe_date(row.get('data_compra_rainbow')),
                        perfil=self._map_perfil(row.get('perfil')),
                        status=self._map_status_cliente(row.get('status')),
                    )

                    # Criar endereço se existir
                    if row.get('endereco') or row.get('cidade'):
                        Endereco.objects.create(
                            cliente=cliente,
                            tipo='residencial',
                            logradouro=row.get('endereco', ''),
                            numero=row.get('numero', ''),
                            complemento=row.get('complemento', ''),
                            bairro=row.get('bairro', ''),
                            cidade=row.get('cidade', ''),
                            estado=row.get('estado', ''),
                            cep=row.get('cep', ''),
                            principal=True,
                        )

                    # Guardar mapeamento
                    self.id_map['clientes'][row['id']] = cliente.id
                    self.stats['clientes']['migrated'] += 1

                except Exception as e:
                    logger.error(f"   ❌ Erro ao migrar cliente {row.get('id')}: {e}")
                    self.stats['clientes']['errors'] += 1

        except Exception as e:
            logger.error(f"❌ Erro ao buscar clientes: {e}")

        self._print_stats('clientes')

    def _map_origem(self, origem):
        """Mapeia origem do cliente."""
        mapa = {
            'indicacao': 'indicacao',
            'internet': 'internet',
            'evento': 'evento',
            'telefone': 'telefone',
        }
        return mapa.get(origem, 'outro')

    def _map_perfil(self, perfil):
        """Mapeia perfil do cliente."""
        mapa = {
            'diamante': 'diamante',
            'ouro': 'ouro',
            'prata': 'prata',
            'bronze': 'bronze',
        }
        return mapa.get(perfil, 'standard')

    def _map_status_cliente(self, status):
        """Mapeia status do cliente."""
        mapa = {
            'ativo': 'ativo',
            'inativo': 'inativo',
            'prospecto': 'prospecto',
        }
        return mapa.get(status, 'ativo')

    # =========================================================================
    # MIGRAÇÃO DE ALUGUÉIS (NORMALIZAÇÃO!)
    # =========================================================================

    def migrate_alugueis(self):
        """
        Migra tabela de aluguéis com NORMALIZAÇÃO.

        ANTES (MySQL):
            um_aluguel, dois_aluguel, ..., aluguel_doze (12 colunas!)

        DEPOIS (PostgreSQL):
            ContratoAluguel + ParcelaAluguel (estrutura normalizada)
        """
        logger.info("📋 Iniciando migração de ALUGUÉIS (com normalização)...")

        query = """
        SELECT
            id, cliente_id, data_inicio, duracao_meses, valor_mensal, caucao,
            equipamento_serie, endereco_entrega, status, observacoes,
            um_aluguel, dois_aluguel, tres_aluguel, quatro_aluguel,
            cinco_aluguel, seis_aluguel, sete_aluguel, oito_aluguel,
            nove_aluguel, dez_aluguel, onze_aluguel, aluguel_doze
        FROM alugueis
        ORDER BY id
        """

        try:
            rows = self.execute_query(query)
            self.stats['alugueis']['total'] = len(rows)
            logger.info(f"   Encontrados {len(rows)} contratos de aluguel")

            for row in rows:
                try:
                    if self.dry_run:
                        logger.info(f"   [DRY RUN] Aluguel ID: {row['id']}")
                        self.stats['alugueis']['migrated'] += 1
                        continue

                    # Buscar cliente migrado
                    cliente_id = self.id_map['clientes'].get(row['cliente_id'])
                    if not cliente_id:
                        logger.warning(f"   ⚠️ Cliente {row['cliente_id']} não encontrado, pulando aluguel")
                        continue

                    cliente = Cliente.objects.get(id=cliente_id)

                    # Criar contrato
                    contrato = ContratoAluguel.objects.create(
                        cliente=cliente,
                        data_inicio=self.safe_date(row['data_inicio']) or timezone.now().date(),
                        duracao_meses=row.get('duracao_meses', 12),
                        valor_mensal=self.safe_decimal(row.get('valor_mensal')),
                        caucao=self.safe_decimal(row.get('caucao')),
                        endereco_entrega=row.get('endereco_entrega', ''),
                        status=self._map_status_aluguel(row.get('status')),
                        observacoes=row.get('observacoes', ''),
                    )

                    # NORMALIZAÇÃO: Converter colunas um_aluguel...aluguel_doze em ParcelaAluguel
                    parcelas_colunas = [
                        'um_aluguel', 'dois_aluguel', 'tres_aluguel', 'quatro_aluguel',
                        'cinco_aluguel', 'seis_aluguel', 'sete_aluguel', 'oito_aluguel',
                        'nove_aluguel', 'dez_aluguel', 'onze_aluguel', 'aluguel_doze'
                    ]

                    for i, coluna in enumerate(parcelas_colunas, 1):
                        valor_parcela = row.get(coluna)
                        if valor_parcela is not None:
                            # Calcular data de vencimento
                            data_inicio = self.safe_date(row['data_inicio']) or timezone.now().date()
                            data_vencimento = data_inicio + timedelta(days=(i - 1) * 30)

                            # Determinar status da parcela
                            status_parcela = 'pago' if float(valor_parcela or 0) > 0 else 'pendente'

                            ParcelaAluguel.objects.create(
                                contrato=contrato,
                                numero=i,
                                valor=contrato.valor_mensal,
                                data_vencimento=data_vencimento,
                                valor_pago=self.safe_decimal(valor_parcela) if status_parcela == 'pago' else None,
                                data_pagamento=data_vencimento if status_parcela == 'pago' else None,
                                status=status_parcela,
                            )

                    self.id_map['alugueis'][row['id']] = contrato.id
                    self.stats['alugueis']['migrated'] += 1

                except Exception as e:
                    logger.error(f"   ❌ Erro ao migrar aluguel {row.get('id')}: {e}")
                    self.stats['alugueis']['errors'] += 1

        except Exception as e:
            logger.error(f"❌ Erro ao buscar aluguéis: {e}")

        self._print_stats('alugueis')

    def _map_status_aluguel(self, status):
        """Mapeia status do aluguel."""
        mapa = {
            'ativo': 'ativo',
            'finalizado': 'finalizado',
            'cancelado': 'cancelado',
        }
        return mapa.get(status, 'ativo')

    # =========================================================================
    # MIGRAÇÃO DE VENDAS
    # =========================================================================

    def migrate_vendas(self):
        """Migra tabela de vendas."""
        logger.info("📋 Iniciando migração de VENDAS...")

        query = """
        SELECT
            id, cliente_id, consultor_id, data_venda, tipo_venda,
            valor_produtos, valor_servicos, desconto, valor_total,
            forma_pagamento, parcelas, status, observacoes
        FROM vendas
        ORDER BY id
        """

        try:
            rows = self.execute_query(query)
            self.stats['vendas']['total'] = len(rows)
            logger.info(f"   Encontradas {len(rows)} vendas")

            for row in rows:
                try:
                    if self.dry_run:
                        logger.info(f"   [DRY RUN] Venda ID: {row['id']}")
                        self.stats['vendas']['migrated'] += 1
                        continue

                    # Buscar cliente migrado
                    cliente_id = self.id_map['clientes'].get(row['cliente_id'])
                    if not cliente_id:
                        logger.warning(f"   ⚠️ Cliente {row['cliente_id']} não encontrado, pulando venda")
                        continue

                    cliente = Cliente.objects.get(id=cliente_id)

                    # Criar venda
                    venda = Venda.objects.create(
                        cliente=cliente,
                        data_venda=self.safe_datetime(row['data_venda']) or timezone.now(),
                        tipo_venda=self._map_tipo_venda(row.get('tipo_venda')),
                        valor_produtos=self.safe_decimal(row.get('valor_produtos')),
                        valor_servicos=self.safe_decimal(row.get('valor_servicos')),
                        desconto=self.safe_decimal(row.get('desconto')),
                        valor_total=self.safe_decimal(row.get('valor_total')),
                        forma_pagamento=self._map_forma_pagamento(row.get('forma_pagamento')),
                        parcelas_total=row.get('parcelas', 1),
                        status=self._map_status_venda(row.get('status')),
                        observacoes=row.get('observacoes', ''),
                    )

                    self.id_map['vendas'][row['id']] = venda.id
                    self.stats['vendas']['migrated'] += 1

                except Exception as e:
                    logger.error(f"   ❌ Erro ao migrar venda {row.get('id')}: {e}")
                    self.stats['vendas']['errors'] += 1

        except Exception as e:
            logger.error(f"❌ Erro ao buscar vendas: {e}")

        self._print_stats('vendas')

    def _map_tipo_venda(self, tipo):
        """Mapeia tipo de venda."""
        mapa = {
            'rainbow': 'rainbow',
            'acessorio': 'acessorio',
            'servico': 'servico',
        }
        return mapa.get(tipo, 'rainbow')

    def _map_forma_pagamento(self, forma):
        """Mapeia forma de pagamento."""
        mapa = {
            'pix': 'pix',
            'cartao': 'cartao_credito',
            'cartao_credito': 'cartao_credito',
            'cartao_debito': 'cartao_debito',
            'boleto': 'boleto',
            'dinheiro': 'dinheiro',
            'transferencia': 'transferencia',
        }
        return mapa.get(forma, 'dinheiro')

    def _map_status_venda(self, status):
        """Mapeia status da venda."""
        mapa = {
            'orcamento': 'orcamento',
            'pendente': 'pendente',
            'aprovada': 'aprovada',
            'finalizada': 'finalizada',
            'cancelada': 'cancelada',
        }
        return mapa.get(status, 'pendente')

    # =========================================================================
    # UTILITÁRIOS
    # =========================================================================

    def _print_stats(self, entity):
        """Imprime estatísticas de migração."""
        s = self.stats[entity]
        logger.info(f"   ✅ {entity.upper()}: {s['migrated']}/{s['total']} migrados, {s['errors']} erros")

    def run_full_migration(self):
        """Executa migração completa."""
        logger.info("=" * 60)
        logger.info("🚀 LIFE RAINBOW 2.0 - MIGRAÇÃO DE DADOS")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("⚠️  MODO DRY RUN - Nenhum dado será alterado")

        if not self.connect():
            return False

        try:
            # Ordem importante para manter integridade referencial
            self.migrate_clientes()
            self.migrate_alugueis()
            self.migrate_vendas()

            logger.info("=" * 60)
            logger.info("📊 RESUMO DA MIGRAÇÃO")
            logger.info("=" * 60)
            for entity, stats in self.stats.items():
                logger.info(f"   {entity.upper()}: {stats['migrated']}/{stats['total']} ✅, {stats['errors']} ❌")

            return True

        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(description='Migração MySQL → PostgreSQL Life Rainbow')
    parser.add_argument('--mysql-host', default='localhost', help='Host do MySQL')
    parser.add_argument('--mysql-port', type=int, default=3306, help='Porta do MySQL')
    parser.add_argument('--mysql-user', default='root', help='Usuário do MySQL')
    parser.add_argument('--mysql-password', default='', help='Senha do MySQL')
    parser.add_argument('--mysql-db', default='lfrainbo_life', help='Database do MySQL')
    parser.add_argument('--dry-run', action='store_true', help='Simular migração sem alterar dados')

    args = parser.parse_args()

    mysql_config = {
        'host': args.mysql_host,
        'port': args.mysql_port,
        'user': args.mysql_user,
        'password': args.mysql_password,
        'database': args.mysql_db,
    }

    migrator = MySQLMigrator(mysql_config, dry_run=args.dry_run)
    success = migrator.run_full_migration()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
