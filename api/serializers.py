"""
=============================================================================
LIFE RAINBOW 2.0 - Serializers para API REST
Serializers para todos os módulos do sistema
=============================================================================
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User

# Imports dos modelos
from clientes.models import Cliente, Endereco, HistoricoInteracao, ClienteFoto, ObservacaoCliente
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


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer customizado para incluir dados do usuário no JWT.
    Adiciona: role, email, first_name, last_name, is_staff, permissions
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Dados básicos do usuário
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['is_staff'] = user.is_staff
        token['username'] = user.username

        # Role e permissões do perfil
        if hasattr(user, 'profile'):
            token['role'] = user.profile.role
            token['permissions'] = user.profile.permissions
        else:
            # Fallback: admin se is_staff, senão comercial
            token['role'] = 'admin' if user.is_staff else 'comercial'
            token['permissions'] = {}

        return token


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
            'id', 'tipo', 'direcao', 'descricao', 'resultado',
            'usuario', 'usuario_nome', 'created_at', 'proxima_acao', 'data_proxima_acao'
        ]
        read_only_fields = ['id', 'usuario_nome', 'created_at']


class ClienteFotoSerializer(serializers.ModelSerializer):
    """Serializer para fotos de documentação do cliente."""
    foto_url = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = ClienteFoto
        fields = [
            'id', 'tipo', 'tipo_display', 'foto', 'foto_url',
            'descricao', 'created_at'
        ]
        read_only_fields = ['id', 'foto_url', 'tipo_display', 'created_at']

    def get_foto_url(self, obj):
        """Retorna a URL absoluta da foto."""
        request = self.context.get('request')
        if obj.foto and request:
            return request.build_absolute_uri(obj.foto.url)
        elif obj.foto:
            return obj.foto.url
        return None


class ObservacaoClienteSerializer(serializers.ModelSerializer):
    """Serializer para observações dos consultores."""
    usuario_nome = serializers.SerializerMethodField()

    class Meta:
        model = ObservacaoCliente
        fields = ['id', 'texto', 'usuario', 'usuario_nome', 'created_at']
        read_only_fields = ['id', 'usuario_nome', 'created_at']

    def get_usuario_nome(self, obj):
        if obj.usuario:
            nome = obj.usuario.get_full_name()
            return nome if nome else obj.usuario.username
        return 'Sistema'


class ClienteListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de clientes."""
    endereco_principal = serializers.SerializerMethodField()
    dias_sem_contato = serializers.SerializerMethodField()
    cidade = serializers.SerializerMethodField()
    estado = serializers.SerializerMethodField()

    class Meta:
        model = Cliente
        fields = [
            'id', 'nome', 'telefone', 'email', 'cidade', 'estado',
            'perfil', 'status', 'endereco_principal', 'dias_sem_contato',
            'possui_rainbow', 'data_ultimo_contato'
        ]

    def get_endereco_principal(self, obj):
        endereco = obj.enderecos.filter(principal=True).first()
        if endereco:
            return f"{endereco.cidade}/{endereco.estado}"
        return None

    def get_dias_sem_contato(self, obj):
        return obj.dias_sem_contato

    def get_cidade(self, obj):
        endereco = obj.enderecos.filter(principal=True).first()
        return endereco.cidade if endereco else None

    def get_estado(self, obj):
        endereco = obj.enderecos.filter(principal=True).first()
        return endereco.estado if endereco else None


class ClienteDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes do cliente."""
    enderecos = EnderecoSerializer(many=True, read_only=True)
    historico_interacoes = HistoricoInteracaoSerializer(
        source='historico_interacoes.all',
        many=True,
        read_only=True
    )
    fotos = ClienteFotoSerializer(many=True, read_only=True)
    observacoes_consultor = ObservacaoClienteSerializer(many=True, read_only=True)
    consultor_nome = serializers.CharField(source='consultor_responsavel.get_full_name', read_only=True)
    vendas = serializers.SerializerMethodField()
    equipamentos = serializers.SerializerMethodField()

    # Campos calculados para timeline do cliente (últimas ações)
    ultima_preventiva = serializers.SerializerMethodField()
    ultimo_atendimento = serializers.SerializerMethodField()
    ultima_interacao = serializers.SerializerMethodField()
    ultima_compra_liquido = serializers.SerializerMethodField()

    # Campos calculados para próximas ações do cliente
    proxima_preventiva = serializers.SerializerMethodField()
    proxima_compra_liquido = serializers.SerializerMethodField()
    proxima_interacao = serializers.SerializerMethodField()

    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_vendas(self, obj):
        """Retorna as vendas do cliente ordenadas por data."""
        from vendas.models import Venda
        vendas = obj.vendas.all().order_by('-data_venda')[:20]  # Últimas 20 vendas
        return [
            {
                'id': v.id,
                'numero': v.numero,
                'data_venda': v.data_venda.isoformat() if v.data_venda else None,
                'valor_total': str(v.valor_total),
                'status': v.status,
                'status_display': v.get_status_display(),
                'forma_pagamento': v.forma_pagamento,
                'forma_pagamento_display': v.get_forma_pagamento_display(),
                'numero_parcelas': v.numero_parcelas,
            }
            for v in vendas
        ]

    def get_equipamentos(self, obj):
        """Retorna os equipamentos do cliente."""
        from equipamentos.models import Equipamento
        equipamentos = obj.equipamentos.select_related('modelo').all()
        return [
            {
                'id': e.id,
                'numero_serie': e.numero_serie,
                'modelo_nome': e.modelo.nome if e.modelo else None,
                'categoria': e.modelo.categoria if e.modelo else None,
                'categoria_display': e.modelo.get_categoria_display() if e.modelo else None,
                'status': e.status,
                'status_display': e.get_status_display(),
                'data_venda': e.data_venda.isoformat() if e.data_venda else None,
                'data_fim_garantia': e.data_fim_garantia.isoformat() if e.data_fim_garantia else None,
                'em_garantia': e.em_garantia,
                'possui_power': e.possui_power,
                'numero_power': e.numero_power,
            }
            for e in equipamentos
        ]

    def get_ultima_preventiva(self, obj):
        """
        Retorna a última manutenção preventiva realizada.
        Busca no Agendamento com tipo='manutencao' e status='realizado'.
        """
        agendamento = obj.agendamentos.filter(
            tipo='manutencao',
            status='realizado'
        ).order_by('-data').first()

        if agendamento:
            return {
                'data': agendamento.data.isoformat() if agendamento.data else None,
                'tipo': 'Manutenção Preventiva',
                'responsavel': agendamento.responsavel.get_full_name() if agendamento.responsavel else None,
            }
        return None

    def get_ultimo_atendimento(self, obj):
        """
        Retorna o último atendimento presencial realizado.
        Busca no Agendamento com status='realizado' (visita, demonstração, manutenção).
        """
        tipos_presenciais = ['visita', 'demonstracao', 'manutencao', 'entrega', 'retirada']
        agendamento = obj.agendamentos.filter(
            tipo__in=tipos_presenciais,
            status='realizado'
        ).order_by('-data').first()

        if agendamento:
            return {
                'data': agendamento.data.isoformat() if agendamento.data else None,
                'tipo': agendamento.get_tipo_display(),
                'responsavel': agendamento.responsavel.get_full_name() if agendamento.responsavel else None,
            }
        return None

    def get_ultima_interacao(self, obj):
        """
        Retorna a última interação (contato remoto) com o cliente.
        Busca no HistoricoInteracao (ligação, whatsapp, email).
        """
        tipos_remotos = ['ligacao', 'whatsapp', 'email']
        interacao = obj.historico_interacoes.filter(
            tipo__in=tipos_remotos
        ).order_by('-created_at').first()

        if interacao:
            return {
                'data': interacao.created_at.isoformat() if interacao.created_at else None,
                'tipo': interacao.get_tipo_display(),
                'direcao': interacao.get_direcao_display(),
                'usuario': interacao.usuario.get_full_name() if interacao.usuario else None,
            }
        return None

    def get_ultima_compra_liquido(self, obj):
        """
        Retorna a última compra de líquidos do cliente.
        Busca em ItemVenda com modelo de categoria 'liquido' ou 'acessorio'.
        """
        from vendas.models import ItemVenda

        ultima_compra = ItemVenda.objects.filter(
            venda__cliente=obj,
            venda__status__in=['concluida', 'parcial', 'pendente'],
            modelo__categoria__in=['liquido', 'acessorio']
        ).select_related('venda', 'modelo').order_by('-venda__data_venda').first()

        if ultima_compra:
            return {
                'data': ultima_compra.venda.data_venda.isoformat() if ultima_compra.venda.data_venda else None,
                'tipo': ultima_compra.modelo.nome if ultima_compra.modelo else 'Líquido',
                'valor': str(ultima_compra.valor_total) if ultima_compra.valor_total else None,
                'venda_numero': ultima_compra.venda.numero,
            }
        return None

    def get_proxima_preventiva(self, obj):
        """
        Calcula a data da próxima manutenção preventiva.
        Baseado na última preventiva realizada + giro do cliente (12/15/18/24 meses).
        Ou retorna o próximo agendamento de manutenção pendente se existir.
        """
        from dateutil.relativedelta import relativedelta
        from datetime import date

        # Primeiro, verifica se há agendamento de manutenção pendente
        proximo_agendamento = obj.agendamentos.filter(
            tipo='manutencao',
            status__in=['agendado', 'confirmado'],
            data__gte=date.today()
        ).order_by('data').first()

        if proximo_agendamento:
            return {
                'data': proximo_agendamento.data.isoformat(),
                'tipo': 'Agendado',
                'dias_restantes': (proximo_agendamento.data - date.today()).days,
            }

        # Senão, calcula baseado na última preventiva + giro
        ultima = obj.agendamentos.filter(
            tipo='manutencao',
            status='realizado'
        ).order_by('-data').first()

        if ultima and obj.giro:
            # Converte giro para meses (ex: '12_meses' -> 12)
            giro_str = obj.giro.replace('_meses', '')
            try:
                meses = int(giro_str)
                proxima_data = ultima.data + relativedelta(months=meses)
                dias_restantes = (proxima_data - date.today()).days
                return {
                    'data': proxima_data.isoformat(),
                    'tipo': 'Calculado',
                    'dias_restantes': dias_restantes,
                    'status': 'atrasado' if dias_restantes < 0 else 'pendente',
                }
            except (ValueError, TypeError):
                pass

        return None

    def get_proxima_compra_liquido(self, obj):
        """
        Calcula a data da próxima compra de líquidos.
        Baseado na última compra de líquidos + periodicidade do cliente.
        """
        from dateutil.relativedelta import relativedelta
        from datetime import date

        # Verifica se cliente tem periodicidade definida
        if not obj.periodicidade_liquido:
            return None

        # Busca última venda que contenha líquidos
        # (itens com modelo de categoria 'acessorio' ou 'liquido')
        from vendas.models import ItemVenda
        ultima_compra_liquido = ItemVenda.objects.filter(
            venda__cliente=obj,
            venda__status__in=['concluida', 'parcial', 'pendente'],
            modelo__categoria__in=['acessorio', 'liquido']
        ).select_related('venda').order_by('-venda__data_venda').first()

        if ultima_compra_liquido:
            ultima_data = ultima_compra_liquido.venda.data_venda
            proxima_data = ultima_data + relativedelta(months=obj.periodicidade_liquido)
            dias_restantes = (proxima_data - date.today()).days
            return {
                'data': proxima_data.isoformat(),
                'tipo': obj.get_liquido_display() if obj.liquido else 'Líquidos',
                'dias_restantes': dias_restantes,
                'status': 'atrasado' if dias_restantes < 0 else 'pendente',
                'ultima_compra': ultima_data.isoformat(),
            }

        return None

    def get_proxima_interacao(self, obj):
        """
        Retorna a próxima interação programada com o cliente.
        Busca no FollowUp com status=pendente.
        """
        from datetime import date

        # Busca próximo follow-up pendente
        from agenda.models import FollowUp
        proximo_followup = obj.follow_ups.filter(
            status='pendente',
            data_prevista__gte=date.today()
        ).order_by('data_prevista').first()

        if proximo_followup:
            dias_restantes = (proximo_followup.data_prevista - date.today()).days
            return {
                'data': proximo_followup.data_prevista.isoformat(),
                'tipo': proximo_followup.get_tipo_display(),
                'assunto': proximo_followup.assunto,
                'dias_restantes': dias_restantes,
                'prioridade': proximo_followup.prioridade,
            }

        # Se não há follow-up, verifica data_proxima_ligacao do cliente
        if obj.data_proxima_ligacao:
            dias_restantes = (obj.data_proxima_ligacao - date.today()).days
            return {
                'data': obj.data_proxima_ligacao.isoformat(),
                'tipo': 'Ligação',
                'assunto': 'Ligação programada',
                'dias_restantes': dias_restantes,
                'prioridade': 'media',
            }

        return None


class ClienteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação/atualização de clientes."""
    enderecos = EnderecoSerializer(many=True, required=False)

    class Meta:
        model = Cliente
        exclude = ['created_at', 'updated_at']

    def validate_whatsapp(self, value):
        """Valida se o WhatsApp é único no sistema."""
        if not value:
            return value

        # Verifica se já existe outro cliente com este WhatsApp
        queryset = Cliente.objects.filter(whatsapp=value)

        # Se estamos atualizando, exclui o cliente atual da verificação
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            cliente_existente = queryset.first()
            raise serializers.ValidationError(
                f'Este WhatsApp já está cadastrado para o cliente: {cliente_existente.nome}'
            )

        return value

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
        read_only_fields = ['id', 'created_at', 'updated_at']


# =============================================================================
# VENDAS
# =============================================================================

class ItemVendaSerializer(serializers.ModelSerializer):
    """Serializer para itens de venda."""
    produto_nome = serializers.SerializerMethodField()
    modelo_nome = serializers.SerializerMethodField()
    equipamento_serie = serializers.SerializerMethodField()

    class Meta:
        model = ItemVenda
        fields = [
            'id', 'equipamento', 'modelo', 'produto',
            'produto_nome', 'modelo_nome', 'equipamento_serie',
            'quantidade', 'valor_unitario', 'valor_custo_unitario',
            'desconto', 'valor_total', 'observacoes'
        ]

    def get_produto_nome(self, obj):
        """Retorna nome do produto do estoque (se houver)."""
        if obj.produto:
            return obj.produto.nome
        return None

    def get_modelo_nome(self, obj):
        """Retorna nome do modelo do equipamento (se houver)."""
        if obj.modelo:
            return obj.modelo.nome
        elif obj.equipamento and obj.equipamento.modelo:
            return obj.equipamento.modelo.nome
        return None

    def get_equipamento_serie(self, obj):
        """Retorna número de série do equipamento (se houver)."""
        if obj.equipamento:
            return obj.equipamento.numero_serie
        return None


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
    vendedor_nome = serializers.CharField(source='vendedor.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Venda
        fields = [
            'id', 'numero', 'cliente', 'cliente_nome', 'vendedor', 'vendedor_nome',
            'data_venda', 'valor_total', 'status', 'status_display'
        ]


class VendaClienteSerializer(serializers.ModelSerializer):
    """Serializer resumido para exibir vendas no detalhe do cliente."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    forma_pagamento_display = serializers.CharField(source='get_forma_pagamento_display', read_only=True)

    class Meta:
        model = Venda
        fields = [
            'id', 'numero', 'data_venda', 'valor_total', 'status', 'status_display',
            'forma_pagamento', 'forma_pagamento_display', 'numero_parcelas'
        ]


class VendaDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes da venda."""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    vendedor_nome = serializers.CharField(source='vendedor.get_full_name', read_only=True)
    itens = ItemVendaSerializer(many=True, read_only=True)
    parcelas = ParcelaSerializer(many=True, read_only=True)
    total_pago = serializers.SerializerMethodField()
    saldo_devedor = serializers.SerializerMethodField()

    class Meta:
        model = Venda
        fields = '__all__'
        read_only_fields = ['id', 'numero', 'data_venda', 'updated_at']

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
        read_only_fields = ['id', 'numero', 'created_at', 'updated_at']

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
    plano_conta_nome = serializers.CharField(source='plano_conta.nome', read_only=True)
    consultor_nome = serializers.CharField(source='consultor.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ContaReceber
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContaPagarSerializer(serializers.ModelSerializer):
    """Serializer para contas a pagar."""
    plano_conta_nome = serializers.CharField(source='plano_conta.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ContaPagar
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CaixaSerializer(serializers.ModelSerializer):
    """Serializer para caixas."""
    usuario_abertura_nome = serializers.CharField(source='usuario_abertura.get_full_name', read_only=True)
    usuario_fechamento_nome = serializers.CharField(source='usuario_fechamento.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Caixa
        fields = '__all__'
        read_only_fields = ['id', 'data_hora_abertura']


class MovimentacaoSerializer(serializers.ModelSerializer):
    """Serializer para movimentações."""
    caixa_data = serializers.DateField(source='caixa.data', read_only=True)
    plano_conta_nome = serializers.CharField(source='plano_conta.nome', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    movimento_display = serializers.CharField(source='get_movimento_display', read_only=True)

    class Meta:
        model = Movimentacao
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


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
        read_only_fields = ['id', 'created_at', 'updated_at']


class FollowUpSerializer(serializers.ModelSerializer):
    """Serializer para follow-ups."""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)

    class Meta:
        model = FollowUp
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TarefaSerializer(serializers.ModelSerializer):
    """Serializer para tarefas."""
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    criado_por_nome = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Tarefa
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


# =============================================================================
# ASSISTÊNCIA TÉCNICA
# =============================================================================

class ItemOrdemServicoSerializer(serializers.ModelSerializer):
    """Serializer para itens de ordem de serviço (leitura)."""
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    produto_codigo = serializers.CharField(source='produto.codigo', read_only=True)
    estoque_disponivel = serializers.IntegerField(source='produto.estoque_atual', read_only=True)

    class Meta:
        model = ItemOrdemServico
        fields = [
            'id', 'ordem_servico', 'descricao', 'quantidade',
            'valor_unitario', 'valor_total', 'produto',
            'produto_nome', 'produto_codigo', 'estoque_disponivel'
        ]
        read_only_fields = ['id', 'valor_total']


class ItemOrdemServicoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criar/atualizar itens de OS.
    Valida disponibilidade de estoque automaticamente.
    """

    class Meta:
        model = ItemOrdemServico
        fields = [
            'id', 'ordem_servico', 'descricao', 'quantidade',
            'valor_unitario', 'produto'
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        """Valida disponibilidade de estoque."""
        produto = attrs.get('produto')
        quantidade = attrs.get('quantidade', 1)

        if produto:
            # Verificar estoque disponível
            if produto.estoque_atual < quantidade:
                raise serializers.ValidationError({
                    'quantidade': (
                        f"Estoque insuficiente para '{produto.nome}': "
                        f"disponível {produto.estoque_atual}, solicitado {quantidade}"
                    )
                })

            # Alertar se estoque ficará baixo
            estoque_apos = produto.estoque_atual - quantidade
            if estoque_apos <= produto.estoque_minimo:
                # Apenas alerta, não bloqueia
                self.context['estoque_alerta'] = (
                    f"Atenção: Após esta operação, o estoque de '{produto.nome}' "
                    f"ficará em {estoque_apos} (mínimo: {produto.estoque_minimo})"
                )

        return attrs

    def create(self, validated_data):
        """Cria item com usuário para rastreamento."""
        request = self.context.get('request')
        instance = ItemOrdemServico(**validated_data)

        if request and request.user:
            instance._usuario = request.user

        instance.save()
        return instance


class OrdemServicoListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de OS."""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    equipamento_serie = serializers.CharField(source='equipamento.numero_serie', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prioridade_display = serializers.CharField(source='get_prioridade_display', read_only=True)

    class Meta:
        model = OrdemServico
        fields = [
            'id', 'numero', 'cliente', 'cliente_nome', 'equipamento', 'equipamento_serie',
            'prioridade', 'prioridade_display', 'data_abertura', 'status', 'status_display', 'valor_total'
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
        read_only_fields = ['id', 'numero', 'data_abertura', 'updated_at']


# =============================================================================
# ESTOQUE
# =============================================================================

class ProdutoSerializer(serializers.ModelSerializer):
    """Serializer para produtos."""
    estoque_baixo = serializers.SerializerMethodField()

    class Meta:
        model = Produto
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_estoque_baixo(self, obj):
        return obj.estoque_atual <= obj.estoque_minimo


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
        read_only_fields = ['id', 'created_at', 'updated_at']


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
