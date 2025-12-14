# 🌈 Life Rainbow 2.0

Sistema de Gestão Empresarial Inteligente para Life Rainbow - Aspiradores Rainbow.

## 📋 Visão Geral

Sistema completo de CRM, vendas, aluguéis, assistência técnica e automação de WhatsApp com IA integrada.

### ✨ Principais Funcionalidades

- **👥 Gestão de Clientes (CRM)**
  - Cadastro completo com múltiplos endereços
  - Classificação por perfil (Diamante, Ouro, Prata, Bronze)
  - Histórico de interações
  - Alertas de clientes sem contato

- **🔧 Equipamentos Rainbow**
  - Controle de número de série
  - Gestão de garantia
  - Histórico de manutenções
  - Alertas de manutenção preventiva

- **💰 Vendas**
  - Orçamentos e vendas
  - Parcelamento flexível
  - Controle de parcelas
  - Relatórios de performance

- **📦 Aluguéis**
  - Contratos com parcelas automáticas
  - Controle de inadimplência
  - Renovação e devolução
  - **Estrutura normalizada** (não mais 12 colunas separadas!)

- **🔨 Assistência Técnica**
  - Ordens de serviço
  - Controle de peças
  - Técnicos e agendamentos
  - Garantia de serviços

- **💵 Financeiro**
  - Contas a pagar/receber
  - Controle de caixa
  - Plano de contas
  - Relatórios financeiros

- **📅 Agenda**
  - Agendamentos de visitas
  - Follow-ups automáticos
  - Tarefas e lembretes
  - Integração com calendário

- **📲 WhatsApp Business API**
  - Envio de mensagens automáticas
  - Templates aprovados
  - Campanhas em massa
  - Chatbot com IA

- **🤖 Assistente de IA**
  - Comandos em linguagem natural
  - Function Calling com GPT-4
  - Automação de tarefas
  - Relatórios inteligentes

## 🚀 Instalação

### Pré-requisitos

- Python 3.11+
- PostgreSQL 15+
- Redis (para Celery)
- Node.js (opcional, para frontend)

### Configuração Local

```bash
# Clonar repositório
git clone https://github.com/liferainbow/liferainbow.git
cd liferainbow

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Aplicar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

### Acessar

- **API:** http://localhost:8000/api/
- **Admin Django:** http://localhost:8000/admin/
- **Documentação API:** http://localhost:8000/api/docs/

## 📁 Estrutura do Projeto

```
liferainbow/
├── core/                   # Configurações Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── api/                    # API REST
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── clientes/               # Módulo de Clientes
├── equipamentos/           # Módulo de Equipamentos
├── vendas/                 # Módulo de Vendas
├── alugueis/               # Módulo de Aluguéis
├── financeiro/             # Módulo Financeiro
├── agenda/                 # Módulo de Agenda
├── assistencia/            # Módulo de Assistência
├── estoque/                # Módulo de Estoque
├── whatsapp_integration/   # Integração WhatsApp
├── ai_assistant/           # Assistente de IA
├── scripts/                # Scripts utilitários
│   └── migrate_from_mysql.py
├── requirements.txt
├── manage.py
└── README.md
```

## 🔌 API REST

### Autenticação

```bash
# Obter token JWT
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "senha"}'

# Usar token
curl http://localhost:8000/api/clientes/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Endpoints Principais

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/clientes/` | Lista clientes |
| `GET /api/clientes/sem-contato/` | Clientes sem contato |
| `GET /api/vendas/` | Lista vendas |
| `GET /api/vendas/resumo/` | Resumo de vendas |
| `GET /api/alugueis/` | Lista contratos |
| `GET /api/alugueis/vencendo/` | Parcelas vencendo |
| `GET /api/ordens-servico/` | Lista OS |
| `GET /api/dashboard/` | Dados do dashboard |
| `POST /api/ai/comando/` | Comando para IA |

## 🤖 Assistente de IA

### Exemplos de Comandos

```bash
# Enviar comando para IA
curl -X POST http://localhost:8000/api/ai/comando/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "Quais clientes não receberam contato este mês?"}'
```

**Comandos suportados:**

- "Buscar cliente João Silva"
- "Listar clientes sem contato há 30 dias"
- "Quais aluguéis vencem esta semana?"
- "Enviar WhatsApp para Maria: Olá, tudo bem?"
- "Criar agendamento de visita para amanhã às 14h"
- "Gerar relatório de vendas do mês"
- "Ranking de consultores"

## 📲 WhatsApp Business API

### Configuração

1. Criar app no [Meta for Developers](https://developers.facebook.com/)
2. Adicionar produto WhatsApp Business
3. Configurar webhook: `https://seu-dominio.com/api/webhooks/whatsapp/`
4. Copiar Phone Number ID e Access Token para `.env`

### Custos por Mensagem

| Categoria | Custo |
|-----------|-------|
| UTILITY (notificações) | R$ 0,04 |
| MARKETING (promoções) | R$ 0,38 |
| Dentro janela 24h | Grátis |

## 🔄 Migração do Sistema Antigo

```bash
# Migrar dados do MySQL para PostgreSQL
python scripts/migrate_from_mysql.py \
  --mysql-host=localhost \
  --mysql-db=lfrainbo_life \
  --mysql-user=root \
  --mysql-password=senha

# Modo dry-run (simulação)
python scripts/migrate_from_mysql.py --dry-run
```

### O que é Normalizado

**Antes (MySQL):**
```sql
-- 12 colunas para parcelas de aluguel 😱
um_aluguel, dois_aluguel, tres_aluguel, ..., aluguel_doze
```

**Depois (PostgreSQL):**
```python
# Estrutura normalizada ✅
ContratoAluguel
  └── ParcelaAluguel (1..N)
```

## 🚀 Deploy em Produção

### Google Cloud Run

```bash
# Build e deploy
gcloud run deploy liferainbow \
  --source . \
  --region=us-central1 \
  --memory=2Gi \
  --add-cloudsql-instances=PROJECT:REGION:INSTANCE
```

### Variáveis de Ambiente (Produção)

Configure no Cloud Run ou use Secret Manager para:
- `DATABASE_URL`
- `OPENAI_API_KEY`
- `WHATSAPP_ACCESS_TOKEN`
- `SECRET_KEY`

## 📊 Tecnologias

| Categoria | Tecnologia |
|-----------|------------|
| Backend | Django 4.2, Django REST Framework |
| Database | PostgreSQL 15 |
| Cache | Redis |
| Tasks | Celery |
| IA | OpenAI GPT-4o-mini |
| WhatsApp | Meta Cloud API |
| Auth | JWT (SimpleJWT) |
| Docs | drf-spectacular (OpenAPI) |

## 🧪 Testes

```bash
# Rodar todos os testes
python manage.py test

# Com coverage
coverage run manage.py test
coverage report
```

## 📝 Licença

Proprietário - Life Rainbow © 2025

## 👥 Equipe

Desenvolvido para Life Rainbow - Aspiradores Rainbow

---

**Versão:** 2.0.0
**Última Atualização:** Dezembro 2025
