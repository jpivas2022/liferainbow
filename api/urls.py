"""
=============================================================================
LIFE RAINBOW 2.0 - URLs da API REST
Configuração de todas as rotas da API
=============================================================================
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    # Clientes
    ClienteViewSet,
    EnderecoViewSet,
    # Equipamentos
    ModeloEquipamentoViewSet,
    EquipamentoViewSet,
    # Vendas
    VendaViewSet,
    # Aluguéis
    ContratoAluguelViewSet,
    # Financeiro
    PlanoContaViewSet,
    ContaReceberViewSet,
    ContaPagarViewSet,
    CaixaViewSet,
    MovimentacaoViewSet,
    # Agenda
    AgendamentoViewSet,
    FollowUpViewSet,
    TarefaViewSet,
    # Assistência
    OrdemServicoViewSet,
    # Estoque
    ProdutoViewSet,
    MovimentacaoEstoqueViewSet,
    # WhatsApp
    ConversaViewSet,
    TemplateViewSet,
    CampanhaMensagemViewSet,
    # Dashboard e AI
    DashboardAPIView,
    AIAssistantAPIView,
    WhatsAppWebhookAPIView,
    # Google Places API
    places_autocomplete,
    places_details,
    places_by_cep,
)

# =============================================================================
# ROUTER CONFIGURATION
# =============================================================================

router = DefaultRouter()

# Clientes
router.register(r'clientes', ClienteViewSet, basename='cliente')

# Equipamentos
router.register(r'modelos-equipamento', ModeloEquipamentoViewSet, basename='modelo-equipamento')
router.register(r'equipamentos', EquipamentoViewSet, basename='equipamento')

# Vendas
router.register(r'vendas', VendaViewSet, basename='venda')

# Aluguéis
router.register(r'alugueis', ContratoAluguelViewSet, basename='aluguel')

# Financeiro
router.register(r'plano-contas', PlanoContaViewSet, basename='plano-conta')
router.register(r'contas-receber', ContaReceberViewSet, basename='conta-receber')
router.register(r'contas-pagar', ContaPagarViewSet, basename='conta-pagar')
router.register(r'caixas', CaixaViewSet, basename='caixa')
router.register(r'movimentacoes', MovimentacaoViewSet, basename='movimentacao')

# Agenda
router.register(r'agendamentos', AgendamentoViewSet, basename='agendamento')
router.register(r'followups', FollowUpViewSet, basename='followup')
router.register(r'tarefas', TarefaViewSet, basename='tarefa')

# Assistência
router.register(r'ordens-servico', OrdemServicoViewSet, basename='ordem-servico')

# Estoque
router.register(r'produtos', ProdutoViewSet, basename='produto')
router.register(r'movimentacoes-estoque', MovimentacaoEstoqueViewSet, basename='movimentacao-estoque')

# WhatsApp
router.register(r'conversas', ConversaViewSet, basename='conversa')
router.register(r'templates', TemplateViewSet, basename='template')
router.register(r'campanhas', CampanhaMensagemViewSet, basename='campanha')


# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

    # Autenticação JWT
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Dashboard
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard'),

    # AI Assistant
    path('ai/comando/', AIAssistantAPIView.as_view(), name='ai-comando'),

    # Webhooks
    path('webhooks/whatsapp/', WhatsAppWebhookAPIView.as_view(), name='webhook-whatsapp'),

    # Nested routes para endereços
    path(
        'clientes/<int:cliente_pk>/enderecos/',
        EnderecoViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='cliente-enderecos'
    ),

    # Google Places API - Autocomplete de endereço
    path('places/autocomplete/', places_autocomplete, name='places-autocomplete'),
    path('places/details/', places_details, name='places-details'),
    path('places/cep/', places_by_cep, name='places-cep'),
]


# =============================================================================
# API DOCUMENTATION (drf-spectacular)
# =============================================================================

"""
Documentação disponível em:
- /api/schema/ - OpenAPI schema
- /api/docs/ - Swagger UI
- /api/redoc/ - ReDoc
"""
