# 🌈 Life Rainbow 2.0 - Contexto para Claude

## 📋 Visão Geral do Projeto

**Life Rainbow 2.0** é um sistema de gestão empresarial completo para a empresa Life Rainbow, especializada em vendas e aluguéis de aspiradores Rainbow.

### 🎯 Objetivo Principal
Substituir o sistema legado PHP/MySQL por uma arquitetura moderna Django/PostgreSQL com:
- API REST completa
- Integração WhatsApp Business
- Assistente de IA com GPT-4 Function Calling
- Interface administrativa robusta

### 👤 Cliente
- **Empresa:** Life Rainbow
- **Proprietário:** Jucimar Pivetta
- **Negócio:** Vendas, aluguéis e manutenção de aspiradores Rainbow
- **Base de clientes:** 2.377+ clientes ativos

---

## 🏗️ Arquitetura do Sistema

### Stack Tecnológico
| Camada | Tecnologia |
|--------|------------|
| Backend | Django 4.2 + Django REST Framework |
| Database | PostgreSQL 15 |
| Cache/Queue | Redis + Celery |
| IA | OpenAI GPT-4o-mini (Function Calling) |
| Mensageria | WhatsApp Business Cloud API |
| Auth | JWT (SimpleJWT) |
| Docs | drf-spectacular (OpenAPI/Swagger) |

### Estrutura de Diretórios
```
liferainbow/
├── core/                      # Configurações Django principais
│   ├── settings.py            # Todas as configurações
│   ├── urls.py                # URLs raiz
│   └── wsgi.py                # WSGI para produção
├── api/                       # API REST centralizada
│   ├── serializers.py         # 30+ serializers para todos os módulos
│   ├── views.py               # ViewSets, Dashboard, AI endpoint
│   └── urls.py                # Router com todos os endpoints
├── clientes/                  # Módulo CRM
│   ├── models.py              # Cliente, Endereco, HistoricoInteracao
│   └── admin.py               # Admin com badges e filtros
├── equipamentos/              # Gestão de Equipamentos Rainbow
│   ├── models.py              # ModeloEquipamento, Equipamento, HistoricoManutencao
│   └── admin.py               # Controle de garantia e manutenção
├── vendas/                    # Módulo de Vendas
│   ├── models.py              # Venda, ItemVenda, Parcela
│   └── admin.py               # Controle de parcelas e status
├── alugueis/                  # Contratos de Aluguel (NORMALIZADO!)
│   ├── models.py              # ContratoAluguel, ParcelaAluguel, HistoricoAluguel
│   └── admin.py               # Gestão de contratos
├── financeiro/                # Módulo Financeiro
│   ├── models.py              # PlanoConta, ContaReceber, ContaPagar, Caixa, Movimentacao
│   └── admin.py               # Controle financeiro completo
├── agenda/                    # Agendamentos e Tarefas
│   ├── models.py              # Agendamento, FollowUp, Tarefa
│   └── admin.py               # Gestão de agenda
├── assistencia/               # Assistência Técnica
│   ├── models.py              # OrdemServico, ItemOrdemServico
│   └── admin.py               # Controle de OS
├── estoque/                   # Gestão de Estoque
│   ├── models.py              # Produto, MovimentacaoEstoque, Inventario
│   └── admin.py               # Controle de inventário
├── whatsapp_integration/      # Integração WhatsApp Business
│   ├── models.py              # Conversa, Mensagem, Template, CampanhaMensagem
│   ├── services.py            # WhatsAppService (envio de mensagens)
│   └── admin.py               # Gestão de conversas e campanhas
├── ai_assistant/              # Assistente de IA
│   ├── services.py            # AIAssistant com Function Calling
│   └── functions.py           # 17 funções implementadas
├── scripts/
│   └── migrate_from_mysql.py  # Script de migração do sistema antigo
├── requirements.txt
├── .env.example
├── README.md
└── manage.py
```

---

## 🔑 Informações Críticas

### Normalização de Dados (IMPORTANTE!)
O sistema antigo tinha uma estrutura problemática para aluguéis:
```sql
-- ANTES: 12 colunas separadas para parcelas 😱
um_aluguel, dois_aluguel, tres_aluguel, ..., aluguel_doze
```

**DEPOIS:** Estrutura normalizada com relacionamento 1:N
```python
ContratoAluguel
    └── ParcelaAluguel (numero=1..12)
```

O script `migrate_from_mysql.py` converte automaticamente essa estrutura.

### Classificação de Clientes
| Perfil | Descrição |
|--------|-----------|
| Diamante | Cliente VIP, múltiplas compras |
| Ouro | Cliente frequente |
| Prata | Cliente regular |
| Bronze | Cliente ocasional |
| Standard | Cliente novo |

### Custos WhatsApp Business API
| Categoria | Custo por mensagem |
|-----------|-------------------|
| UTILITY | R$ 0,04 |
| MARKETING | R$ 0,38 |
| Janela 24h | Grátis |

---

## 🔌 Endpoints da API

### Autenticação
```
POST /api/auth/token/          # Obter JWT
POST /api/auth/token/refresh/  # Renovar token
POST /api/auth/token/verify/   # Verificar token
```

### Principais Recursos
```
GET/POST   /api/clientes/                    # CRUD clientes
GET        /api/clientes/sem-contato/        # Clientes sem contato
GET        /api/clientes/aniversariantes/    # Aniversariantes do mês

GET/POST   /api/vendas/                      # CRUD vendas
GET        /api/vendas/resumo/               # Resumo de vendas
POST       /api/vendas/{id}/registrar-pagamento/

GET/POST   /api/alugueis/                    # CRUD contratos
GET        /api/alugueis/vencendo/           # Parcelas vencendo
GET        /api/alugueis/atrasados/          # Parcelas atrasadas

GET/POST   /api/ordens-servico/              # CRUD OS
GET        /api/ordens-servico/abertas/      # OS abertas
GET        /api/ordens-servico/urgentes/     # OS urgentes

GET        /api/dashboard/                   # Dados do dashboard
POST       /api/ai/comando/                  # Comando para IA
POST       /api/webhooks/whatsapp/           # Webhook WhatsApp
```

---

## 🤖 Assistente de IA - Function Calling

### Funções Implementadas (17 total)

| Função | Descrição |
|--------|-----------|
| `buscar_cliente` | Busca cliente por nome, telefone ou email |
| `listar_clientes_sem_contato` | Clientes sem contato há X dias |
| `listar_clientes_sem_manutencao` | Clientes sem manutenção há X meses |
| `registrar_contato` | Registra interação com cliente |
| `listar_vendas_periodo` | Vendas em um período |
| `listar_contas_vencidas` | Contas a receber vencidas |
| `calcular_resumo_financeiro` | Resumo financeiro do período |
| `listar_alugueis_vencendo` | Aluguéis com parcelas vencendo |
| `listar_parcelas_atrasadas` | Parcelas de aluguel atrasadas |
| `listar_agendamentos` | Agendamentos do período |
| `criar_agendamento` | Cria novo agendamento |
| `enviar_whatsapp` | Envia mensagem WhatsApp |
| `enviar_campanha_whatsapp` | Envia campanha em massa |
| `gerar_relatorio_vendas` | Gera relatório de vendas |
| `ranking_consultores` | Ranking de vendas por consultor |
| `buscar_equipamento` | Busca equipamento por série |
| `verificar_garantia` | Verifica status da garantia |

### Exemplo de Uso
```bash
curl -X POST http://localhost:8000/api/ai/comando/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "Quais clientes não receberam contato este mês?"}'
```

---

## ⚙️ Configuração do Ambiente

### Variáveis de Ambiente (.env)
```bash
# Django
DEBUG=True
SECRET_KEY=sua-chave-secreta
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/liferainbow

# OpenAI
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_MODEL=gpt-4o-mini

# WhatsApp Business
WHATSAPP_PHONE_NUMBER_ID=123456789
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxx
WHATSAPP_VERIFY_TOKEN=token-verificacao

# Redis
REDIS_URL=redis://localhost:6379/0
```

### Comandos Úteis
```bash
# Ativar ambiente
source venv/bin/activate

# Rodar servidor
python manage.py runserver

# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Shell Django
python manage.py shell_plus

# Migrar do MySQL
python scripts/migrate_from_mysql.py --mysql-db=lfrainbo_life
```

---

## 📊 Modelos de Dados Principais

### Cliente (clientes/models.py)
```python
class Cliente(models.Model):
    nome = CharField(max_length=200)
    email = EmailField(blank=True)
    telefone = CharField(max_length=20)
    whatsapp = CharField(max_length=20)
    cpf = CharField(max_length=14, blank=True)
    perfil = CharField(choices=PERFIL_CHOICES)  # diamante/ouro/prata/bronze/standard
    status = CharField(choices=STATUS_CHOICES)  # ativo/inativo/prospecto
    possui_rainbow = BooleanField(default=False)
    ultimo_contato = DateTimeField(null=True)
    consultor = ForeignKey(User)
    indicado_por = ForeignKey('self', null=True)
```

### ContratoAluguel (alugueis/models.py)
```python
class ContratoAluguel(models.Model):
    numero = CharField(max_length=20, unique=True)
    cliente = ForeignKey(Cliente)
    equipamento = ForeignKey(Equipamento)
    data_inicio = DateField()
    data_fim = DateField()
    duracao_meses = IntegerField(default=12)
    valor_mensal = DecimalField()
    status = CharField(choices=STATUS_CHOICES)  # ativo/suspenso/finalizado/cancelado

    def gerar_parcelas(self):
        """Gera todas as parcelas do contrato automaticamente."""
        for i in range(self.duracao_meses):
            ParcelaAluguel.objects.create(
                contrato=self,
                numero=i + 1,
                valor=self.valor_mensal,
                data_vencimento=self.data_inicio + relativedelta(months=i),
            )
```

### Venda (vendas/models.py)
```python
class Venda(models.Model):
    numero = CharField(max_length=20, unique=True)
    cliente = ForeignKey(Cliente)
    consultor = ForeignKey(User)
    data_venda = DateTimeField()
    tipo_venda = CharField(choices=TIPO_CHOICES)  # rainbow/acessorio/servico
    valor_total = DecimalField()
    forma_pagamento = CharField(choices=PAGAMENTO_CHOICES)
    status = CharField(choices=STATUS_CHOICES)
```

---

## 🚀 Deploy e Produção

### Google Cloud Run
```bash
gcloud run deploy liferainbow \
  --source . \
  --region=us-central1 \
  --memory=2Gi \
  --add-cloudsql-instances=PROJECT:REGION:INSTANCE
```

### Checklist de Deploy
- [ ] Configurar variáveis de ambiente no Cloud Run
- [ ] Configurar Cloud SQL PostgreSQL
- [ ] Configurar Redis (Memorystore ou externo)
- [ ] Configurar webhook do WhatsApp
- [ ] Rodar migrações
- [ ] Criar superusuário
- [ ] Configurar domínio customizado

---

## 🔗 Relacionamento com iCiclo

Este projeto é **separado** do iCiclo, mas desenvolvido pelo mesmo time:

| Projeto | Localização | Tecnologia |
|---------|-------------|------------|
| iCiclo | `/Users/iciclodev/Development/iciclo-django/` | Django + Flutter |
| Life Rainbow | `/Users/iciclodev/Development/liferainbow/` | Django (API) |

O Life Rainbow pode futuramente ter um app Flutter similar ao iCiclo, mas por enquanto é apenas API + Admin Django.

---

## 📝 Notas Importantes

1. **Nunca commitar .env** - Use .env.example como template
2. **Sempre usar virtualenv** - `source venv/bin/activate`
3. **Testar migração em dry-run primeiro** - `--dry-run`
4. **WhatsApp templates precisam aprovação** - Submeter via Meta Business
5. **Function Calling é assíncrono** - Usar asyncio para AI e WhatsApp

---

## 🆘 Troubleshooting

### Erro de importação circular
Se aparecer erro de import, verificar se não há imports diretos nos models.
Usar strings para ForeignKey: `ForeignKey('app.Model')`

### WhatsApp não envia
1. Verificar se token não expirou
2. Verificar se número está formatado corretamente (apenas dígitos, com DDI)
3. Verificar logs do webhook

### Celery não processa tasks
1. Verificar se Redis está rodando
2. Verificar se worker está ativo: `celery -A core worker -l info`

---

**Última atualização:** Dezembro 2025
**Versão:** 2.0.0
