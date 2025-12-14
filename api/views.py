"""
=============================================================================
LIFE RAINBOW 2.0 - Views para API REST
ViewSets e APIViews para todos os módulos do sistema
=============================================================================
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

# Imports dos modelos
from clientes.models import Cliente, Endereco, HistoricoInteracao
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
    EnderecoSerializer, HistoricoInteracaoSerializer,
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
    OrdemServicoListSerializer, OrdemServicoDetailSerializer, ItemOrdemServicoSerializer,
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
    filterset_fields = ['status', 'perfil', 'cidade', 'estado', 'possui_rainbow', 'consultor']
    search_fields = ['nome', 'email', 'telefone', 'cpf']
    ordering_fields = ['nome', 'data_cadastro', 'ultimo_contato']
    ordering = ['-data_cadastro']

    def get_serializer_class(self):
        if self.action == 'list':
            return ClienteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ClienteCreateUpdateSerializer
        return ClienteDetailSerializer

    @action(detail=False, methods=['get'])
    def sem_contato(self, request):
        """Lista clientes sem contato há mais de 30 dias."""
        dias = int(request.query_params.get('dias', 30))
        data_limite = timezone.now() - timedelta(days=dias)

        clientes = Cliente.objects.filter(
            Q(ultimo_contato__lt=data_limite) | Q(ultimo_contato__isnull=True),
            status='ativo'
        ).order_by('ultimo_contato')

        serializer = ClienteListSerializer(clientes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def aniversariantes(self, request):
        """Lista aniversariantes do mês atual."""
        mes = int(request.query_params.get('mes', timezone.now().month))

        clientes = Cliente.objects.filter(
            data_nascimento__month=mes,
            status='ativo'
        ).order_by('data_nascimento__day')

        serializer = ClienteListSerializer(clientes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def registrar_contato(self, request, pk=None):
        """Registra uma interação com o cliente."""
        cliente = self.get_object()

        interacao = HistoricoInteracao.objects.create(
            cliente=cliente,
            tipo=request.data.get('tipo', 'contato'),
            canal=request.data.get('canal', 'telefone'),
            descricao=request.data.get('descricao', ''),
            resultado=request.data.get('resultado', ''),
            usuario=request.user,
            proxima_acao=request.data.get('proxima_acao'),
            data_proxima_acao=request.data.get('data_proxima_acao'),
        )

        cliente.ultimo_contato = timezone.now()
        cliente.save()

        return Response(HistoricoInteracaoSerializer(interacao).data)


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

    @action(detail=False, methods=['get'])
    def garantia_vencendo(self, request):
        """Lista equipamentos com garantia vencendo em 30 dias."""
        dias = int(request.query_params.get('dias', 30))
        hoje = timezone.now().date()
        data_limite = hoje + timedelta(days=dias)

        equipamentos = Equipamento.objects.filter(
            garantia_ate__gte=hoje,
            garantia_ate__lte=data_limite,
            status='ativo'
        ).order_by('garantia_ate')

        serializer = EquipamentoListSerializer(equipamentos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def sem_manutencao(self, request):
        """Lista equipamentos sem manutenção há mais de 6 meses."""
        meses = int(request.query_params.get('meses', 6))
        data_limite = timezone.now() - timedelta(days=meses * 30)

        equipamentos = Equipamento.objects.filter(
            Q(ultima_manutencao__lt=data_limite) | Q(ultima_manutencao__isnull=True),
            status='ativo'
        ).order_by('ultima_manutencao')

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
    queryset = Venda.objects.select_related('cliente', 'consultor')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'tipo_venda', 'consultor', 'cliente']
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

        # Vendas por consultor
        por_consultor = vendas.values(
            'consultor__first_name', 'consultor__last_name'
        ).annotate(
            quantidade=Count('id'),
            valor=Sum('valor_total')
        ).order_by('-valor')

        return Response({
            'periodo_dias': dias,
            'total_vendas': resumo['total_vendas'] or 0,
            'valor_total': resumo['valor_total'] or 0,
            'por_consultor': list(por_consultor),
        })

    @action(detail=True, methods=['post'])
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
    queryset = PlanoConta.objects.filter(pai__isnull=True)
    serializer_class = PlanoContaSerializer
    permission_classes = [IsAuthenticated]


class ContaReceberViewSet(viewsets.ModelViewSet):
    """ViewSet para contas a receber."""
    queryset = ContaReceber.objects.select_related('cliente', 'categoria')
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
    queryset = ContaPagar.objects.select_related('categoria')
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
    queryset = Movimentacao.objects.select_related('caixa', 'categoria')
    serializer_class = MovimentacaoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['caixa', 'tipo']
    ordering = ['-data_hora']


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
    ordering = ['data_hora']

    @action(detail=False, methods=['get'])
    def hoje(self, request):
        """Lista agendamentos de hoje."""
        hoje = timezone.now().date()
        agendamentos = Agendamento.objects.filter(
            data_hora__date=hoje
        ).order_by('data_hora')

        serializer = AgendamentoSerializer(agendamentos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def semana(self, request):
        """Lista agendamentos da semana."""
        hoje = timezone.now().date()
        fim_semana = hoje + timedelta(days=7)

        agendamentos = Agendamento.objects.filter(
            data_hora__date__gte=hoje,
            data_hora__date__lte=fim_semana
        ).order_by('data_hora')

        serializer = AgendamentoSerializer(agendamentos, many=True)
        return Response(serializer.data)


class FollowUpViewSet(viewsets.ModelViewSet):
    """ViewSet para follow-ups."""
    queryset = FollowUp.objects.select_related('cliente', 'responsavel')
    serializer_class = FollowUpSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo', 'prioridade', 'concluido', 'responsavel']


class TarefaViewSet(viewsets.ModelViewSet):
    """ViewSet para tarefas."""
    queryset = Tarefa.objects.select_related('responsavel', 'criado_por')
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
    filterset_fields = ['status', 'tipo_servico', 'tecnico', 'urgente']
    ordering = ['-data_abertura']

    def get_serializer_class(self):
        if self.action == 'list':
            return OrdemServicoListSerializer
        return OrdemServicoDetailSerializer

    @action(detail=False, methods=['get'])
    def abertas(self, request):
        """Lista ordens de serviço abertas."""
        os_abertas = OrdemServico.objects.filter(
            status__in=['aberta', 'em_andamento', 'aguardando_peca']
        ).order_by('-urgente', 'data_abertura')

        serializer = OrdemServicoListSerializer(os_abertas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def urgentes(self, request):
        """Lista ordens de serviço urgentes."""
        os_urgentes = OrdemServico.objects.filter(
            urgente=True,
            status__in=['aberta', 'em_andamento', 'aguardando_peca']
        ).order_by('data_abertura')

        serializer = OrdemServicoListSerializer(os_urgentes, many=True)
        return Response(serializer.data)


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

    @action(detail=False, methods=['get'])
    def estoque_baixo(self, request):
        """Lista produtos com estoque abaixo do mínimo."""
        from django.db.models import F

        produtos = Produto.objects.filter(
            quantidade_atual__lte=F('estoque_minimo'),
            ativo=True
        ).order_by('quantidade_atual')

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
    queryset = CampanhaMensagem.objects.select_related('template', 'criado_por')
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
            Q(ultimo_contato__lt=data_30_dias) | Q(ultimo_contato__isnull=True),
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
            status__in=['aberta', 'em_andamento', 'aguardando_peca']
        ).count()
        os_urgentes = OrdemServico.objects.filter(
            urgente=True,
            status__in=['aberta', 'em_andamento', 'aguardando_peca']
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
            data_hora__date=hoje
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
