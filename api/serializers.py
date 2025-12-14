"""
=============================================================================
LIFE RAINBOW 2.0 - Serializers para API REST
Serializers para todos os módulos do sistema
=============================================================================
"""

from rest_framework import serializers
from django.contrib.auth.models import User

# Imports dos modelos
from clientes.models import Cliente, Endereco, HistoricoInteracao
from equipamentos.models import ModeloEquipamento, Equipamento, HistoricoManutencao
from vendas.models import Venda, ItemVenda, Parcela
from alugueis.models import ContratoAluguel, ParcelaAluguel, HistoricoAluguel
from financeiro.models import PlanoConta, ContaReceber, ContaPagar, Caixa, Movimentacao
from agenda.models import Agendamento, FollowUp, Tarefa
from assistencia.models import OrdemServico, ItemOrdemServico
from estoque.models import Produto, MovimentacaoEstoque, Inventario
from whatsapp_integration.models import Conversa, Mensagem, Template, CampanhaMensagem


# =============================================================================
# USUÁRIOS
# =============================================================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer para usuários do sistema."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']
        read_only_fields = ['id']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de usuários."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


# =============================================================================
# CLIENTES
# =============================================================================

class EnderecoSerializer(serializers.ModelSerializer):
    """Serializer para endereços."""

    class Meta:
        model = Endereco
        fields = [
            'id', 'tipo', 'cep', 'logradouro', 'numero', 'complemento',
            'bairro', 'cidade', 'estado', 'principal', 'latitude', 'longitude'
        ]
        read_only_fields = ['id']


class HistoricoInteracaoSerializer(serializers.ModelSerializer):
    """Serializer para histórico de interações."""
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)

    class Meta:
        model = HistoricoInteracao
        fields = [
            'id', 'tipo', 'canal', 'descricao', 'resultado',
            'usuario', 'usuario_nome', 'data_hora', 'proxima_acao', 'data_proxima_acao'
        ]
        read_only_fields = ['id', 'usuario_nome', 'data_hora']


class ClienteListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de clientes."""
    endereco_principal = serializers.SerializerMethodField()
    dias_sem_contato = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cliente
        fields = [
            'id', 'nome', 'telefone', 'email', 'cidade', 'estado',
            'perfil', 'status', 'endereco_principal', 'dias_sem_contato',
            'possui_rainbow', 'ultimo_contato'
        ]

    def get_endereco_principal(self, obj):
        endereco = obj.enderecos.filter(principal=True).first()
        if endereco:
            return f"{endereco.cidade}/{endereco.estado}"
        return None


class ClienteDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes do cliente."""
    enderecos = EnderecoSerializer(many=True, read_only=True)
    historico_interacoes = HistoricoInteracaoSerializer(
        source='historico_interacoes.all',
        many=True,
        read_only=True
    )
    consultor_nome = serializers.CharField(source='consultor.get_full_name', read_only=True)
    indicado_por_nome = serializers.CharField(source='indicado_por.nome', read_only=True)

    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['id', 'data_cadastro', 'atualizado_em']


class ClienteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação/atualização de clientes."""
    enderecos = EnderecoSerializer(many=True, required=False)

    class Meta:
        model = Cliente
        exclude = ['data_cadastro', 'atualizado_em']

    def create(self, validated_data):
        enderecos_data = validated_data.pop('enderecos', [])
        cliente = Cliente.objects.create(**validated_data)
        for endereco_data in enderecos_data:
            Endereco.objects.create(cliente=cliente, **endereco_data)
        return cliente

    def update(self, instance, validated_data):
        enderecos_data = validated_data.pop('enderecos', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if enderecos_data is not None:
            instance.enderecos.all().delete()
            for endereco_data in enderecos_data:
                Endereco.objects.create(cliente=instance, **endereco_data)

        return instance


# =============================================================================
# EQUIPAMENTOS
# =============================================================================

class ModeloEquipamentoSerializer(serializers.ModelSerializer):
    """Serializer para modelos de equipamento."""

    class Meta:
        model = ModeloEquipamento
        fields = '__all__'
        read_only_fields = ['id']


class HistoricoManutencaoSerializer(serializers.ModelSerializer):
    """Serializer para histórico de manutenção."""
    tecnico_nome = serializers.CharField(source='tecnico.get_full_name', read_only=True)

    class Meta:
        model = HistoricoManutencao
        fields = '__all__'
        read_only_fields = ['id']


class EquipamentoListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de equipamentos."""
    modelo_nome = serializers.CharField(source='modelo.nome', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    garantia_status = serializers.SerializerMethodField()

    class Meta:
        model = Equipamento
        fields = [
            'id', 'numero_serie', 'modelo', 'modelo_nome', 'cliente', 'cliente_nome',
            'status', 'data_compra', 'garantia_ate', 'garantia_status'
        ]

    def get_garantia_status(self, obj):
        from django.utils import timezone
        if obj.garantia_ate:
            if obj.garantia_ate >= timezone.now().date():
                return 'ativa'
            return 'expirada'
        return 'sem_garantia'


class EquipamentoDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes do equipamento."""
    modelo = ModeloEquipamentoSerializer(read_only=True)
    historico_manutencao = HistoricoManutencaoSerializer(many=True, read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)

    class Meta:
        model = Equipamento
        fields = '__all__'
        read_only_fields = ['id', 'data_cadastro', 'atualizado_em']


# =============================================================================
# VENDAS
# =============================================================================

class ItemVendaSerializer(serializers.ModelSerializer):
    """Serializer para itens de venda."""
    produto_nome = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ItemVenda
        fields = [
            'id', 'tipo_item', 'equipamento', 'produto', 'produto_nome',
            'descricao', 'quantidade', 'valor_unitario', 'desconto', 'subtotal'
        ]

    def get_produto_nome(self, obj):
        if obj.equipamento:
            return f"Rainbow {obj.equipamento.modelo.nome}"
        elif obj.produto:
            return obj.produto.nome
        return obj.descricao


class ParcelaSerializer(serializers.ModelSerializer):
    """Serializer para parcelas de venda."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Parcela
        fields = [
            'id', 'numero', 'valor', 'data_vencimento', 'data_pagamento',
            'valor_pago', 'forma_pagamento', 'status', 'status_display', 'observacao'
        ]
        read_only_fields = ['id']


class VendaListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de vendas."""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    consultor_nome = serializers.CharField(source='consultor.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Venda
        fields = [
            'id', 'numero', 'cliente', 'cliente_nome', 'consultor', 'consultor_nome',
            'data_venda', 'valor_total', 'status', 'status_display', 'tipo_venda'
        ]


class VendaDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes da venda."""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    consultor_nome = serializers.CharField(source='consultor.get_full_name', read_only=True)
    itens = ItemVendaSerializer(many=True, read_only=True)
    parcelas = ParcelaSerializer(many=True, read_only=True)
    total_pago = serializers.SerializerMethodField()
    saldo_devedor = serializers.SerializerMethodField()

    class Meta:
        model = Venda
        fields = '__all__'
        read_only_fields = ['id', 'numero', 'data_venda', 'atualizado_em']

    def get_total_pago(self, obj):
        return sum(p.valor_pago or 0 for p in obj.parcelas.filter(status='pago'))

    def get_saldo_devedor(self, obj):
        return obj.valor_total - self.get_total_pago(obj)


# =============================================================================
# ALUGUÉIS
# =============================================================================

class ParcelaAluguelSerializer(serializers.ModelSerializer):
    """Serializer para parcelas de aluguel."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ParcelaAluguel
        fields = [
            'id', 'numero', 'valor', 'data_vencimento', 'data_pagamento',
            'valor_pago', 'status', 'status_display', 'observacao'
        ]
        read_only_fields = ['id']


class HistoricoAluguelSerializer(serializers.ModelSerializer):
    """Serializer para histórico de aluguel."""
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)

    class Meta:
        model = HistoricoAluguel
        fields = '__all__'
        read_only_fields = ['id']


class ContratoAluguelListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de contratos."""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    equipamento_serie = serializers.CharField(source='equipamento.numero_serie', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    parcelas_pendentes = serializers.SerializerMethodField()

    class Meta:
        model = ContratoAluguel
        fields = [
            'id', 'numero', 'cliente', 'cliente_nome', 'equipamento', 'equipamento_serie',
            'data_inicio', 'data_fim', 'valor_mensal', 'status', 'status_display',
            'parcelas_pendentes'
        ]

    def get_parcelas_pendentes(self, obj):
        return obj.parcelas.filter(status='pendente').count()


class ContratoAluguelDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes do contrato."""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    equipamento_info = EquipamentoListSerializer(source='equipamento', read_only=True)
    parcelas = ParcelaAluguelSerializer(many=True, read_only=True)
    historico = HistoricoAluguelSerializer(many=True, read_only=True)
    total_pago = serializers.SerializerMethodField()

    class Meta:
        model = ContratoAluguel
        fields = '__all__'
        read_only_fields = ['id', 'numero', 'criado_em', 'atualizado_em']

    def get_total_pago(self, obj):
        return sum(p.valor_pago or 0 for p in obj.parcelas.filter(status='pago'))


# =============================================================================
# FINANCEIRO
# =============================================================================

class PlanoContaSerializer(serializers.ModelSerializer):
    """Serializer para plano de contas."""
    filhos = serializers.SerializerMethodField()

    class Meta:
        model = PlanoConta
        fields = '__all__'
        read_only_fields = ['id']

    def get_filhos(self, obj):
        filhos = obj.filhos.all()
        return PlanoContaSerializer(filhos, many=True).data if filhos else []


class ContaReceberSerializer(serializers.ModelSerializer):
    """Serializer para contas a receber."""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ContaReceber
        fields = '__all__'
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class ContaPagarSerializer(serializers.ModelSerializer):
    """Serializer para contas a pagar."""
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ContaPagar
        fields = '__all__'
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class CaixaSerializer(serializers.ModelSerializer):
    """Serializer para caixas."""
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)

    class Meta:
        model = Caixa
        fields = '__all__'
        read_only_fields = ['id']


class MovimentacaoSerializer(serializers.ModelSerializer):
    """Serializer para movimentações."""
    caixa_nome = serializers.CharField(source='caixa.nome', read_only=True)
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)

    class Meta:
        model = Movimentacao
        fields = '__all__'
        read_only_fields = ['id', 'data_hora', 'saldo_anterior', 'saldo_posterior']


# =============================================================================
# AGENDA
# =============================================================================

class AgendamentoSerializer(serializers.ModelSerializer):
    """Serializer para agendamentos."""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Agendamento
        fields = '__all__'
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class FollowUpSerializer(serializers.ModelSerializer):
    """Serializer para follow-ups."""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)

    class Meta:
        model = FollowUp
        fields = '__all__'
        read_only_fields = ['id', 'criado_em']


class TarefaSerializer(serializers.ModelSerializer):
    """Serializer para tarefas."""
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    criado_por_nome = serializers.CharField(source='criado_por.get_full_name', read_only=True)

    class Meta:
        model = Tarefa
        fields = '__all__'
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


# =============================================================================
# ASSISTÊNCIA TÉCNICA
# =============================================================================

class ItemOrdemServicoSerializer(serializers.ModelSerializer):
    """Serializer para itens de ordem de serviço."""
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)

    class Meta:
        model = ItemOrdemServico
        fields = '__all__'
        read_only_fields = ['id']


class OrdemServicoListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de OS."""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    equipamento_serie = serializers.CharField(source='equipamento.numero_serie', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = OrdemServico
        fields = [
            'id', 'numero', 'cliente', 'cliente_nome', 'equipamento', 'equipamento_serie',
            'tipo_servico', 'data_abertura', 'status', 'status_display', 'valor_total', 'urgente'
        ]


class OrdemServicoDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes da OS."""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    equipamento_info = EquipamentoListSerializer(source='equipamento', read_only=True)
    tecnico_nome = serializers.CharField(source='tecnico.get_full_name', read_only=True)
    itens = ItemOrdemServicoSerializer(many=True, read_only=True)

    class Meta:
        model = OrdemServico
        fields = '__all__'
        read_only_fields = ['id', 'numero', 'data_abertura', 'atualizado_em']


# =============================================================================
# ESTOQUE
# =============================================================================

class ProdutoSerializer(serializers.ModelSerializer):
    """Serializer para produtos."""
    estoque_baixo = serializers.SerializerMethodField()

    class Meta:
        model = Produto
        fields = '__all__'
        read_only_fields = ['id', 'criado_em', 'atualizado_em']

    def get_estoque_baixo(self, obj):
        return obj.quantidade_atual <= obj.estoque_minimo


class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    """Serializer para movimentações de estoque."""
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)

    class Meta:
        model = MovimentacaoEstoque
        fields = '__all__'
        read_only_fields = ['id', 'data_hora']


class InventarioSerializer(serializers.ModelSerializer):
    """Serializer para inventários."""
    realizado_por_nome = serializers.CharField(source='realizado_por.get_full_name', read_only=True)

    class Meta:
        model = Inventario
        fields = '__all__'
        read_only_fields = ['id']


# =============================================================================
# WHATSAPP
# =============================================================================

class MensagemSerializer(serializers.ModelSerializer):
    """Serializer para mensagens WhatsApp."""

    class Meta:
        model = Mensagem
        fields = '__all__'
        read_only_fields = ['id', 'data_hora']


class ConversaSerializer(serializers.ModelSerializer):
    """Serializer para conversas WhatsApp."""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    mensagens_recentes = serializers.SerializerMethodField()

    class Meta:
        model = Conversa
        fields = '__all__'
        read_only_fields = ['id', 'iniciada_em', 'atualizada_em']

    def get_mensagens_recentes(self, obj):
        mensagens = obj.mensagens.order_by('-data_hora')[:20]
        return MensagemSerializer(mensagens, many=True).data


class TemplateSerializer(serializers.ModelSerializer):
    """Serializer para templates WhatsApp."""

    class Meta:
        model = Template
        fields = '__all__'
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class CampanhaMensagemSerializer(serializers.ModelSerializer):
    """Serializer para campanhas WhatsApp."""
    template_nome = serializers.CharField(source='template.nome', read_only=True)
    criado_por_nome = serializers.CharField(source='criado_por.get_full_name', read_only=True)

    class Meta:
        model = CampanhaMensagem
        fields = '__all__'
        read_only_fields = ['id', 'criada_em', 'iniciada_em', 'finalizada_em']


# =============================================================================
# DASHBOARD E RELATÓRIOS
# =============================================================================

class DashboardSerializer(serializers.Serializer):
    """Serializer para dados do dashboard."""
    clientes_total = serializers.IntegerField()
    clientes_ativos = serializers.IntegerField()
    clientes_sem_contato_30d = serializers.IntegerField()
    vendas_mes = serializers.IntegerField()
    vendas_valor_mes = serializers.DecimalField(max_digits=12, decimal_places=2)
    alugueis_ativos = serializers.IntegerField()
    alugueis_vencendo = serializers.IntegerField()
    os_abertas = serializers.IntegerField()
    os_urgentes = serializers.IntegerField()
    contas_receber_vencidas = serializers.DecimalField(max_digits=12, decimal_places=2)
    contas_pagar_vencidas = serializers.DecimalField(max_digits=12, decimal_places=2)
    agendamentos_hoje = serializers.IntegerField()
    tarefas_pendentes = serializers.IntegerField()


class RelatorioVendasSerializer(serializers.Serializer):
    """Serializer para relatório de vendas."""
    periodo_inicio = serializers.DateField()
    periodo_fim = serializers.DateField()
    total_vendas = serializers.IntegerField()
    valor_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    valor_recebido = serializers.DecimalField(max_digits=12, decimal_places=2)
    valor_pendente = serializers.DecimalField(max_digits=12, decimal_places=2)
    ticket_medio = serializers.DecimalField(max_digits=12, decimal_places=2)
    vendas_por_consultor = serializers.ListField()
    vendas_por_tipo = serializers.DictField()
