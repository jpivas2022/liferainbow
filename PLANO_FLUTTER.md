# PLANO DE IMPLEMENTAÇÃO FLUTTER - LIFE RAINBOW 2.0

> Documento gerado com base na análise do código backend Django
> Data: Janeiro 2026
> Status: PRONTO PARA EXECUÇÃO

---

## SUMÁRIO EXECUTIVO

### Objetivo
Desenvolver aplicativo mobile Flutter para o sistema Life Rainbow 2.0, consumindo a API REST Django existente.

### Escopo
- App para consultores/vendedores Life Rainbow
- Gestão de clientes, vendas, aluguéis, agenda
- Integração com assistente de IA (GPT-4o-mini)
- WhatsApp Business integrado

### Evidências Base
- `api/serializers.py` (598 linhas) - 30+ serializers
- `api/views.py` (849 linhas) - ViewSets completos
- `api/urls.py` (137 linhas) - Todos endpoints mapeados
- 13 apps Django com 40+ modelos

---

## FASE 0: SETUP DO PROJETO

### 0.1 Criar Projeto Flutter
```bash
cd /Users/iciclodev/Development
flutter create liferainbow_app --org com.liferainbow
cd liferainbow_app
```

### 0.2 Estrutura de Diretórios
```
lib/
├── main.dart
├── app.dart
├── config/
│   ├── api_config.dart
│   ├── app_theme.dart
│   ├── app_routes.dart
│   └── constants.dart
├── core/
│   ├── http/
│   │   ├── api_client.dart
│   │   ├── api_interceptor.dart
│   │   └── api_exceptions.dart
│   └── storage/
│       └── secure_storage.dart
├── models/
├── services/
├── providers/
├── screens/
├── widgets/
└── utils/
```

### 0.3 Dependências (pubspec.yaml)
```yaml
dependencies:
  flutter:
    sdk: flutter

  # State Management
  flutter_riverpod: ^2.4.10

  # HTTP & API
  dio: ^5.4.0

  # Auth & Storage
  flutter_secure_storage: ^9.0.0
  jwt_decoder: ^2.0.1

  # UI Components
  flutter_svg: ^2.0.9
  cached_network_image: ^3.3.1
  shimmer: ^3.0.0

  # Forms
  flutter_form_builder: ^9.2.1
  form_builder_validators: ^9.1.0

  # Utils
  intl: ^0.19.0
  url_launcher: ^6.2.4

  # Calendar
  table_calendar: ^3.0.9

  # Charts
  fl_chart: ^0.66.2

  # Formatters
  mask_text_input_formatter: ^2.9.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.1
```

### Checklist Fase 0
- [ ] Criar projeto Flutter
- [ ] Configurar estrutura de diretórios
- [ ] Adicionar dependências
- [ ] Configurar análise estática (analysis_options.yaml)
- [ ] Criar arquivo .env.example

---

## FASE 1: CORE - AUTENTICAÇÃO E HTTP

### 1.1 API Config
**Arquivo:** `lib/config/api_config.dart`
**Evidência:** `api/urls.py:105-107` (endpoints JWT)

```dart
class ApiConfig {
  static const String baseUrl = 'http://localhost:8000/api/v1';

  // Endpoints de autenticação
  static const String tokenObtain = '/auth/token/';
  static const String tokenRefresh = '/auth/token/refresh/';
  static const String tokenVerify = '/auth/token/verify/';

  // Endpoints principais
  static const String dashboard = '/dashboard/';
  static const String clientes = '/clientes/';
  static const String vendas = '/vendas/';
  static const String alugueis = '/alugueis/';
  static const String equipamentos = '/equipamentos/';
  static const String ordensServico = '/ordens-servico/';
  static const String agendamentos = '/agendamentos/';
  static const String contasReceber = '/contas-receber/';
  static const String contasPagar = '/contas-pagar/';
  static const String aiComando = '/ai/comando/';
  static const String conversas = '/conversas/';
}
```

### 1.2 HTTP Client com Interceptor JWT
**Arquivo:** `lib/core/http/api_client.dart`
**Evidência:** API usa `rest_framework_simplejwt`

```dart
class ApiClient {
  late Dio _dio;
  final SecureStorage _storage;

  // Interceptor para:
  // 1. Adicionar Authorization: Bearer {token}
  // 2. Refresh automático quando 401
  // 3. Logging de requests/responses
}
```

### 1.3 Auth Service
**Arquivo:** `lib/services/auth_service.dart`
**Evidência:** `api/urls.py:105-107`

```dart
class AuthService {
  Future<AuthResponse> login(String username, String password);
  Future<void> logout();
  Future<bool> refreshToken();
  Future<bool> isAuthenticated();
  Future<User?> getCurrentUser();
}
```

### 1.4 Auth Provider
**Arquivo:** `lib/providers/auth_provider.dart`

```dart
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.read(authServiceProvider));
});

class AuthState {
  final bool isAuthenticated;
  final bool isLoading;
  final User? user;
  final String? error;
}
```

### 1.5 Login Screen
**Arquivo:** `lib/screens/auth/login_screen.dart`

```dart
// Campos:
// - username (TextField)
// - password (TextField obscure)
// - Botão "Entrar"
// - Logo Life Rainbow
// - Tratamento de erros
```

### 1.6 Splash Screen
**Arquivo:** `lib/screens/auth/splash_screen.dart`

```dart
// 1. Verificar token salvo
// 2. Se válido → HomeScreen
// 3. Se inválido → LoginScreen
```

### Checklist Fase 1
- [ ] Criar ApiConfig com todos endpoints
- [ ] Implementar ApiClient com Dio
- [ ] Implementar interceptor JWT
- [ ] Criar SecureStorage wrapper
- [ ] Implementar AuthService
- [ ] Criar AuthProvider (Riverpod)
- [ ] Desenvolver LoginScreen
- [ ] Desenvolver SplashScreen
- [ ] Testar fluxo completo de login
- [ ] Testar refresh automático de token

---

## FASE 2: DASHBOARD E NAVEGAÇÃO

### 2.1 Dashboard Model
**Arquivo:** `lib/models/dashboard.dart`
**Evidência:** `api/serializers.py:571-586`

```dart
class Dashboard {
  final int clientesTotal;
  final int clientesAtivos;
  final int clientesSemContato30d;
  final int vendasMes;
  final double vendasValorMes;
  final int alugueisAtivos;
  final int alugueisVencendo;
  final int osAbertas;
  final int osUrgentes;
  final double contasReceberVencidas;
  final double contasPagarVencidas;
  final int agendamentosHoje;
  final int tarefasPendentes;

  factory Dashboard.fromJson(Map<String, dynamic> json);
}
```

### 2.2 Dashboard Service
**Arquivo:** `lib/services/dashboard_service.dart`
**Evidência:** `api/views.py:658-739`

```dart
class DashboardService {
  Future<Dashboard> getDashboard();
}
```

### 2.3 Home Screen (Dashboard)
**Arquivo:** `lib/screens/home/home_screen.dart`
**Evidência:** `api/views.py:666-736` (dados retornados)

```dart
// Layout:
// - AppBar com título "Life Rainbow" e ícone de notificações
// - Grid de StatCards:
//   - Clientes (total, ativos, sem contato)
//   - Vendas (quantidade, valor do mês)
//   - Aluguéis (ativos, vencendo)
//   - OS (abertas, urgentes)
//   - Financeiro (receber/pagar vencidos)
//   - Agenda (hoje, tarefas)
// - Cada card clicável → navega para lista correspondente
// - Pull-to-refresh
```

### 2.4 App Drawer (Navegação)
**Arquivo:** `lib/widgets/common/app_drawer.dart`

```dart
// Itens do menu:
// 1. Dashboard (Home)
// 2. Clientes
// 3. Vendas
// 4. Aluguéis
// 5. Equipamentos
// 6. Ordens de Serviço
// 7. Agenda
// 8. Financeiro
// 9. Assistente IA
// 10. WhatsApp
// ---
// 11. Configurações
// 12. Sair
```

### 2.5 App Theme
**Arquivo:** `lib/config/app_theme.dart`

```dart
class AppColors {
  // Primary - Verde Rainbow
  static const primary = Color(0xFF00A86B);
  static const primaryDark = Color(0xFF008C57);

  // Perfis de Cliente
  static const perfilDiamante = Color(0xFFB9F2FF);
  static const perfilOuro = Color(0xFFFFD700);
  static const perfilPrata = Color(0xFFC0C0C0);
  static const perfilBronze = Color(0xFFCD7F32);
  static const perfilStandard = Color(0xFF9E9E9E);

  // Status
  static const statusPendente = Color(0xFFFFC107);
  static const statusConcluido = Color(0xFF28A745);
  static const statusCancelado = Color(0xFFDC3545);
  static const statusAtrasado = Color(0xFFFF5722);
}
```

### Checklist Fase 2
- [ ] Criar Dashboard model
- [ ] Implementar DashboardService
- [ ] Criar DashboardProvider
- [ ] Desenvolver StatCard widget
- [ ] Desenvolver HomeScreen com grid de cards
- [ ] Implementar AppDrawer
- [ ] Configurar AppTheme com cores Rainbow
- [ ] Configurar rotas (GoRouter ou Navigator)
- [ ] Testar navegação completa

---

## FASE 3: MÓDULO DE CLIENTES

### 3.1 Models de Cliente
**Arquivo:** `lib/models/cliente.dart`
**Evidência:** `clientes/models.py:14-284` (30+ campos)

```dart
class Cliente {
  final int id;
  final String nome;
  final String tipoPessoa; // 'PF' | 'PJ'
  final String? cpfCnpj;
  final String telefone;
  final String? telefoneSecundario;
  final String? email;
  final String? whatsapp;

  // Classificação
  final String status; // 'ativo' | 'inativo' | 'prospecto'
  final String perfil; // 'diamante' | 'ouro' | 'prata' | 'bronze' | 'standard'
  final String segmento; // 'residencial' | 'comercial' | 'industrial'

  // Rainbow específico
  final double? poderCompra;
  final bool possuiRainbow;
  final DateTime? dataCompraRainbow;

  // Acompanhamento
  final int? consultorResponsavelId;
  final String? consultorNome;
  final DateTime? dataProximaLigacao;
  final DateTime? dataUltimoContato;

  // Marketing
  final String? origem;
  final bool aceitaWhatsapp;
  final bool aceitaEmail;

  // Relacionamentos
  final List<Endereco>? enderecos;
  final List<HistoricoInteracao>? historicoInteracoes;

  // Computed
  int? get diasSemContato;
  Endereco? get enderecoPrincipal;

  factory Cliente.fromJson(Map<String, dynamic> json);
  Map<String, dynamic> toJson();
}
```

**Arquivo:** `lib/models/endereco.dart`
**Evidência:** `clientes/models.py:286-369`

```dart
class Endereco {
  final int id;
  final String tipo; // 'residencial' | 'comercial' | 'entrega' | 'cobranca'
  final bool principal;
  final String cep;
  final String logradouro;
  final String numero;
  final String? complemento;
  final String bairro;
  final String cidade;
  final String estado;
  final double? latitude;
  final double? longitude;
}
```

**Arquivo:** `lib/models/historico_interacao.dart`
**Evidência:** `clientes/models.py:372-465`

```dart
class HistoricoInteracao {
  final int id;
  final String tipo; // 'ligacao' | 'whatsapp' | 'email' | 'visita' | 'reuniao' | 'demonstracao'
  final String direcao; // 'entrada' | 'saida'
  final String descricao;
  final String? resultado;
  final String? proximaAcao;
  final DateTime? dataProximaAcao;
  final int? usuarioId;
  final String? usuarioNome;
  final bool geradoPorIa;
  final DateTime createdAt;
}
```

### 3.2 Cliente Service
**Arquivo:** `lib/services/cliente_service.dart`
**Evidência:** `api/views.py:65-140`

```dart
class ClienteService {
  // CRUD básico
  Future<PaginatedResponse<Cliente>> getClientes({
    int page = 1,
    String? status,
    String? perfil,
    String? cidade,
    String? estado,
    bool? possuiRainbow,
    int? consultorId,
    String? search,
    String? ordering,
  });

  Future<Cliente> getCliente(int id);
  Future<Cliente> createCliente(Cliente cliente);
  Future<Cliente> updateCliente(int id, Cliente cliente);
  Future<void> deleteCliente(int id);

  // Actions especiais (evidência: api/views.py:94-140)
  Future<List<Cliente>> getSemContato({int dias = 30});
  Future<List<Cliente>> getAniversariantes({int? mes});
  Future<HistoricoInteracao> registrarContato(int clienteId, {
    required String tipo,
    required String descricao,
    String? resultado,
    String? proximaAcao,
    DateTime? dataProximaAcao,
  });
}
```

### 3.3 Cliente Provider
**Arquivo:** `lib/providers/cliente_provider.dart`

```dart
// Provider para lista de clientes
final clientesProvider = StateNotifierProvider<ClientesNotifier, ClientesState>(...);

// Provider para cliente individual (com cache)
final clienteProvider = FutureProvider.family<Cliente, int>((ref, id) async {
  return ref.read(clienteServiceProvider).getCliente(id);
});

// Provider para clientes sem contato
final clientesSemContatoProvider = FutureProvider<List<Cliente>>((ref) async {
  return ref.read(clienteServiceProvider).getSemContato();
});
```

### 3.4 Telas de Cliente

**Arquivo:** `lib/screens/clientes/clientes_list_screen.dart`
```dart
// - AppBar com título e botão de busca
// - Filtros: status, perfil (chips)
// - Lista infinita com paginação
// - ClienteCard para cada item
// - FAB para adicionar novo cliente
// - Pull-to-refresh
```

**Arquivo:** `lib/screens/clientes/cliente_detail_screen.dart`
```dart
// - Foto/Avatar com iniciais
// - Nome, telefone, email, WhatsApp
// - Badge de perfil (cor correspondente)
// - Tabs: Dados, Endereços, Histórico, Vendas, Aluguéis
// - Ações: Ligar, WhatsApp, Editar
// - Botão registrar contato
```

**Arquivo:** `lib/screens/clientes/cliente_form_screen.dart`
```dart
// - Form com validação
// - Campos organizados em seções:
//   - Dados Pessoais (nome, tipo pessoa, CPF/CNPJ)
//   - Contato (telefone, email, WhatsApp)
//   - Classificação (status, perfil, segmento)
//   - Rainbow (possui, data compra, poder compra)
//   - Marketing (origem, aceita contato)
// - Endereços (adicionar múltiplos)
// - Máscara para CPF, CNPJ, telefone, CEP
```

### 3.5 Widgets de Cliente

**Arquivo:** `lib/widgets/cards/cliente_card.dart`
```dart
class ClienteCard extends StatelessWidget {
  final Cliente cliente;
  final VoidCallback? onTap;
  final VoidCallback? onWhatsApp;
  final VoidCallback? onLigar;

  // Exibe:
  // - Avatar com iniciais
  // - Nome
  // - Telefone
  // - Badge de perfil (colorido)
  // - Dias sem contato (se > 30)
  // - Ícones de ação (WhatsApp, Telefone)
}
```

**Arquivo:** `lib/widgets/badges/perfil_badge.dart`
```dart
class PerfilBadge extends StatelessWidget {
  final String perfil;

  // Retorna chip colorido:
  // - Diamante: azul claro
  // - Ouro: dourado
  // - Prata: cinza claro
  // - Bronze: bronze
  // - Standard: cinza
}
```

### Checklist Fase 3
- [ ] Criar model Cliente (30+ campos)
- [ ] Criar model Endereco
- [ ] Criar model HistoricoInteracao
- [ ] Implementar ClienteService com CRUD
- [ ] Implementar actions especiais (sem-contato, aniversariantes)
- [ ] Criar ClienteProvider
- [ ] Desenvolver ClientesListScreen com filtros
- [ ] Desenvolver ClienteDetailScreen com tabs
- [ ] Desenvolver ClienteFormScreen com validação
- [ ] Criar ClienteCard widget
- [ ] Criar PerfilBadge widget
- [ ] Implementar máscaras (CPF, CNPJ, telefone, CEP)
- [ ] Implementar busca
- [ ] Testar CRUD completo

---

## FASE 4: MÓDULO DE VENDAS

### 4.1 Models de Venda
**Arquivo:** `lib/models/venda.dart`
**Evidência:** `vendas/models.py:14-258`

```dart
class Venda {
  final int id;
  final String numero;
  final int clienteId;
  final String? clienteNome;
  final int? vendedorId;
  final String? vendedorNome;

  final String status; // 'pendente' | 'parcial' | 'concluida' | 'cancelada'
  final DateTime dataVenda;
  final DateTime? dataEntrega;
  final bool entregue;
  final String tipoEntrega;

  // Valores
  final double valorProdutos;
  final double valorCusto;
  final double desconto;
  final double acrescimo;
  final double valorFrete;
  final double valorTotal;

  // Pagamento
  final String formaPagamento;
  final int numeroParcelas;
  final DateTime? dataPrimeiroVencimento;

  // Relacionamentos
  final List<ItemVenda>? itens;
  final List<Parcela>? parcelas;

  // Computed
  double get lucro => valorTotal - valorCusto;
  double get margemLucro => valorTotal > 0 ? (lucro / valorTotal) * 100 : 0;
  double get totalPago;
  double get saldoDevedor;
}
```

**Arquivo:** `lib/models/item_venda.dart`
**Evidência:** `vendas/models.py:260-332`

```dart
class ItemVenda {
  final int id;
  final int? equipamentoId;
  final int modeloId;
  final String? produtoNome;
  final int quantidade;
  final double valorUnitario;
  final double valorCustoUnitario;
  final double desconto;
  final double valorTotal;
}
```

**Arquivo:** `lib/models/parcela.dart`
**Evidência:** `vendas/models.py:335-429`

```dart
class Parcela {
  final int id;
  final int numero;
  final double valor;
  final DateTime dataVencimento;
  final DateTime? dataPagamento;
  final String status; // 'pendente' | 'paga' | 'atrasada' | 'cancelada'
  final String? formaPagamento;
  final double? valorPago;
  final double juros;
  final double multa;

  int get diasAtraso;
}
```

### 4.2 Venda Service
**Arquivo:** `lib/services/venda_service.dart`
**Evidência:** `api/views.py:219-288`

```dart
class VendaService {
  Future<PaginatedResponse<Venda>> getVendas({
    int page = 1,
    String? status,
    String? tipoVenda,
    int? consultorId,
    int? clienteId,
    String? ordering,
  });

  Future<Venda> getVenda(int id);
  Future<Venda> createVenda(Venda venda);
  Future<Venda> updateVenda(int id, Venda venda);

  // Actions especiais
  Future<Map<String, dynamic>> getResumo({int dias = 30});
  Future<Parcela> registrarPagamento(int vendaId, {
    required int parcelaId,
    required double valorPago,
    required String formaPagamento,
  });
}
```

### 4.3 Telas de Venda

**Arquivo:** `lib/screens/vendas/vendas_list_screen.dart`
```dart
// - Filtros: status, período
// - Lista com VendaCard
// - Resumo no topo (total vendido no período)
// - FAB nova venda
```

**Arquivo:** `lib/screens/vendas/venda_detail_screen.dart`
```dart
// - Cabeçalho: número, cliente, data, status
// - Card de valores: total, desconto, frete
// - Lista de itens vendidos
// - Lista de parcelas com status
// - Ações: registrar pagamento de parcela
```

### Checklist Fase 4
- [ ] Criar model Venda
- [ ] Criar model ItemVenda
- [ ] Criar model Parcela
- [ ] Implementar VendaService
- [ ] Criar VendaProvider
- [ ] Desenvolver VendasListScreen
- [ ] Desenvolver VendaDetailScreen
- [ ] Implementar registro de pagamento
- [ ] Criar VendaCard widget
- [ ] Criar ParcelaWidget
- [ ] Testar fluxo completo

---

## FASE 5: MÓDULO DE ALUGUÉIS

### 5.1 Models de Aluguel
**Arquivo:** `lib/models/contrato_aluguel.dart`
**Evidência:** `alugueis/models.py:16-269`

```dart
class ContratoAluguel {
  final int id;
  final String numero;
  final int clienteId;
  final String? clienteNome;
  final int equipamentoId;
  final String? equipamentoSerie;
  final int? consultorId;

  // Período
  final DateTime dataInicio;
  final DateTime dataFimPrevista;
  final DateTime? dataFimReal;
  final int duracaoMeses;

  // Valores
  final double valorMensal;
  final double valorCaucao;
  final int diaVencimento;

  // Status
  final String status; // 'ativo' | 'encerrado' | 'suspenso' | 'convertido' | 'cancelado'

  // Entrega
  final DateTime? dataEntrega;
  final bool entregue;
  final DateTime? dataDevolucao;
  final bool devolvido;

  // Relacionamentos
  final List<ParcelaAluguel>? parcelas;

  // Computed
  int get mesesPagos;
  int get mesesPendentes;
  double get totalPago;
}
```

**Arquivo:** `lib/models/parcela_aluguel.dart`
**Evidência:** `alugueis/models.py:271-399`

```dart
class ParcelaAluguel {
  final int id;
  final int numero; // 1 a 12
  final String mesReferencia; // "MM/YYYY"
  final double valor;
  final DateTime dataVencimento;
  final DateTime? dataPagamento;
  final String status;
  final double? valorPago;
  final String? formaPagamento;
  final double juros;
  final double multa;
  final String? codigoPix;
  final String? linhaDigitavel;

  int get diasAtraso;
  double calcularValorComMulta({double taxaJurosDia = 0.033, double taxaMulta = 2.0});
}
```

### 5.2 Aluguel Service
**Arquivo:** `lib/services/aluguel_service.dart`
**Evidência:** `api/views.py:295-347`

```dart
class AluguelService {
  Future<PaginatedResponse<ContratoAluguel>> getContratos({
    int page = 1,
    String? status,
    int? clienteId,
    String? ordering,
  });

  Future<ContratoAluguel> getContrato(int id);
  Future<ContratoAluguel> createContrato(ContratoAluguel contrato);

  // Actions especiais (evidência: api/views.py:318-347)
  Future<List<ContratoAluguel>> getVencendo({int dias = 7});
  Future<List<ContratoAluguel>> getAtrasados();

  Future<ParcelaAluguel> registrarPagamentoParcela(int contratoId, int parcelaId, {
    required double valorPago,
    required String formaPagamento,
  });
}
```

### 5.3 Telas de Aluguel

**Arquivo:** `lib/screens/alugueis/alugueis_list_screen.dart`
```dart
// - Filtros: status (ativo, encerrado)
// - Cards de alertas: vencendo, atrasados
// - Lista de contratos
```

**Arquivo:** `lib/screens/alugueis/aluguel_detail_screen.dart`
```dart
// - Info do contrato: cliente, equipamento, período
// - Valores: mensal, caução
// - Grid de 12 parcelas (visual de calendário)
// - Cada parcela: mês, valor, status (pago/pendente/atrasado)
// - Ação: registrar pagamento
// - Cálculo automático de juros/multa
```

### 5.4 Widget de Parcelas
**Arquivo:** `lib/widgets/aluguel/parcelas_grid.dart`

```dart
class ParcelasGrid extends StatelessWidget {
  final List<ParcelaAluguel> parcelas;
  final Function(ParcelaAluguel) onPagar;

  // Grid 3x4 ou 4x3 mostrando os 12 meses
  // Cores: verde (pago), amarelo (pendente), vermelho (atrasado)
  // Tap abre modal de pagamento
}
```

### Checklist Fase 5
- [ ] Criar model ContratoAluguel
- [ ] Criar model ParcelaAluguel
- [ ] Implementar AluguelService
- [ ] Criar AluguelProvider
- [ ] Desenvolver AlugueisListScreen
- [ ] Desenvolver AluguelDetailScreen
- [ ] Criar ParcelasGrid widget
- [ ] Implementar cálculo de juros/multa
- [ ] Implementar registro de pagamento
- [ ] Criar alertas de vencimento

---

## FASE 6: MÓDULO DE AGENDA

### 6.1 Models de Agenda
**Arquivo:** `lib/models/agendamento.dart`
**Evidência:** `agenda/models.py:13-157`

```dart
class Agendamento {
  final int id;
  final String titulo;
  final String tipo; // 'demonstracao' | 'visita' | 'manutencao' | 'entrega' | 'retirada' | 'reuniao'
  final int clienteId;
  final String? clienteNome;
  final int? responsavelId;
  final String? responsavelNome;

  final DateTime data;
  final String horaInicio;
  final String? horaFim;
  final int duracaoEstimada;

  final String status; // 'agendado' | 'confirmado' | 'realizado' | 'cancelado' | 'remarcado' | 'nao_compareceu'

  final int? enderecoId;
  final String? localDescricao;

  final String? resultado;
  final int? vendaResultanteId;
}
```

**Arquivo:** `lib/models/tarefa.dart`
**Evidência:** `agenda/models.py:290-366`

```dart
class Tarefa {
  final int id;
  final String titulo;
  final String? descricao;
  final int? responsavelId;
  final String? responsavelNome;
  final DateTime? dataLimite;
  final String status; // 'pendente' | 'andamento' | 'concluida' | 'cancelada'
  final String prioridade; // 'baixa' | 'media' | 'alta' | 'urgente'
  final int? clienteId;
  final String? clienteNome;
}
```

### 6.2 Agenda Service
**Arquivo:** `lib/services/agenda_service.dart`
**Evidência:** `api/views.py:437-469`

```dart
class AgendaService {
  Future<List<Agendamento>> getAgendamentos({
    DateTime? data,
    String? tipo,
    String? status,
    int? responsavelId,
  });

  Future<Agendamento> getAgendamento(int id);
  Future<Agendamento> createAgendamento(Agendamento agendamento);
  Future<Agendamento> updateAgendamento(int id, Agendamento agendamento);

  // Actions especiais
  Future<List<Agendamento>> getHoje();
  Future<List<Agendamento>> getSemana();

  // Tarefas
  Future<List<Tarefa>> getTarefas({String? status, int? responsavelId});
  Future<Tarefa> createTarefa(Tarefa tarefa);
  Future<Tarefa> updateTarefa(int id, Tarefa tarefa);
}
```

### 6.3 Tela de Agenda
**Arquivo:** `lib/screens/agenda/agenda_screen.dart`

```dart
// - Calendário mensal (table_calendar)
// - Marcadores nos dias com agendamentos
// - Lista do dia selecionado abaixo
// - FAB para novo agendamento
// - Cores por tipo de agendamento
```

**Arquivo:** `lib/screens/agenda/agendamento_form_screen.dart`

```dart
// - Seletor de cliente
// - Tipo de agendamento (dropdown)
// - Data e hora
// - Duração estimada
// - Local/endereço
// - Observações
```

### Checklist Fase 6
- [ ] Criar model Agendamento
- [ ] Criar model Tarefa
- [ ] Implementar AgendaService
- [ ] Criar AgendaProvider
- [ ] Desenvolver AgendaScreen com calendário
- [ ] Desenvolver AgendamentoFormScreen
- [ ] Integrar table_calendar
- [ ] Criar AgendamentoCard widget
- [ ] Implementar filtros por tipo/responsável
- [ ] Criar TarefasScreen

---

## FASE 7: MÓDULO DE EQUIPAMENTOS E OS

### 7.1 Models
**Arquivo:** `lib/models/equipamento.dart`
**Evidência:** `equipamentos/models.py:128-286`

```dart
class Equipamento {
  final int id;
  final int modeloId;
  final String? modeloNome;
  final String numeroSerie;
  final String status; // 'estoque' | 'vendido' | 'alugado' | 'manutencao' | 'demonstracao' | 'sucata'
  final int? clienteId;
  final String? clienteNome;
  final DateTime? dataAquisicao;
  final DateTime? dataVenda;
  final DateTime? dataFimGarantia;
  final DateTime? dataProximaManutencao;
  final DateTime? dataUltimaManutencao;
  final String? localizacao;
  final String? numeroPower;
  final bool possuiPower;
  final String condicao;

  bool get emGarantia;
  bool get manutencaoAtrasada;
}
```

**Arquivo:** `lib/models/ordem_servico.dart`
**Evidência:** `assistencia/models.py:13-222`

```dart
class OrdemServico {
  final int id;
  final String numero;
  final int clienteId;
  final String? clienteNome;
  final int equipamentoId;
  final String? equipamentoSerie;
  final String descricaoProblema;
  final String? diagnostico;
  final String status; // 8 estados
  final String prioridade; // 'baixa' | 'normal' | 'alta' | 'urgente'
  final bool emGarantia;
  final DateTime dataAbertura;
  final DateTime? dataPrevisao;
  final DateTime? dataConclusao;
  final double valorMaoObra;
  final double valorPecas;
  final double desconto;
  final double valorTotal;
  final bool pago;
  final int? tecnicoId;
  final String? tecnicoNome;
  final List<ItemOrdemServico>? itens;
}
```

### 7.2 Services
**Arquivo:** `lib/services/equipamento_service.dart`
**Evidência:** `api/views.py:165-212`

```dart
class EquipamentoService {
  Future<List<Equipamento>> getEquipamentos({...});
  Future<Equipamento> getEquipamento(int id);
  Future<List<Equipamento>> getGarantiaVencendo({int dias = 30});
  Future<List<Equipamento>> getSemManutencao({int meses = 6});
}
```

**Arquivo:** `lib/services/ordem_servico_service.dart`
**Evidência:** `api/views.py:494-532`

```dart
class OrdemServicoService {
  Future<List<OrdemServico>> getOrdensServico({...});
  Future<OrdemServico> getOrdemServico(int id);
  Future<List<OrdemServico>> getAbertas();
  Future<List<OrdemServico>> getUrgentes();
}
```

### Checklist Fase 7
- [ ] Criar model Equipamento
- [ ] Criar model ModeloEquipamento
- [ ] Criar model OrdemServico
- [ ] Criar model ItemOrdemServico
- [ ] Implementar EquipamentoService
- [ ] Implementar OrdemServicoService
- [ ] Desenvolver EquipamentosListScreen
- [ ] Desenvolver EquipamentoDetailScreen
- [ ] Desenvolver OrdensServicoListScreen
- [ ] Desenvolver OrdemServicoDetailScreen
- [ ] Criar badges de garantia/manutenção

---

## FASE 8: MÓDULO FINANCEIRO

### 8.1 Models
**Arquivo:** `lib/models/conta_receber.dart`
**Evidência:** `financeiro/models.py:65-238`

```dart
class ContaReceber {
  final int id;
  final String descricao;
  final int? clienteId;
  final String? clienteNome;
  final double valor;
  final double? valorPago;
  final double juros;
  final double multa;
  final double desconto;
  final DateTime dataEmissao;
  final DateTime dataVencimento;
  final DateTime? dataPagamento;
  final String status;
  final String? formaPagamento;
  final int? vendaId;
  final int? contratoAluguelId;

  int get diasAtraso;
}
```

**Arquivo:** `lib/models/conta_pagar.dart`
**Evidência:** `financeiro/models.py:240-364`

### 8.2 Service
**Arquivo:** `lib/services/financeiro_service.dart`
**Evidência:** `api/views.py:354-413`

```dart
class FinanceiroService {
  Future<List<ContaReceber>> getContasReceber({String? status, int? clienteId});
  Future<List<ContaReceber>> getContasReceberVencidas({int diasAtraso = 1});
  Future<ContaReceber> baixarContaReceber(int id, {required double valorPago});

  Future<List<ContaPagar>> getContasPagar({String? status});
  Future<List<ContaPagar>> getContasPagarVencidas();
}
```

### Checklist Fase 8
- [ ] Criar model ContaReceber
- [ ] Criar model ContaPagar
- [ ] Implementar FinanceiroService
- [ ] Desenvolver FinanceiroScreen (resumo)
- [ ] Desenvolver ContasReceberScreen
- [ ] Desenvolver ContasPagarScreen
- [ ] Implementar baixa de conta
- [ ] Criar alertas de vencimento

---

## FASE 9: ASSISTENTE DE IA

### 9.1 AI Service
**Arquivo:** `lib/services/ai_service.dart`
**Evidência:** `ai_assistant/services.py:508-601`

```dart
class AIService {
  Future<AIResponse> enviarComando(String mensagem);
}

class AIResponse {
  final bool success;
  final String resposta;
  final List<String> funcoesExecutadas;
  final int tokensUsados;
  final String? error;
}
```

### 9.2 Chatbot Screen
**Arquivo:** `lib/screens/ai/chatbot_screen.dart`

```dart
// - Interface de chat (balões)
// - Campo de texto na parte inferior
// - Histórico de mensagens
// - Indicador de loading durante processamento
// - Exibir funções executadas (expandível)
//
// Exemplos de comandos suportados (evidência: ai_assistant/services.py:61-505):
// - "Quais clientes não receberam contato este mês?"
// - "Mostre o ranking de vendedores de dezembro"
// - "Agende uma demonstração para João amanhã às 14h"
// - "Envie mensagem WhatsApp para cliente 123"
// - "Verifique a garantia do equipamento SN12345"
```

### Checklist Fase 9
- [ ] Criar model AIResponse
- [ ] Implementar AIService
- [ ] Criar AIProvider
- [ ] Desenvolver ChatbotScreen
- [ ] Criar MessageBubble widget
- [ ] Implementar histórico local de mensagens
- [ ] Adicionar sugestões de comandos

---

## FASE 10: INTEGRAÇÃO WHATSAPP

### 10.1 Models
**Arquivo:** `lib/models/conversa.dart`
**Evidência:** `whatsapp_integration/models.py`

```dart
class Conversa {
  final int id;
  final int? clienteId;
  final String? clienteNome;
  final String telefone;
  final String status; // 'ativa' | 'aguardando' | 'encerrada'
  final String modoAtendimento; // 'ia' | 'humano' | 'hibrido'
  final DateTime iniciadaEm;
  final DateTime? atualizadaEm;
  final List<Mensagem>? mensagensRecentes;
}

class Mensagem {
  final int id;
  final String direcao; // 'entrada' | 'saida'
  final String tipo; // 'text' | 'image' | 'document' | 'audio'
  final String conteudo;
  final DateTime dataHora;
  final String status; // 'enviada' | 'entregue' | 'lida' | 'erro'
}
```

### 10.2 WhatsApp Service
**Arquivo:** `lib/services/whatsapp_service.dart`
**Evidência:** `api/views.py:575-617`

```dart
class WhatsAppService {
  Future<List<Conversa>> getConversas({String? status, int? clienteId});
  Future<Conversa> getConversa(int id);
  Future<Mensagem> enviarMensagem(int conversaId, String texto);
}
```

### 10.3 WhatsApp Screen
**Arquivo:** `lib/screens/whatsapp/conversas_screen.dart`

```dart
// - Lista de conversas (estilo WhatsApp)
// - Preview da última mensagem
// - Badge de não lidas
// - Filtro por status
```

**Arquivo:** `lib/screens/whatsapp/chat_screen.dart`

```dart
// - Interface de chat
// - Mensagens com balões (entrada/saída)
// - Campo de texto para enviar
// - Info do cliente no header
```

### Checklist Fase 10
- [ ] Criar model Conversa
- [ ] Criar model Mensagem
- [ ] Implementar WhatsAppService
- [ ] Desenvolver ConversasScreen
- [ ] Desenvolver ChatScreen
- [ ] Criar ChatBubble widget
- [ ] Implementar envio de mensagem

---

## CRONOGRAMA ESTIMADO

| Fase | Descrição | Duração | Acumulado |
|------|-----------|---------|-----------|
| 0 | Setup do Projeto | 2 dias | 2 dias |
| 1 | Core (Auth + HTTP) | 5 dias | 1 semana |
| 2 | Dashboard + Navegação | 4 dias | 1.5 semanas |
| 3 | Módulo Clientes | 7 dias | 2.5 semanas |
| 4 | Módulo Vendas | 5 dias | 3.5 semanas |
| 5 | Módulo Aluguéis | 5 dias | 4.5 semanas |
| 6 | Módulo Agenda | 4 dias | 5 semanas |
| 7 | Equipamentos + OS | 5 dias | 6 semanas |
| 8 | Módulo Financeiro | 4 dias | 7 semanas |
| 9 | Assistente IA | 3 dias | 7.5 semanas |
| 10 | WhatsApp | 4 dias | 8.5 semanas |
| - | Testes + Polish | 5 dias | **10 semanas** |

### MVP Mínimo (Fases 0-5): ~4.5 semanas
Funcionalidades: Auth, Dashboard, Clientes, Vendas, Aluguéis

---

## COMANDOS DE REFERÊNCIA

### Rodar Backend Django
```bash
cd /Users/iciclodev/Development/liferainbow
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### Rodar App Flutter
```bash
cd /Users/iciclodev/Development/liferainbow_app
flutter run
```

### Testar API
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "senha"}'

# Dashboard (com token)
curl http://localhost:8000/api/v1/dashboard/ \
  -H "Authorization: Bearer {token}"

# Clientes
curl http://localhost:8000/api/v1/clientes/ \
  -H "Authorization: Bearer {token}"
```

---

## NOTAS IMPORTANTES

### Evidências do Backend

1. **Autenticação JWT** (api/urls.py:105-107)
   - Token obtain: `/api/v1/auth/token/`
   - Token refresh: `/api/v1/auth/token/refresh/`

2. **Serializers prontos** (api/serializers.py)
   - 30+ serializers bem estruturados
   - List vs Detail serializers separados
   - Campos computados já calculados no backend

3. **ViewSets com actions** (api/views.py)
   - CRUD completo para todos recursos
   - Actions especiais: `@action(detail=False/True)`
   - Filtros via DjangoFilterBackend

4. **Integração IA** (ai_assistant/services.py)
   - 17 funções de Function Calling
   - System prompt contextualizado para Life Rainbow
   - GPT-4o-mini configurado

5. **Normalização de Aluguéis** (alugueis/models.py)
   - Estrutura 1:N ao invés de 12 colunas
   - Parcelas com cálculo de juros/multa
   - Método `gerar_parcelas()` no backend

### Padrões a Seguir

1. **Models** devem ter `fromJson` e `toJson`
2. **Services** devem usar ApiClient configurado
3. **Providers** devem usar Riverpod (StateNotifier ou AsyncNotifier)
4. **Screens** devem ter loading/error/empty states
5. **Widgets** devem ser reutilizáveis e testáveis

---

*Documento gerado automaticamente baseado na análise do código backend Django Life Rainbow 2.0*
