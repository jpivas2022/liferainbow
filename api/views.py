"""
=============================================================================
LIFE RAINBOW 2.0 - Views para API REST
ViewSets e APIViews para todos os módulos do sistema
=============================================================================
"""

import requests
import logging

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)

# Imports dos modelos
from clientes.models import Cliente, Endereco, HistoricoInteracao, ClienteFoto
from equipamentos.models import ModeloEquipamento, Equipamento, HistoricoManutencao
from vendas.models import Venda, ItemVenda, Parcela
from alugueis.models import ContratoAluguel, ParcelaAluguel
from financeiro.models import PlanoConta, ContaReceber, ContaPagar, Caixa, Movimentacao
from agenda.models import Agendamento, FollowUp, Tarefa
from assistencia.models import OrdemServico, ItemOrdemServico
from estoque.models import Produto, MovimentacaoEstoque, Inventario
from whatsapp_integration.models import Conversa, Mensagem, Template, CampanhaMensagem

# Imports dos serializers
from .serializers import (
    # Usuários
    UserSerializer, UserCreateSerializer,
    # Clientes
    ClienteListSerializer, ClienteDetailSerializer, ClienteCreateUpdateSerializer,
    EnderecoSerializer, HistoricoInteracaoSerializer, ClienteFotoSerializer,
    # Equipamentos
    ModeloEquipamentoSerializer, EquipamentoListSerializer, EquipamentoDetailSerializer,
    HistoricoManutencaoSerializer,
    # Vendas
    VendaListSerializer, VendaDetailSerializer, ItemVendaSerializer, ParcelaSerializer,
    # Aluguéis
    ContratoAluguelListSerializer, ContratoAluguelDetailSerializer,
    ParcelaAluguelSerializer, HistoricoAluguelSerializer,
    # Financeiro
    PlanoContaSerializer, ContaReceberSerializer, ContaPagarSerializer,
    CaixaSerializer, MovimentacaoSerializer,
    # Agenda
    AgendamentoSerializer, FollowUpSerializer, TarefaSerializer,
    # Assistência
    OrdemServicoListSerializer, OrdemServicoDetailSerializer,
    ItemOrdemServicoSerializer, ItemOrdemServicoCreateSerializer,
    # Estoque
    ProdutoSerializer, MovimentacaoEstoqueSerializer, InventarioSerializer,
    # WhatsApp
    ConversaSerializer, MensagemSerializer, TemplateSerializer, CampanhaMensagemSerializer,
    # Dashboard
    DashboardSerializer, RelatorioVendasSerializer,
)


# =============================================================================
# CLIENTES
# =============================================================================

class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gerenciamento de clientes.

    Endpoints:
    - GET /api/clientes/ - Lista clientes
    - POST /api/clientes/ - Cria cliente
    - GET /api/clientes/{id}/ - Detalhes do cliente
    - PUT /api/clientes/{id}/ - Atualiza cliente
    - DELETE /api/clientes/{id}/ - Remove cliente
    - GET /api/clientes/sem-contato/ - Clientes sem contato
    - GET /api/clientes/aniversariantes/ - Aniversariantes do mês
    - POST /api/clientes/{id}/registrar-contato/ - Registra interação
    """
    queryset = Cliente.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'perfil', 'possui_rainbow', 'consultor_responsavel']
    search_fields = ['nome', 'email', 'telefone', 'cpf_cnpj']
    ordering_fields = ['nome', 'created_at', 'data_ultimo_contato']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ClienteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ClienteCreateUpdateSerializer
        return ClienteDetailSerializer

    @action(detail=False, methods=['get'], url_path='sem-contato')
    def sem_contato(self, request):
        """Lista clientes sem contato há mais de 30 dias."""
        dias = int(request.query_params.get('dias', 30))
        data_limite = timezone.now() - timedelta(days=dias)

        clientes = Cliente.objects.filter(
            Q(data_ultimo_contato__lt=data_limite) | Q(data_ultimo_contato__isnull=True),
            status='ativo'
        ).order_by('data_ultimo_contato')

        serializer = ClienteListSerializer(clientes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def aniversariantes(self, request):
        """Lista aniversariantes do mês atual.
        NOTA: Campo data_nascimento não existe no modelo atual.
        Retorna lista vazia até o campo ser adicionado.
        """
        # TODO: Adicionar campo data_nascimento ao modelo Cliente
        return Response([])

    @action(detail=True, methods=['post'], url_path='registrar-contato')
    def registrar_contato(self, request, pk=None):
        """Registra uma interação com o cliente."""
        cliente = self.get_object()

        interacao = HistoricoInteracao.objects.create(
            cliente=cliente,
            tipo=request.data.get('tipo', 'ligacao'),
            direcao=request.data.get('direcao', 'saida'),
            descricao=request.data.get('descricao', ''),
            resultado=request.data.get('resultado', ''),
            usuario=request.user,
            proxima_acao=request.data.get('proxima_acao'),
            data_proxima_acao=request.data.get('data_proxima_acao'),
        )

        cliente.data_ultimo_contato = timezone.now()
        cliente.save()

        return Response(HistoricoInteracaoSerializer(interacao).data)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser], url_path='upload-fotos')
    def upload_fotos(self, request, pk=None):
        """
        Upload de múltiplas fotos para o cliente.

        POST /api/clientes/{id}/upload-fotos/
        Content-Type: multipart/form-data

        Parâmetros:
        - tipo: tipo da foto (ficha_retirada, foto_rainbow, contrato_aluguel)
        - fotos: arquivos de imagem (até 3)
        - descricao: descrição opcional

        Tipos de foto:
        - ficha_retirada: Ficha de retirada (pós-venda)
        - foto_rainbow: Foto do equipamento Rainbow (pós-venda)
        - contrato_aluguel: Contrato/termo de aluguel
        """
        cliente = self.get_object()
        tipo = request.data.get('tipo')
        descricao = request.data.get('descricao', '')

        # Validar tipo
        tipos_validos = [choice[0] for choice in ClienteFoto.TIPO_CHOICES]
        if tipo not in tipos_validos:
            return Response(
                {'error': f'Tipo inválido. Valores aceitos: {tipos_validos}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar limite de 3 fotos por tipo
        fotos_existentes = ClienteFoto.objects.filter(
            cliente=cliente, tipo=tipo
        ).count()

        fotos_enviadas = request.FILES.getlist('fotos')
        if not fotos_enviadas:
            # Tentar pegar foto única
            foto_unica = request.FILES.get('foto')
            if foto_unica:
                fotos_enviadas = [foto_unica]

        if not fotos_enviadas:
            return Response(
                {'error': 'Nenhuma foto enviada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if fotos_existentes + len(fotos_enviadas) > 3:
            return Response(
                {'error': f'Limite de 3 fotos por tipo. Já existem {fotos_existentes} fotos deste tipo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Salvar fotos
        fotos_criadas = []
        for foto_arquivo in fotos_enviadas:
            foto = ClienteFoto.objects.create(
                cliente=cliente,
                foto=foto_arquivo,
                tipo=tipo,
                descricao=descricao,
                created_by=request.user
            )
            fotos_criadas.append(foto)

        serializer = ClienteFotoSerializer(
            fotos_criadas, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def fotos(self, request, pk=None):
        """
        Lista fotos do cliente, opcionalmente filtradas por tipo.

        GET /api/clientes/{id}/fotos/
        GET /api/clientes/{id}/fotos/?tipo=ficha_retirada
        """
        cliente = self.get_object()
        tipo = request.query_params.get('tipo')

        fotos = ClienteFoto.objects.filter(cliente=cliente)
        if tipo:
            fotos = fotos.filter(tipo=tipo)

        serializer = ClienteFotoSerializer(
            fotos, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], url_path='fotos/(?P<foto_id>[^/.]+)')
    def deletar_foto(self, request, pk=None, foto_id=None):
        """
        Deleta uma foto específica do cliente.

        DELETE /api/clientes/{id}/fotos/{foto_id}/
        """
        cliente = self.get_object()

        try:
            foto = ClienteFoto.objects.get(id=foto_id, cliente=cliente)
            foto.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ClienteFoto.DoesNotExist:
            return Response(
                {'error': 'Foto não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )


class EnderecoViewSet(viewsets.ModelViewSet):
    """ViewSet para endereços de clientes."""
    serializer_class = EnderecoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Endereco.objects.filter(cliente_id=self.kwargs.get('cliente_pk'))


# =============================================================================
# EQUIPAMENTOS
# =============================================================================

class ModeloEquipamentoViewSet(viewsets.ModelViewSet):
    """ViewSet para modelos de equipamento Rainbow."""
    queryset = ModeloEquipamento.objects.all()
    serializer_class = ModeloEquipamentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome', 'codigo']


class EquipamentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para equipamentos Rainbow.

    Endpoints adicionais:
    - GET /api/equipamentos/garantia-vencendo/ - Garantias próximas do vencimento
    - GET /api/equipamentos/sem-manutencao/ - Sem manutenção há mais de 6 meses
    """
    queryset = Equipamento.objects.select_related('modelo', 'cliente')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'modelo', 'cliente']
    search_fields = ['numero_serie', 'cliente__nome']

    def get_serializer_class(self):
        if self.action == 'list':
            return EquipamentoListSerializer
        return EquipamentoDetailSerializer

    @action(detail=False, methods=['get'], url_path='garantia-vencendo')
    def garantia_vencendo(self, request):
        """Lista equipamentos com garantia vencendo em 30 dias."""
        dias = int(request.query_params.get('dias', 30))
        hoje = timezone.now().date()
        data_limite = hoje + timedelta(days=dias)

        equipamentos = Equipamento.objects.filter(
            data_fim_garantia__gte=hoje,
            data_fim_garantia__lte=data_limite,
            status__in=['vendido', 'alugado']
        ).order_by('data_fim_garantia')

        serializer = EquipamentoListSerializer(equipamentos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='sem-manutencao')
    def sem_manutencao(self, request):
        """Lista equipamentos sem manutenção há mais de 6 meses."""
        meses = int(request.query_params.get('meses', 6))
        data_limite = timezone.now().date() - timedelta(days=meses * 30)

        equipamentos = Equipamento.objects.filter(
            Q(data_ultima_manutencao__lt=data_limite) | Q(data_ultima_manutencao__isnull=True),
            status__in=['vendido', 'alugado']
        ).order_by('data_ultima_manutencao')

        serializer = EquipamentoListSerializer(equipamentos, many=True)
        return Response(serializer.data)


# =============================================================================
# VENDAS
# =============================================================================

class VendaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para vendas.

    Endpoints adicionais:
    - GET /api/vendas/resumo/ - Resumo de vendas do período
    - POST /api/vendas/{id}/registrar-pagamento/ - Registra pagamento de parcela
    """
    queryset = Venda.objects.select_related('cliente', 'vendedor')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'vendedor', 'cliente']
    ordering_fields = ['data_venda', 'valor_total']
    ordering = ['-data_venda']

    def get_serializer_class(self):
        if self.action == 'list':
            return VendaListSerializer
        return VendaDetailSerializer

    @action(detail=False, methods=['get'])
    def resumo(self, request):
        """Retorna resumo de vendas do período."""
        dias = int(request.query_params.get('dias', 30))
        data_inicio = timezone.now() - timedelta(days=dias)

        vendas = Venda.objects.filter(data_venda__gte=data_inicio)

        resumo = vendas.aggregate(
            total_vendas=Count('id'),
            valor_total=Sum('valor_total'),
        )

        # Vendas por vendedor
        por_vendedor = vendas.values(
            'vendedor__first_name', 'vendedor__last_name'
        ).annotate(
            quantidade=Count('id'),
            valor=Sum('valor_total')
        ).order_by('-valor')

        return Response({
            'periodo_dias': dias,
            'total_vendas': resumo['total_vendas'] or 0,
            'valor_total': resumo['valor_total'] or 0,
            'por_vendedor': list(por_vendedor),
        })

    @action(detail=True, methods=['post'], url_path='registrar-pagamento')
    def registrar_pagamento(self, request, pk=None):
        """Registra pagamento de uma parcela."""
        venda = self.get_object()
        parcela_id = request.data.get('parcela_id')
        valor_pago = request.data.get('valor_pago')
        forma_pagamento = request.data.get('forma_pagamento')

        try:
            parcela = venda.parcelas.get(id=parcela_id)
            parcela.valor_pago = valor_pago
            parcela.data_pagamento = timezone.now()
            parcela.forma_pagamento = forma_pagamento
            parcela.status = 'pago'
            parcela.save()

            return Response(ParcelaSerializer(parcela).data)
        except Parcela.DoesNotExist:
            return Response(
                {'error': 'Parcela não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )


# =============================================================================
# ALUGUÉIS
# =============================================================================

class ContratoAluguelViewSet(viewsets.ModelViewSet):
    """
    ViewSet para contratos de aluguel.

    Endpoints adicionais:
    - GET /api/alugueis/vencendo/ - Contratos com parcelas vencendo
    - GET /api/alugueis/atrasados/ - Contratos com parcelas atrasadas
    """
    queryset = ContratoAluguel.objects.select_related('cliente', 'equipamento')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'cliente']
    ordering = ['-data_inicio']

    def get_serializer_class(self):
        if self.action == 'list':
            return ContratoAluguelListSerializer
        return ContratoAluguelDetailSerializer

    def perform_create(self, serializer):
        contrato = serializer.save()
        contrato.gerar_parcelas()

    @action(detail=False, methods=['get'])
    def vencendo(self, request):
        """Lista contratos com parcelas vencendo nos próximos dias."""
        dias = int(request.query_params.get('dias', 7))
        hoje = timezone.now().date()
        data_limite = hoje + timedelta(days=dias)

        contratos = ContratoAluguel.objects.filter(
            parcelas__data_vencimento__gte=hoje,
            parcelas__data_vencimento__lte=data_limite,
            parcelas__status='pendente',
            status='ativo'
        ).distinct()

        serializer = ContratoAluguelListSerializer(contratos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def atrasados(self, request):
        """Lista contratos com parcelas atrasadas."""
        hoje = timezone.now().date()

        contratos = ContratoAluguel.objects.filter(
            parcelas__data_vencimento__lt=hoje,
            parcelas__status='pendente',
            status='ativo'
        ).distinct()

        serializer = ContratoAluguelListSerializer(contratos, many=True)
        return Response(serializer.data)


# =============================================================================
# FINANCEIRO
# =============================================================================

class PlanoContaViewSet(viewsets.ModelViewSet):
    """ViewSet para plano de contas."""
    queryset = PlanoConta.objects.filter(conta_pai__isnull=True)
    serializer_class = PlanoContaSerializer
    permission_classes = [IsAuthenticated]


class ContaReceberViewSet(viewsets.ModelViewSet):
    """ViewSet para contas a receber."""
    queryset = ContaReceber.objects.select_related('cliente', 'plano_conta', 'consultor')
    serializer_class = ContaReceberSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'cliente']
    ordering = ['data_vencimento']

    @action(detail=False, methods=['get'])
    def vencidas(self, request):
        """Lista contas a receber vencidas."""
        hoje = timezone.now().date()
        contas = ContaReceber.objects.filter(
            data_vencimento__lt=hoje,
            status='pendente'
        ).order_by('data_vencimento')

        serializer = ContaReceberSerializer(contas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def baixar(self, request, pk=None):
        """Baixa (recebe) uma conta."""
        conta = self.get_object()
        conta.valor_pago = request.data.get('valor_pago', conta.valor)
        conta.data_pagamento = timezone.now().date()
        conta.status = 'pago'
        conta.save()

        return Response(ContaReceberSerializer(conta).data)


class ContaPagarViewSet(viewsets.ModelViewSet):
    """ViewSet para contas a pagar."""
    queryset = ContaPagar.objects.select_related('plano_conta')
    serializer_class = ContaPagarSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering = ['data_vencimento']

    @action(detail=False, methods=['get'])
    def vencidas(self, request):
        """Lista contas a pagar vencidas."""
        hoje = timezone.now().date()
        contas = ContaPagar.objects.filter(
            data_vencimento__lt=hoje,
            status='pendente'
        ).order_by('data_vencimento')

        serializer = ContaPagarSerializer(contas, many=True)
        return Response(serializer.data)


class CaixaViewSet(viewsets.ModelViewSet):
    """ViewSet para caixas."""
    queryset = Caixa.objects.all()
    serializer_class = CaixaSerializer
    permission_classes = [IsAuthenticated]


class MovimentacaoViewSet(viewsets.ModelViewSet):
    """ViewSet para movimentações financeiras."""
    queryset = Movimentacao.objects.select_related('caixa', 'plano_conta', 'usuario')
    serializer_class = MovimentacaoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['caixa', 'tipo']
    ordering = ['-data', '-created_at']


# =============================================================================
# AGENDA
# =============================================================================

class AgendamentoViewSet(viewsets.ModelViewSet):
    """ViewSet para agendamentos."""
    queryset = Agendamento.objects.select_related('cliente', 'responsavel')
    serializer_class = AgendamentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tipo', 'status', 'responsavel']
    ordering = ['data', 'hora_inicio']

    @action(detail=False, methods=['get'])
    def hoje(self, request):
        """Lista agendamentos de hoje."""
        hoje = timezone.now().date()
        agendamentos = Agendamento.objects.filter(
            data=hoje
        ).order_by('hora_inicio')

        serializer = AgendamentoSerializer(agendamentos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def semana(self, request):
        """Lista agendamentos da semana."""
        hoje = timezone.now().date()
        fim_semana = hoje + timedelta(days=7)

        agendamentos = Agendamento.objects.filter(
            data__gte=hoje,
            data__lte=fim_semana
        ).order_by('data', 'hora_inicio')

        serializer = AgendamentoSerializer(agendamentos, many=True)
        return Response(serializer.data)


class FollowUpViewSet(viewsets.ModelViewSet):
    """ViewSet para follow-ups."""
    queryset = FollowUp.objects.select_related('cliente', 'responsavel')
    serializer_class = FollowUpSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo', 'prioridade', 'status', 'responsavel']


class TarefaViewSet(viewsets.ModelViewSet):
    """ViewSet para tarefas."""
    queryset = Tarefa.objects.select_related('responsavel', 'created_by')
    serializer_class = TarefaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'prioridade', 'responsavel']


# =============================================================================
# ASSISTÊNCIA TÉCNICA
# =============================================================================

class OrdemServicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ordens de serviço.

    Endpoints adicionais:
    - GET /api/ordens-servico/abertas/ - OS abertas
    - GET /api/ordens-servico/urgentes/ - OS urgentes
    """
    queryset = OrdemServico.objects.select_related('cliente', 'equipamento', 'tecnico')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'prioridade', 'tecnico']
    ordering = ['-data_abertura']

    def get_serializer_class(self):
        if self.action == 'list':
            return OrdemServicoListSerializer
        return OrdemServicoDetailSerializer

    @action(detail=False, methods=['get'])
    def abertas(self, request):
        """Lista ordens de serviço abertas."""
        os_abertas = OrdemServico.objects.filter(
            status__in=['aberta', 'analise', 'orcamento', 'aprovado', 'execucao']
        ).order_by('-prioridade', 'data_abertura')

        serializer = OrdemServicoListSerializer(os_abertas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def urgentes(self, request):
        """Lista ordens de serviço urgentes (prioridade urgente ou alta)."""
        os_urgentes = OrdemServico.objects.filter(
            prioridade__in=['urgente', 'alta'],
            status__in=['aberta', 'analise', 'orcamento', 'aprovado', 'execucao']
        ).order_by('data_abertura')

        serializer = OrdemServicoListSerializer(os_urgentes, many=True)
        return Response(serializer.data)

    # =========================================================================
    # GERENCIAMENTO DE ITENS DA OS (Integração com Estoque)
    # =========================================================================

    @action(detail=True, methods=['get'], url_path='itens')
    def listar_itens(self, request, pk=None):
        """
        Lista todos os itens de uma OS.
        GET /api/ordens-servico/{id}/itens/
        """
        os = self.get_object()
        itens = os.itens.select_related('produto').all()
        serializer = ItemOrdemServicoSerializer(itens, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='adicionar-item')
    def adicionar_item(self, request, pk=None):
        """
        Adiciona um item à OS com baixa automática de estoque.

        POST /api/ordens-servico/{id}/adicionar-item/
        {
            "descricao": "Filtro Rainbow",
            "quantidade": 1,
            "valor_unitario": 150.00,
            "produto": 45  // opcional - ID do produto no estoque
        }

        Se produto for informado:
        - Valida disponibilidade de estoque
        - Cria MovimentacaoEstoque automaticamente (via signal)
        - Atualiza estoque do produto
        """
        os = self.get_object()

        # Preparar dados com a OS
        data = request.data.copy()
        data['ordem_servico'] = os.id

        serializer = ItemOrdemServicoCreateSerializer(
            data=data,
            context={'request': request}
        )

        if serializer.is_valid():
            item = serializer.save()

            # Atualizar valor_pecas da OS
            os.valor_pecas = sum(i.valor_total for i in os.itens.all())
            os.save()

            # Preparar resposta
            response_data = ItemOrdemServicoSerializer(item).data
            response_data['os_valor_pecas'] = float(os.valor_pecas)
            response_data['os_valor_total'] = float(os.valor_total)

            # Incluir alerta de estoque baixo se houver
            if 'estoque_alerta' in serializer.context:
                response_data['alerta'] = serializer.context['estoque_alerta']

            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='remover-item/(?P<item_id>[^/.]+)')
    def remover_item(self, request, pk=None, item_id=None):
        """
        Remove um item da OS com devolução automática ao estoque.

        DELETE /api/ordens-servico/{id}/remover-item/{item_id}/

        Se o item tinha produto vinculado:
        - Cria MovimentacaoEstoque de devolução (via signal)
        - Atualiza estoque do produto
        """
        os = self.get_object()

        try:
            item = os.itens.get(id=item_id)
        except ItemOrdemServico.DoesNotExist:
            return Response(
                {'error': f'Item {item_id} não encontrado nesta OS'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Guardar info para resposta
        item_info = {
            'id': item.id,
            'descricao': item.descricao,
            'quantidade': item.quantidade,
            'valor_total': float(item.valor_total),
            'produto_nome': item.produto.nome if item.produto else None,
            'estoque_devolvido': item.produto is not None
        }

        # Associar usuário para o signal
        item._usuario = request.user

        # Deletar (signal fará a devolução ao estoque)
        item.delete()

        # Atualizar valor_pecas da OS
        os.valor_pecas = sum(i.valor_total for i in os.itens.all())
        os.save()

        return Response({
            'success': True,
            'message': f"Item '{item_info['descricao']}' removido com sucesso",
            'item_removido': item_info,
            'os_valor_pecas': float(os.valor_pecas),
            'os_valor_total': float(os.valor_total)
        })

    @action(detail=True, methods=['get'], url_path='impacto-estoque')
    def impacto_estoque(self, request, pk=None):
        """
        Retorna o impacto no estoque desta OS.

        GET /api/ordens-servico/{id}/impacto-estoque/
        """
        from estoque.signals import calcular_impacto_estoque

        os = self.get_object()
        impacto = calcular_impacto_estoque(os)

        return Response({
            'ordem_servico': os.numero,
            'status': os.status,
            'impacto': impacto
        })


# =============================================================================
# ESTOQUE
# =============================================================================

class ProdutoViewSet(viewsets.ModelViewSet):
    """ViewSet para produtos."""
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['categoria', 'ativo']
    search_fields = ['nome', 'codigo', 'codigo_barras']

    @action(detail=False, methods=['get'], url_path='estoque-baixo')
    def estoque_baixo(self, request):
        """Lista produtos com estoque abaixo do mínimo."""
        from django.db.models import F

        produtos = Produto.objects.filter(
            estoque_atual__lte=F('estoque_minimo'),
            ativo=True
        ).order_by('estoque_atual')

        serializer = ProdutoSerializer(produtos, many=True)
        return Response(serializer.data)


class MovimentacaoEstoqueViewSet(viewsets.ModelViewSet):
    """ViewSet para movimentações de estoque."""
    queryset = MovimentacaoEstoque.objects.select_related('produto', 'usuario')
    serializer_class = MovimentacaoEstoqueSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['produto', 'tipo']


# =============================================================================
# WHATSAPP
# =============================================================================

class ConversaViewSet(viewsets.ModelViewSet):
    """ViewSet para conversas WhatsApp."""
    queryset = Conversa.objects.select_related('cliente')
    serializer_class = ConversaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'cliente']

    @action(detail=True, methods=['post'])
    def enviar_mensagem(self, request, pk=None):
        """Envia uma mensagem na conversa."""
        from whatsapp_integration.services import whatsapp_service
        import asyncio

        conversa = self.get_object()
        texto = request.data.get('texto')

        # Envia via WhatsApp API
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resultado = loop.run_until_complete(
            whatsapp_service.enviar_mensagem_texto(
                conversa.telefone,
                texto
            )
        )
        loop.close()

        if resultado.get('success'):
            mensagem = Mensagem.objects.create(
                conversa=conversa,
                direcao='enviada',
                tipo='text',
                conteudo=texto,
                wamid=resultado.get('message_id'),
                status='enviada'
            )
            return Response(MensagemSerializer(mensagem).data)

        return Response(
            {'error': resultado.get('error')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class TemplateViewSet(viewsets.ModelViewSet):
    """ViewSet para templates WhatsApp."""
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['categoria', 'status']


class CampanhaMensagemViewSet(viewsets.ModelViewSet):
    """ViewSet para campanhas de mensagem."""
    queryset = CampanhaMensagem.objects.select_related('template', 'created_by')
    serializer_class = CampanhaMensagemSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        """Inicia a execução de uma campanha."""
        campanha = self.get_object()

        if campanha.status != 'rascunho':
            return Response(
                {'error': 'Campanha já foi iniciada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        campanha.status = 'agendada'
        campanha.save()

        # TODO: Disparar task Celery para executar campanha

        return Response({'message': 'Campanha agendada com sucesso'})


# =============================================================================
# DASHBOARD
# =============================================================================

class DashboardAPIView(APIView):
    """
    API para dados do dashboard principal.

    GET /api/dashboard/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hoje = timezone.now().date()
        inicio_mes = hoje.replace(day=1)

        # Clientes
        clientes_total = Cliente.objects.count()
        clientes_ativos = Cliente.objects.filter(status='ativo').count()

        data_30_dias = timezone.now() - timedelta(days=30)
        clientes_sem_contato = Cliente.objects.filter(
            Q(data_ultimo_contato__lt=data_30_dias) | Q(data_ultimo_contato__isnull=True),
            status='ativo'
        ).count()

        # Vendas do mês
        vendas_mes = Venda.objects.filter(data_venda__gte=inicio_mes)
        vendas_count = vendas_mes.count()
        vendas_valor = vendas_mes.aggregate(total=Sum('valor_total'))['total'] or Decimal('0')

        # Aluguéis
        alugueis_ativos = ContratoAluguel.objects.filter(status='ativo').count()
        alugueis_vencendo = ParcelaAluguel.objects.filter(
            contrato__status='ativo',
            status='pendente',
            data_vencimento__lte=hoje + timedelta(days=7)
        ).values('contrato').distinct().count()

        # Ordens de serviço
        os_abertas = OrdemServico.objects.filter(
            status__in=['aberta', 'analise', 'orcamento', 'aprovado', 'execucao']
        ).count()
        os_urgentes = OrdemServico.objects.filter(
            prioridade__in=['urgente', 'alta'],
            status__in=['aberta', 'analise', 'orcamento', 'aprovado', 'execucao']
        ).count()

        # Financeiro
        contas_receber_vencidas = ContaReceber.objects.filter(
            data_vencimento__lt=hoje,
            status='pendente'
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0')

        contas_pagar_vencidas = ContaPagar.objects.filter(
            data_vencimento__lt=hoje,
            status='pendente'
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0')

        # Agenda
        agendamentos_hoje = Agendamento.objects.filter(
            data=hoje
        ).count()

        tarefas_pendentes = Tarefa.objects.filter(
            status='pendente'
        ).count()

        data = {
            'clientes_total': clientes_total,
            'clientes_ativos': clientes_ativos,
            'clientes_sem_contato_30d': clientes_sem_contato,
            'vendas_mes': vendas_count,
            'vendas_valor_mes': vendas_valor,
            'alugueis_ativos': alugueis_ativos,
            'alugueis_vencendo': alugueis_vencendo,
            'os_abertas': os_abertas,
            'os_urgentes': os_urgentes,
            'contas_receber_vencidas': contas_receber_vencidas,
            'contas_pagar_vencidas': contas_pagar_vencidas,
            'agendamentos_hoje': agendamentos_hoje,
            'tarefas_pendentes': tarefas_pendentes,
        }

        serializer = DashboardSerializer(data)
        return Response(serializer.data)


# =============================================================================
# AI ASSISTANT
# =============================================================================

class AIAssistantAPIView(APIView):
    """
    API para interação com o assistente de IA.

    POST /api/ai/comando/
    {
        "mensagem": "Quais clientes não receberam contato este mês?"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from ai_assistant.services import AIAssistant
        import asyncio

        mensagem = request.data.get('mensagem')
        if not mensagem:
            return Response(
                {'error': 'Mensagem é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )

        assistant = AIAssistant()

        # Executar processamento assíncrono
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            resultado = loop.run_until_complete(
                assistant.processar_comando(
                    mensagem=mensagem,
                    usuario=request.user
                )
            )
        finally:
            loop.close()

        return Response(resultado)


# =============================================================================
# WEBHOOKS
# =============================================================================

class WhatsAppWebhookAPIView(APIView):
    """
    Webhook para receber mensagens do WhatsApp.

    GET /api/webhooks/whatsapp/ - Verificação do webhook
    POST /api/webhooks/whatsapp/ - Receber eventos
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Verificação do webhook pelo Facebook."""
        verify_token = request.query_params.get('hub.verify_token')
        challenge = request.query_params.get('hub.challenge')

        # TODO: Verificar token configurado
        expected_token = 'seu_verify_token_aqui'

        if verify_token == expected_token:
            return Response(int(challenge))

        return Response({'error': 'Invalid token'}, status=403)

    def post(self, request):
        """Processa eventos recebidos do WhatsApp."""
        from whatsapp_integration.services import whatsapp_service

        payload = request.data
        resultado = whatsapp_service.processar_webhook(payload)

        if resultado['tipo'] == 'mensagem_recebida':
            # Processar mensagem recebida
            telefone = resultado['telefone']

            # Buscar ou criar conversa
            try:
                cliente = Cliente.objects.get(telefone__endswith=telefone[-8:])
                conversa, _ = Conversa.objects.get_or_create(
                    cliente=cliente,
                    telefone=telefone,
                    defaults={'status': 'ativa'}
                )
            except Cliente.DoesNotExist:
                conversa, _ = Conversa.objects.get_or_create(
                    telefone=telefone,
                    defaults={'status': 'ativa'}
                )

            # Salvar mensagem
            Mensagem.objects.create(
                conversa=conversa,
                direcao='recebida',
                tipo=resultado.get('tipo_mensagem', 'text'),
                conteudo=resultado.get('conteudo', ''),
                wamid=resultado.get('wamid'),
                status='recebida'
            )

            # TODO: Processar com IA se necessário

        return Response({'status': 'ok'})


# =============================================================================
# GOOGLE PLACES API - Endpoints para autocomplete de endereço
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def places_autocomplete(request):
    """
    Busca sugestões de endereços usando Google Places Autocomplete.

    GET /api/v1/places/autocomplete/?input=Av Paulista

    Retorna lista de previsões com place_id, description, etc.
    """
    input_text = request.query_params.get('input', '')

    if len(input_text) < 3:
        return Response({'predictions': []})

    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)

    if not api_key:
        logger.error('GOOGLE_MAPS_API_KEY não configurada')
        return Response(
            {'error': 'Serviço de busca de endereços não configurado'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    try:
        url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json'
        params = {
            'input': input_text,
            'key': api_key,
            'language': 'pt-BR',
            'components': 'country:br',
            'types': 'address',
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if data.get('status') == 'OK':
            return Response({'predictions': data.get('predictions', [])})
        elif data.get('status') == 'ZERO_RESULTS':
            return Response({'predictions': []})
        else:
            logger.warning(f"Google Places API error: {data.get('status')} - {data.get('error_message', '')}")
            return Response({'predictions': []})

    except requests.RequestException as e:
        logger.error(f"Erro ao conectar com Google Places API: {e}")
        return Response({'predictions': []})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def places_details(request):
    """
    Busca detalhes completos de um lugar pelo place_id.

    GET /api/v1/places/details/?place_id=ChIJ...

    Retorna endereço parseado com CEP, logradouro, número, bairro, cidade, estado, coordenadas.
    """
    place_id = request.query_params.get('place_id', '')

    if not place_id:
        return Response(
            {'error': 'place_id é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )

    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)

    if not api_key:
        logger.error('GOOGLE_MAPS_API_KEY não configurada')
        return Response(
            {'error': 'Serviço de busca de endereços não configurado'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    try:
        url = 'https://maps.googleapis.com/maps/api/place/details/json'
        params = {
            'place_id': place_id,
            'key': api_key,
            'language': 'pt-BR',
            'fields': 'formatted_address,address_components,geometry',
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if data.get('status') != 'OK':
            logger.warning(f"Google Places Details error: {data.get('status')}")
            return Response(
                {'error': 'Endereço não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        result = data.get('result', {})
        components = result.get('address_components', [])
        geometry = result.get('geometry', {}).get('location', {})

        # Parsear componentes do endereço
        address_data = {
            'place_id': place_id,
            'formatted_address': result.get('formatted_address', ''),
            'latitude': geometry.get('lat'),
            'longitude': geometry.get('lng'),
            'cep': None,
            'logradouro': None,
            'numero': None,
            'bairro': None,
            'cidade': None,
            'estado': None,
            'pais': 'Brasil',
        }

        for component in components:
            types = component.get('types', [])
            short_name = component.get('short_name', '')
            long_name = component.get('long_name', '')

            if 'postal_code' in types:
                address_data['cep'] = short_name.replace('-', '')
            elif 'route' in types:
                address_data['logradouro'] = long_name
            elif 'street_number' in types:
                address_data['numero'] = short_name
            elif 'sublocality' in types or 'sublocality_level_1' in types:
                address_data['bairro'] = long_name
            elif 'administrative_area_level_2' in types:
                address_data['cidade'] = long_name
            elif 'administrative_area_level_1' in types:
                address_data['estado'] = short_name
            elif 'country' in types:
                address_data['pais'] = long_name

        return Response(address_data)

    except requests.RequestException as e:
        logger.error(f"Erro ao conectar com Google Places API: {e}")
        return Response(
            {'error': 'Erro ao buscar detalhes do endereço'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def places_by_cep(request):
    """
    Busca endereço pelo CEP usando ViaCEP (API gratuita brasileira).

    GET /api/v1/places/cep/?cep=01310100

    Retorna endereço parseado com logradouro, bairro, cidade, estado.
    """
    cep = request.query_params.get('cep', '')

    # Limpar CEP (remover tudo que não for dígito)
    cep_clean = ''.join(filter(str.isdigit, cep))

    if len(cep_clean) != 8:
        return Response(
            {'error': 'CEP deve ter 8 dígitos'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        url = f'https://viacep.com.br/ws/{cep_clean}/json/'
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get('erro'):
            return Response(
                {'error': 'CEP não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Converter para formato padronizado
        address_data = {
            'place_id': f'cep:{cep_clean}',
            'formatted_address': f"{data.get('logradouro', '')}, {data.get('bairro', '')} - {data.get('localidade', '')}/{data.get('uf', '')}",
            'cep': cep_clean,
            'logradouro': data.get('logradouro', ''),
            'numero': None,  # ViaCEP não retorna número
            'bairro': data.get('bairro', ''),
            'cidade': data.get('localidade', ''),
            'estado': data.get('uf', ''),
            'pais': 'Brasil',
            'latitude': None,  # ViaCEP não retorna coordenadas
            'longitude': None,
        }

        return Response(address_data)

    except requests.RequestException as e:
        logger.error(f"Erro ao conectar com ViaCEP: {e}")
        return Response(
            {'error': 'Erro ao buscar CEP'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
