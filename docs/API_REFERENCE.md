# 🔌 Life Rainbow 2.0 - Referência da API

## Informações Gerais

**Base URL:** `https://api.liferainbow.com.br/api/` (produção)
**Base URL Local:** `http://localhost:8000/api/`

**Content-Type:** `application/json`
**Autenticação:** Bearer Token (JWT)

---

## Autenticação

### Obter Token de Acesso

```http
POST /api/auth/token/
```

**Request Body:**
```json
{
    "username": "usuario",
    "password": "senha"
}
```

**Response (200 OK):**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Usar token nas requisições:**
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Renovar Token

```http
POST /api/auth/token/refresh/
```

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Verificar Token

```http
POST /api/auth/token/verify/
```

**Request Body:**
```json
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):** Token válido
**Response (401 Unauthorized):** Token inválido

---

## Clientes

### Listar Clientes

```http
GET /api/clientes/
```

**Query Parameters:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `page` | int | Número da página |
| `page_size` | int | Itens por página (max 100) |
| `search` | string | Busca por nome, email, telefone |
| `status` | string | Filtrar por status (ativo, inativo, prospecto) |
| `perfil` | string | Filtrar por perfil (diamante, ouro, prata, bronze, standard) |
| `cidade` | string | Filtrar por cidade |
| `estado` | string | Filtrar por estado (UF) |
| `possui_rainbow` | boolean | Filtrar por possui Rainbow |
| `consultor` | int | Filtrar por ID do consultor |
| `ordering` | string | Ordenação (nome, -data_cadastro, ultimo_contato) |

**Response (200 OK):**
```json
{
    "count": 150,
    "next": "http://api/clientes/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "nome": "João Silva",
            "telefone": "11999999999",
            "email": "joao@email.com",
            "cidade": "São Paulo",
            "estado": "SP",
            "perfil": "ouro",
            "status": "ativo",
            "endereco_principal": "São Paulo/SP",
            "dias_sem_contato": 15,
            "possui_rainbow": true,
            "ultimo_contato": "2025-12-01T10:30:00Z"
        }
    ]
}
```

### Criar Cliente

```http
POST /api/clientes/
```

**Request Body:**
```json
{
    "nome": "Maria Santos",
    "email": "maria@email.com",
    "telefone": "11988888888",
    "whatsapp": "11988888888",
    "cpf": "123.456.789-00",
    "data_nascimento": "1985-05-15",
    "profissao": "Empresária",
    "cidade": "São Paulo",
    "estado": "SP",
    "perfil": "standard",
    "status": "prospecto",
    "origem": "indicacao",
    "observacoes": "Interessada no modelo E2",
    "enderecos": [
        {
            "tipo": "residencial",
            "cep": "01310-100",
            "logradouro": "Av. Paulista",
            "numero": "1000",
            "complemento": "Apto 101",
            "bairro": "Bela Vista",
            "cidade": "São Paulo",
            "estado": "SP",
            "principal": true
        }
    ]
}
```

**Response (201 Created):**
```json
{
    "id": 151,
    "nome": "Maria Santos",
    ...
}
```

### Obter Cliente

```http
GET /api/clientes/{id}/
```

**Response (200 OK):**
```json
{
    "id": 1,
    "nome": "João Silva",
    "email": "joao@email.com",
    "telefone": "11999999999",
    "telefone_secundario": "",
    "whatsapp": "11999999999",
    "cpf": "123.456.789-00",
    "data_nascimento": "1980-03-20",
    "profissao": "Engenheiro",
    "renda_estimada": "15000.00",
    "cidade": "São Paulo",
    "estado": "SP",
    "perfil": "ouro",
    "status": "ativo",
    "origem": "indicacao",
    "possui_rainbow": true,
    "modelo_rainbow": "E2",
    "data_compra_rainbow": "2024-06-15",
    "interesse_rainbow": "",
    "consultor": 2,
    "consultor_nome": "Carlos Vendedor",
    "indicado_por": 45,
    "indicado_por_nome": "Pedro Indicador",
    "ultimo_contato": "2025-12-01T10:30:00Z",
    "observacoes": "Cliente VIP",
    "tags": "vip,rainbow,indicador",
    "data_cadastro": "2024-01-15T08:00:00Z",
    "atualizado_em": "2025-12-10T14:30:00Z",
    "enderecos": [
        {
            "id": 1,
            "tipo": "residencial",
            "cep": "01310-100",
            "logradouro": "Av. Paulista",
            "numero": "1000",
            "complemento": "Apto 101",
            "bairro": "Bela Vista",
            "cidade": "São Paulo",
            "estado": "SP",
            "principal": true,
            "latitude": "-23.5505",
            "longitude": "-46.6333"
        }
    ],
    "historico_interacoes": [
        {
            "id": 1,
            "tipo": "contato",
            "canal": "telefone",
            "descricao": "Ligação para agendar demonstração",
            "resultado": "Agendado para 15/12",
            "usuario": 2,
            "usuario_nome": "Carlos Vendedor",
            "data_hora": "2025-12-01T10:30:00Z",
            "proxima_acao": "Confirmar agendamento",
            "data_proxima_acao": "2025-12-14"
        }
    ]
}
```

### Atualizar Cliente

```http
PUT /api/clientes/{id}/
PATCH /api/clientes/{id}/
```

**Request Body (PATCH - parcial):**
```json
{
    "status": "ativo",
    "perfil": "ouro"
}
```

### Excluir Cliente

```http
DELETE /api/clientes/{id}/
```

**Response (204 No Content)**

### Clientes Sem Contato

```http
GET /api/clientes/sem-contato/
```

**Query Parameters:**
| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `dias` | int | 30 | Dias sem contato |

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "nome": "João Silva",
        "telefone": "11999999999",
        "ultimo_contato": "2025-11-01T10:30:00Z",
        "dias_sem_contato": 42
    }
]
```

### Aniversariantes

```http
GET /api/clientes/aniversariantes/
```

**Query Parameters:**
| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `mes` | int | Mês atual | Mês (1-12) |

### Registrar Contato

```http
POST /api/clientes/{id}/registrar-contato/
```

**Request Body:**
```json
{
    "tipo": "contato",
    "canal": "whatsapp",
    "descricao": "Enviei catálogo por WhatsApp",
    "resultado": "Cliente interessado, vai avaliar",
    "proxima_acao": "Ligar para fazer follow-up",
    "data_proxima_acao": "2025-12-20"
}
```

---

## Vendas

### Listar Vendas

```http
GET /api/vendas/
```

**Query Parameters:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `status` | string | orcamento, pendente, aprovada, finalizada, cancelada |
| `tipo_venda` | string | rainbow, acessorio, servico |
| `consultor` | int | ID do consultor |
| `cliente` | int | ID do cliente |
| `ordering` | string | data_venda, -data_venda, valor_total |

**Response (200 OK):**
```json
{
    "count": 50,
    "results": [
        {
            "id": 1,
            "numero": "V2025001",
            "cliente": 1,
            "cliente_nome": "João Silva",
            "consultor": 2,
            "consultor_nome": "Carlos Vendedor",
            "data_venda": "2025-12-01T14:00:00Z",
            "valor_total": "15000.00",
            "status": "finalizada",
            "tipo_venda": "rainbow"
        }
    ]
}
```

### Detalhes da Venda

```http
GET /api/vendas/{id}/
```

**Response (200 OK):**
```json
{
    "id": 1,
    "numero": "V2025001",
    "cliente": 1,
    "cliente_nome": "João Silva",
    "consultor": 2,
    "consultor_nome": "Carlos Vendedor",
    "data_venda": "2025-12-01T14:00:00Z",
    "tipo_venda": "rainbow",
    "valor_produtos": "14000.00",
    "valor_servicos": "500.00",
    "desconto": "500.00",
    "valor_frete": "0.00",
    "valor_total": "14000.00",
    "forma_pagamento": "cartao_credito",
    "parcelas_total": 10,
    "status": "finalizada",
    "observacoes": "Entrega agendada para 15/12",
    "total_pago": "14000.00",
    "saldo_devedor": "0.00",
    "itens": [
        {
            "id": 1,
            "tipo_item": "equipamento",
            "equipamento": 5,
            "produto": null,
            "produto_nome": "Rainbow E2",
            "descricao": "Aspirador Rainbow E2 Completo",
            "quantidade": 1,
            "valor_unitario": "14000.00",
            "desconto": "0.00",
            "subtotal": "14000.00"
        }
    ],
    "parcelas": [
        {
            "id": 1,
            "numero": 1,
            "valor": "1400.00",
            "data_vencimento": "2025-12-15",
            "data_pagamento": "2025-12-14",
            "valor_pago": "1400.00",
            "forma_pagamento": "cartao_credito",
            "status": "pago"
        }
    ]
}
```

### Resumo de Vendas

```http
GET /api/vendas/resumo/
```

**Query Parameters:**
| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `dias` | int | 30 | Período em dias |

**Response (200 OK):**
```json
{
    "periodo_dias": 30,
    "total_vendas": 15,
    "valor_total": "150000.00",
    "por_consultor": [
        {
            "consultor__first_name": "Carlos",
            "consultor__last_name": "Vendedor",
            "quantidade": 8,
            "valor": "85000.00"
        }
    ]
}
```

### Registrar Pagamento

```http
POST /api/vendas/{id}/registrar-pagamento/
```

**Request Body:**
```json
{
    "parcela_id": 5,
    "valor_pago": "1400.00",
    "forma_pagamento": "pix"
}
```

---

## Aluguéis

### Listar Contratos

```http
GET /api/alugueis/
```

**Response (200 OK):**
```json
{
    "count": 25,
    "results": [
        {
            "id": 1,
            "numero": "A2025001",
            "cliente": 10,
            "cliente_nome": "Maria Santos",
            "equipamento": 15,
            "equipamento_serie": "SRX123456",
            "data_inicio": "2025-01-01",
            "data_fim": "2025-12-31",
            "valor_mensal": "500.00",
            "status": "ativo",
            "parcelas_pendentes": 3
        }
    ]
}
```

### Contratos com Parcelas Vencendo

```http
GET /api/alugueis/vencendo/
```

**Query Parameters:**
| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `dias` | int | 7 | Próximos X dias |

### Contratos com Parcelas Atrasadas

```http
GET /api/alugueis/atrasados/
```

---

## Financeiro

### Contas a Receber

```http
GET /api/contas-receber/
GET /api/contas-receber/vencidas/
POST /api/contas-receber/{id}/baixar/
```

### Contas a Pagar

```http
GET /api/contas-pagar/
GET /api/contas-pagar/vencidas/
```

---

## Agenda

### Agendamentos

```http
GET /api/agendamentos/
GET /api/agendamentos/hoje/
GET /api/agendamentos/semana/
POST /api/agendamentos/
```

**Request Body (POST):**
```json
{
    "titulo": "Demonstração Rainbow",
    "tipo": "demonstracao",
    "cliente": 1,
    "responsavel": 2,
    "data_hora": "2025-12-15T14:00:00Z",
    "duracao": 90,
    "local": "Residência do cliente",
    "endereco": "Av. Paulista, 1000 - São Paulo/SP",
    "descricao": "Demonstração do modelo E2"
}
```

---

## Ordens de Serviço

### Listar OS

```http
GET /api/ordens-servico/
GET /api/ordens-servico/abertas/
GET /api/ordens-servico/urgentes/
```

**Response (200 OK):**
```json
{
    "count": 10,
    "results": [
        {
            "id": 1,
            "numero": "OS2025001",
            "cliente": 1,
            "cliente_nome": "João Silva",
            "equipamento": 5,
            "equipamento_serie": "SRX123456",
            "tipo_servico": "manutencao",
            "data_abertura": "2025-12-10T09:00:00Z",
            "status": "em_andamento",
            "valor_total": "350.00",
            "urgente": false
        }
    ]
}
```

---

## Dashboard

### Dados do Dashboard

```http
GET /api/dashboard/
```

**Response (200 OK):**
```json
{
    "clientes_total": 2377,
    "clientes_ativos": 1850,
    "clientes_sem_contato_30d": 234,
    "vendas_mes": 15,
    "vendas_valor_mes": "150000.00",
    "alugueis_ativos": 45,
    "alugueis_vencendo": 8,
    "os_abertas": 12,
    "os_urgentes": 2,
    "contas_receber_vencidas": "25000.00",
    "contas_pagar_vencidas": "5000.00",
    "agendamentos_hoje": 5,
    "tarefas_pendentes": 18
}
```

---

## Assistente de IA

### Enviar Comando

```http
POST /api/ai/comando/
```

**Request Body:**
```json
{
    "mensagem": "Quais clientes não receberam contato nos últimos 15 dias?"
}
```

**Response (200 OK):**
```json
{
    "resposta": "Encontrei 23 clientes sem contato há mais de 15 dias. Os principais são: João Silva (42 dias), Maria Santos (35 dias)...",
    "dados": [
        {
            "id": 1,
            "nome": "João Silva",
            "ultimo_contato": "2025-11-01",
            "dias_sem_contato": 42
        }
    ],
    "funcao_executada": "listar_clientes_sem_contato",
    "parametros": {"dias": 15}
}
```

**Comandos suportados:**
- "Buscar cliente [nome]"
- "Listar clientes sem contato há [X] dias"
- "Quais aluguéis vencem esta semana?"
- "Enviar WhatsApp para [nome]: [mensagem]"
- "Criar agendamento para [data] com [cliente]"
- "Gerar relatório de vendas do mês"
- "Ranking de consultores"
- "Verificar garantia do equipamento [série]"

---

## Webhooks

### WhatsApp Webhook

```http
GET /api/webhooks/whatsapp/   # Verificação
POST /api/webhooks/whatsapp/  # Receber eventos
```

O webhook processa automaticamente:
- Mensagens recebidas
- Status de entrega
- Respostas de botões interativos

---

## Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 400 | Bad Request - Dados inválidos |
| 401 | Unauthorized - Token inválido ou ausente |
| 403 | Forbidden - Sem permissão |
| 404 | Not Found - Recurso não encontrado |
| 429 | Too Many Requests - Rate limit excedido |
| 500 | Internal Server Error |

**Formato de Erro:**
```json
{
    "detail": "Mensagem de erro",
    "code": "codigo_do_erro"
}
```

---

## Rate Limiting

- **Autenticados:** 1000 requisições/hora
- **Não autenticados:** 100 requisições/hora

Headers de resposta:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1702234567
```

---

## Versionamento

A API atual não possui versionamento explícito. Futuras versões serão disponibilizadas em:
- `/api/v2/...`

---

**Documentação Interativa:**
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI Schema: `/api/schema/`
