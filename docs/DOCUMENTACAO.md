# 📚 Life Rainbow 2.0 - Documentação Técnica Completa

## Índice

1. [Introdução](#1-introdução)
2. [Requisitos do Sistema](#2-requisitos-do-sistema)
3. [Instalação e Configuração](#3-instalação-e-configuração)
4. [Arquitetura do Sistema](#4-arquitetura-do-sistema)
5. [Módulos do Sistema](#5-módulos-do-sistema)
6. [API REST](#6-api-rest)
7. [Integração WhatsApp Business](#7-integração-whatsapp-business)
8. [Assistente de IA](#8-assistente-de-ia)
9. [Django Admin](#9-django-admin)
10. [Migração de Dados](#10-migração-de-dados)
11. [Deploy em Produção](#11-deploy-em-produção)
12. [Segurança](#12-segurança)
13. [Manutenção e Monitoramento](#13-manutenção-e-monitoramento)
14. [Apêndices](#14-apêndices)

---

## 1. Introdução

### 1.1 Sobre o Sistema

O **Life Rainbow 2.0** é um sistema de gestão empresarial desenvolvido especificamente para a empresa Life Rainbow, especializada em vendas, aluguéis e manutenção de aspiradores Rainbow.

### 1.2 Objetivos

- Centralizar a gestão de clientes (CRM)
- Automatizar processos de vendas e aluguéis
- Integrar comunicação via WhatsApp Business
- Fornecer assistente de IA para comandos em linguagem natural
- Substituir sistema legado PHP/MySQL por arquitetura moderna

### 1.3 Público-Alvo

- Consultores de vendas Life Rainbow
- Equipe administrativa
- Técnicos de manutenção
- Gestores e proprietários

---

## 2. Requisitos do Sistema

### 2.1 Requisitos de Software

| Software | Versão Mínima | Recomendada |
|----------|---------------|-------------|
| Python | 3.10 | 3.11+ |
| PostgreSQL | 14 | 15+ |
| Redis | 6.0 | 7.0+ |
| Node.js (opcional) | 18 | 20+ |

### 2.2 Requisitos de Hardware (Produção)

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 1 GB | 2 GB |
| Disco | 10 GB | 20 GB SSD |

### 2.3 Serviços Externos

| Serviço | Obrigatório | Descrição |
|---------|-------------|-----------|
| OpenAI API | Sim | GPT-4o-mini para assistente de IA |
| WhatsApp Business API | Sim | Envio de mensagens |
| Meta for Developers | Sim | Configuração do WhatsApp |
| Google Cloud (opcional) | Não | Hospedagem recomendada |

---

## 3. Instalação e Configuração

### 3.1 Instalação Local

```bash
# 1. Clonar repositório
git clone https://github.com/liferainbow/liferainbow.git
cd liferainbow

# 2. Criar ambiente virtual
python -m venv venv

# 3. Ativar ambiente
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate   # Windows

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Configurar variáveis de ambiente
cp .env.example .env
nano .env  # Editar com suas configurações

# 6. Criar banco de dados PostgreSQL
createdb liferainbow

# 7. Aplicar migrações
python manage.py migrate

# 8. Criar superusuário
python manage.py createsuperuser

# 9. Iniciar servidor de desenvolvimento
python manage.py runserver
```

### 3.2 Configuração do Arquivo .env

```bash
# =============================================================================
# DJANGO
# =============================================================================
DEBUG=True
SECRET_KEY=gere-uma-chave-secreta-forte-aqui
ALLOWED_HOSTS=localhost,127.0.0.1

# =============================================================================
# DATABASE
# =============================================================================
# Desenvolvimento Local
DATABASE_URL=postgresql://postgres:senha@localhost:5432/liferainbow

# Produção (Cloud SQL)
# DATABASE_URL=postgresql://user:pass@/liferainbow?host=/cloudsql/project:region:instance

# =============================================================================
# OPENAI
# =============================================================================
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini

# =============================================================================
# WHATSAPP BUSINESS API
# =============================================================================
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxx
WHATSAPP_VERIFY_TOKEN=seu-token-de-verificacao-webhook

# =============================================================================
# REDIS (para Celery)
# =============================================================================
REDIS_URL=redis://localhost:6379/0

# =============================================================================
# EMAIL
# =============================================================================
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
EMAIL_USE_TLS=True
```

### 3.3 Configuração do Redis e Celery

```bash
# Iniciar Redis (Docker)
docker run -d -p 6379:6379 redis:7-alpine

# Iniciar Celery Worker
celery -A core worker -l info

# Iniciar Celery Beat (agendamento)
celery -A core beat -l info
```

---

## 4. Arquitetura do Sistema

### 4.1 Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTES                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Mobile  │  │   Web    │  │ WhatsApp │  │  Admin   │        │
│  │   App    │  │   App    │  │  Users   │  │  Panel   │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY / NGINX                         │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DJANGO REST FRAMEWORK                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    API REST (JWT Auth)                   │    │
│  ├──────────┬──────────┬──────────┬──────────┬─────────────┤    │
│  │ Clientes │  Vendas  │ Aluguéis │ Agenda   │ Financeiro  │    │
│  ├──────────┴──────────┴──────────┴──────────┴─────────────┤    │
│  │              WhatsApp Integration Service                │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │                 AI Assistant (OpenAI)                    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │    Redis     │    │   Celery     │
│   Database   │    │    Cache     │    │   Workers    │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 4.2 Padrões de Projeto Utilizados

| Padrão | Uso no Sistema |
|--------|----------------|
| MVC/MVT | Estrutura Django |
| Repository | Services para lógica de negócio |
| Factory | Criação de objetos complexos |
| Observer | Signals do Django |
| Strategy | Diferentes estratégias de envio WhatsApp |

### 4.3 Fluxo de Dados

```
Request HTTP
    │
    ▼
URL Router (urls.py)
    │
    ▼
View/ViewSet (views.py)
    │
    ▼
Serializer (serializers.py) ◄──► Validação
    │
    ▼
Service (services.py) ◄──► Lógica de Negócio
    │
    ▼
Model (models.py) ◄──► ORM
    │
    ▼
PostgreSQL Database
```

---

## 5. Módulos do Sistema

### 5.1 Módulo de Clientes (`clientes/`)

#### Modelos

```python
# Cliente - Entidade principal do CRM
class Cliente(models.Model):
    nome = CharField(max_length=200)
    email = EmailField(blank=True)
    telefone = CharField(max_length=20)
    telefone_secundario = CharField(max_length=20, blank=True)
    whatsapp = CharField(max_length=20)
    cpf = CharField(max_length=14, blank=True)
    data_nascimento = DateField(null=True)
    profissao = CharField(max_length=100, blank=True)
    renda_estimada = DecimalField(null=True)

    # Endereço principal (resumido)
    cidade = CharField(max_length=100, blank=True)
    estado = CharField(max_length=2, blank=True)

    # Classificação
    perfil = CharField(choices=PERFIL_CHOICES, default='standard')
    status = CharField(choices=STATUS_CHOICES, default='prospecto')
    origem = CharField(choices=ORIGEM_CHOICES, default='outro')

    # Rainbow
    possui_rainbow = BooleanField(default=False)
    modelo_rainbow = CharField(max_length=100, blank=True)
    data_compra_rainbow = DateField(null=True)
    interesse_rainbow = CharField(max_length=100, blank=True)

    # Relacionamentos
    consultor = ForeignKey(User, null=True, on_delete=SET_NULL)
    indicado_por = ForeignKey('self', null=True, on_delete=SET_NULL)

    # Controle
    ultimo_contato = DateTimeField(null=True)
    observacoes = TextField(blank=True)
    tags = CharField(max_length=500, blank=True)
    data_cadastro = DateTimeField(auto_now_add=True)
    atualizado_em = DateTimeField(auto_now=True)

# Endereco - Múltiplos endereços por cliente
class Endereco(models.Model):
    cliente = ForeignKey(Cliente, related_name='enderecos')
    tipo = CharField(choices=TIPO_CHOICES)  # residencial/comercial/entrega
    cep = CharField(max_length=9)
    logradouro = CharField(max_length=200)
    numero = CharField(max_length=20)
    complemento = CharField(max_length=100, blank=True)
    bairro = CharField(max_length=100)
    cidade = CharField(max_length=100)
    estado = CharField(max_length=2)
    principal = BooleanField(default=False)
    latitude = DecimalField(null=True)
    longitude = DecimalField(null=True)

# HistoricoInteracao - Registro de contatos
class HistoricoInteracao(models.Model):
    cliente = ForeignKey(Cliente, related_name='historico_interacoes')
    tipo = CharField(choices=TIPO_CHOICES)  # contato/visita/proposta/etc
    canal = CharField(choices=CANAL_CHOICES)  # telefone/whatsapp/email/presencial
    descricao = TextField()
    resultado = TextField(blank=True)
    usuario = ForeignKey(User)
    data_hora = DateTimeField(auto_now_add=True)
    proxima_acao = CharField(max_length=200, blank=True)
    data_proxima_acao = DateField(null=True)
```

#### Perfis de Cliente

| Perfil | Critérios | Benefícios |
|--------|-----------|------------|
| Diamante | 3+ compras Rainbow, alto valor | Prioridade máxima, descontos especiais |
| Ouro | 2 compras ou indicações ativas | Atendimento prioritário |
| Prata | 1 compra Rainbow | Programa de indicação |
| Bronze | Aluguel ativo | Ofertas de upgrade |
| Standard | Prospect ou novo | Campanhas de conversão |

### 5.2 Módulo de Vendas (`vendas/`)

#### Modelos

```python
class Venda(models.Model):
    numero = CharField(max_length=20, unique=True)  # Auto-gerado
    cliente = ForeignKey(Cliente)
    consultor = ForeignKey(User)

    # Tipo e valores
    tipo_venda = CharField(choices=TIPO_CHOICES)  # rainbow/acessorio/servico
    valor_produtos = DecimalField(default=0)
    valor_servicos = DecimalField(default=0)
    desconto = DecimalField(default=0)
    valor_frete = DecimalField(default=0)
    valor_total = DecimalField()

    # Pagamento
    forma_pagamento = CharField(choices=PAGAMENTO_CHOICES)
    parcelas_total = IntegerField(default=1)

    # Equipamento (se venda Rainbow)
    equipamento_principal = ForeignKey(Equipamento, null=True)

    # Status
    status = CharField(choices=STATUS_CHOICES, default='orcamento')
    data_venda = DateTimeField(auto_now_add=True)
    observacoes = TextField(blank=True)

class ItemVenda(models.Model):
    venda = ForeignKey(Venda, related_name='itens')
    tipo_item = CharField(choices=TIPO_CHOICES)  # equipamento/acessorio/servico
    equipamento = ForeignKey(Equipamento, null=True)
    produto = ForeignKey(Produto, null=True)
    descricao = CharField(max_length=200)
    quantidade = IntegerField(default=1)
    valor_unitario = DecimalField()
    desconto = DecimalField(default=0)

class Parcela(models.Model):
    venda = ForeignKey(Venda, related_name='parcelas')
    numero = IntegerField()
    valor = DecimalField()
    data_vencimento = DateField()
    data_pagamento = DateField(null=True)
    valor_pago = DecimalField(null=True)
    forma_pagamento = CharField(choices=PAGAMENTO_CHOICES, blank=True)
    status = CharField(choices=STATUS_CHOICES, default='pendente')
    observacao = TextField(blank=True)
```

#### Fluxo de Venda

```
1. ORÇAMENTO
   └── Cliente solicita proposta
       └── Consultor cria orçamento

2. PENDENTE
   └── Cliente aprova orçamento
       └── Sistema gera parcelas

3. APROVADA
   └── Pagamento inicial confirmado
       └── Equipamento reservado

4. FINALIZADA
   └── Todas parcelas pagas
       └── Equipamento entregue

5. CANCELADA
   └── Cliente desistiu ou inadimplente
       └── Equipamento liberado
```

### 5.3 Módulo de Aluguéis (`alugueis/`)

#### Modelos (NORMALIZADOS!)

```python
class ContratoAluguel(models.Model):
    numero = CharField(max_length=20, unique=True)
    cliente = ForeignKey(Cliente)
    equipamento = ForeignKey(Equipamento, null=True)
    venda_origem = ForeignKey(Venda, null=True)  # Se convertido de venda

    # Período
    data_inicio = DateField()
    data_fim = DateField()
    duracao_meses = IntegerField(default=12)

    # Valores
    valor_mensal = DecimalField()
    caucao = DecimalField(default=0)
    desconto_mensal = DecimalField(default=0)

    # Entrega
    endereco_entrega = TextField(blank=True)

    # Status
    status = CharField(choices=STATUS_CHOICES, default='rascunho')
    motivo_cancelamento = TextField(blank=True)
    observacoes = TextField(blank=True)

    def gerar_parcelas(self):
        """Gera automaticamente todas as parcelas do contrato."""
        from dateutil.relativedelta import relativedelta

        for i in range(self.duracao_meses):
            data_vencimento = self.data_inicio + relativedelta(months=i)
            ParcelaAluguel.objects.create(
                contrato=self,
                numero=i + 1,
                valor=self.valor_mensal - self.desconto_mensal,
                data_vencimento=data_vencimento,
            )

class ParcelaAluguel(models.Model):
    contrato = ForeignKey(ContratoAluguel, related_name='parcelas')
    numero = IntegerField()
    valor = DecimalField()
    data_vencimento = DateField()
    data_pagamento = DateField(null=True)
    valor_pago = DecimalField(null=True)
    status = CharField(choices=STATUS_CHOICES, default='pendente')
    observacao = TextField(blank=True)
```

#### Comparação: Antes vs Depois

**ANTES (Sistema Antigo - MySQL):**
```sql
CREATE TABLE alugueis (
    id INT PRIMARY KEY,
    cliente_id INT,
    valor_mensal DECIMAL(10,2),
    -- 12 colunas para parcelas! 😱
    um_aluguel DECIMAL(10,2),
    dois_aluguel DECIMAL(10,2),
    tres_aluguel DECIMAL(10,2),
    quatro_aluguel DECIMAL(10,2),
    cinco_aluguel DECIMAL(10,2),
    seis_aluguel DECIMAL(10,2),
    sete_aluguel DECIMAL(10,2),
    oito_aluguel DECIMAL(10,2),
    nove_aluguel DECIMAL(10,2),
    dez_aluguel DECIMAL(10,2),
    onze_aluguel DECIMAL(10,2),
    aluguel_doze DECIMAL(10,2)
);
```

**DEPOIS (Sistema Novo - PostgreSQL):**
```sql
-- Tabela de contratos
CREATE TABLE contratos_aluguel (
    id SERIAL PRIMARY KEY,
    cliente_id INT REFERENCES clientes(id),
    valor_mensal DECIMAL(10,2),
    duracao_meses INT DEFAULT 12
);

-- Tabela de parcelas (normalizada!) ✅
CREATE TABLE parcelas_aluguel (
    id SERIAL PRIMARY KEY,
    contrato_id INT REFERENCES contratos_aluguel(id),
    numero INT,
    valor DECIMAL(10,2),
    data_vencimento DATE,
    data_pagamento DATE,
    status VARCHAR(20)
);
```

### 5.4 Módulo Financeiro (`financeiro/`)

#### Modelos

```python
class PlanoConta(models.Model):
    """Plano de contas hierárquico."""
    codigo = CharField(max_length=20)
    nome = CharField(max_length=100)
    tipo = CharField(choices=TIPO_CHOICES)  # receita/despesa
    pai = ForeignKey('self', null=True, related_name='filhos')
    ativo = BooleanField(default=True)

class ContaReceber(models.Model):
    """Contas a receber."""
    cliente = ForeignKey(Cliente)
    categoria = ForeignKey(PlanoConta)
    descricao = CharField(max_length=200)
    valor = DecimalField()
    data_vencimento = DateField()
    data_pagamento = DateField(null=True)
    valor_pago = DecimalField(null=True)
    status = CharField(choices=STATUS_CHOICES, default='pendente')

    # Origem
    venda = ForeignKey(Venda, null=True)
    contrato_aluguel = ForeignKey(ContratoAluguel, null=True)

class ContaPagar(models.Model):
    """Contas a pagar."""
    fornecedor = CharField(max_length=200)
    categoria = ForeignKey(PlanoConta)
    descricao = CharField(max_length=200)
    valor = DecimalField()
    data_vencimento = DateField()
    data_pagamento = DateField(null=True)
    valor_pago = DecimalField(null=True)
    status = CharField(choices=STATUS_CHOICES, default='pendente')

class Caixa(models.Model):
    """Caixas/contas bancárias."""
    nome = CharField(max_length=100)
    tipo = CharField(choices=TIPO_CHOICES)  # caixa/banco/cartao
    saldo = DecimalField(default=0)
    responsavel = ForeignKey(User, null=True)
    ativo = BooleanField(default=True)

class Movimentacao(models.Model):
    """Movimentações financeiras."""
    caixa = ForeignKey(Caixa)
    tipo = CharField(choices=TIPO_CHOICES)  # entrada/saida
    categoria = ForeignKey(PlanoConta, null=True)
    descricao = CharField(max_length=200)
    valor = DecimalField()
    data_hora = DateTimeField(auto_now_add=True)
    saldo_anterior = DecimalField()
    saldo_posterior = DecimalField()

    # Origem
    conta_receber = ForeignKey(ContaReceber, null=True)
    conta_pagar = ForeignKey(ContaPagar, null=True)
```

### 5.5 Módulo de Equipamentos (`equipamentos/`)

```python
class ModeloEquipamento(models.Model):
    """Modelos de aspirador Rainbow."""
    nome = CharField(max_length=100)  # Rainbow E2, SRX, etc
    codigo = CharField(max_length=50)
    tipo = CharField(choices=TIPO_CHOICES)  # aspirador/acessorio
    descricao = TextField(blank=True)
    preco_venda = DecimalField()
    preco_aluguel = DecimalField()
    garantia_meses = IntegerField(default=12)
    ativo = BooleanField(default=True)

class Equipamento(models.Model):
    """Equipamento físico com número de série."""
    modelo = ForeignKey(ModeloEquipamento)
    numero_serie = CharField(max_length=100, unique=True)
    cor = CharField(max_length=50, blank=True)

    # Propriedade
    cliente = ForeignKey(Cliente, null=True)
    status = CharField(choices=STATUS_CHOICES)  # ativo/em_manutencao/inativo
    origem = CharField(choices=ORIGEM_CHOICES)  # venda/aluguel/demonstracao

    # Compra e garantia
    data_compra = DateField(null=True)
    valor_compra = DecimalField(null=True)
    garantia_ate = DateField(null=True)

    # Manutenção
    ultima_manutencao = DateField(null=True)
    proxima_manutencao = DateField(null=True)
    horas_uso = IntegerField(default=0)

class HistoricoManutencao(models.Model):
    """Registro de manutenções."""
    equipamento = ForeignKey(Equipamento, related_name='historico_manutencao')
    tipo = CharField(choices=TIPO_CHOICES)  # preventiva/corretiva/garantia
    descricao = TextField()
    pecas_trocadas = TextField(blank=True)
    valor = DecimalField(default=0)
    tecnico = ForeignKey(User, null=True)
    data_manutencao = DateField()
```

### 5.6 Módulo de Agenda (`agenda/`)

```python
class Agendamento(models.Model):
    """Agendamentos de visitas e compromissos."""
    titulo = CharField(max_length=200)
    tipo = CharField(choices=TIPO_CHOICES)  # visita/demonstracao/entrega/manutencao
    cliente = ForeignKey(Cliente, null=True)
    responsavel = ForeignKey(User)

    # Data e local
    data_hora = DateTimeField()
    duracao = IntegerField(default=60)  # minutos
    local = CharField(max_length=200, blank=True)
    endereco = TextField(blank=True)

    # Vínculos
    venda = ForeignKey(Venda, null=True)
    contrato_aluguel = ForeignKey(ContratoAluguel, null=True)
    ordem_servico = ForeignKey(OrdemServico, null=True)

    # Status
    status = CharField(choices=STATUS_CHOICES, default='agendado')
    descricao = TextField(blank=True)
    resultado = TextField(blank=True)

    # Lembrete
    lembrete_enviado = BooleanField(default=False)
    enviar_lembrete_minutos = IntegerField(default=60)

class FollowUp(models.Model):
    """Follow-ups com clientes."""
    cliente = ForeignKey(Cliente)
    tipo = CharField(choices=TIPO_CHOICES)  # pos_venda/reativacao/indicacao
    descricao = TextField()
    data_prevista = DateField()
    prioridade = CharField(choices=PRIORIDADE_CHOICES, default='media')
    responsavel = ForeignKey(User)
    concluido = BooleanField(default=False)
    data_conclusao = DateTimeField(null=True)
    resultado = TextField(blank=True)

class Tarefa(models.Model):
    """Tarefas gerais."""
    titulo = CharField(max_length=200)
    descricao = TextField(blank=True)
    responsavel = ForeignKey(User, related_name='tarefas')
    criado_por = ForeignKey(User, related_name='tarefas_criadas')
    cliente = ForeignKey(Cliente, null=True)
    data_prazo = DateField(null=True)
    prioridade = CharField(choices=PRIORIDADE_CHOICES, default='media')
    status = CharField(choices=STATUS_CHOICES, default='pendente')
    resultado = TextField(blank=True)
```

### 5.7 Módulo de Assistência (`assistencia/`)

```python
class OrdemServico(models.Model):
    """Ordens de serviço para manutenção."""
    numero = CharField(max_length=20, unique=True)
    cliente = ForeignKey(Cliente)
    equipamento = ForeignKey(Equipamento, null=True)

    # Tipo e problema
    tipo_servico = CharField(choices=TIPO_CHOICES)  # manutencao/reparo/revisao
    defeito_relatado = TextField()
    diagnostico = TextField(blank=True)
    servico_executado = TextField(blank=True)

    # Técnico
    tecnico = ForeignKey(User, null=True)

    # Datas
    data_abertura = DateTimeField(auto_now_add=True)
    data_previsao = DateField(null=True)
    data_conclusao = DateTimeField(null=True)

    # Valores
    valor_mao_obra = DecimalField(default=0)
    valor_pecas = DecimalField(default=0)
    desconto = DecimalField(default=0)
    valor_total = DecimalField(default=0)

    # Status
    status = CharField(choices=STATUS_CHOICES, default='aberta')
    urgente = BooleanField(default=False)
    garantia = BooleanField(default=False)
    observacoes = TextField(blank=True)

class ItemOrdemServico(models.Model):
    """Itens/peças da ordem de serviço."""
    ordem_servico = ForeignKey(OrdemServico, related_name='itens')
    tipo = CharField(choices=TIPO_CHOICES)  # peca/servico
    produto = ForeignKey(Produto, null=True)
    descricao = CharField(max_length=200)
    quantidade = IntegerField(default=1)
    valor_unitario = DecimalField()
```

### 5.8 Módulo de Estoque (`estoque/`)

```python
class Produto(models.Model):
    """Produtos e peças em estoque."""
    codigo = CharField(max_length=50, unique=True)
    codigo_barras = CharField(max_length=50, blank=True)
    nome = CharField(max_length=200)
    descricao = TextField(blank=True)

    # Classificação
    categoria = CharField(choices=CATEGORIA_CHOICES)  # peca/acessorio/consumivel
    tipo = CharField(max_length=100, blank=True)
    marca = CharField(max_length=100, blank=True)
    modelo_compativel = CharField(max_length=200, blank=True)

    # Estoque
    quantidade_atual = IntegerField(default=0)
    estoque_minimo = IntegerField(default=5)
    estoque_maximo = IntegerField(default=100)
    localizacao = CharField(max_length=100, blank=True)

    # Preços
    preco_custo = DecimalField(default=0)
    preco_venda = DecimalField(default=0)
    margem_lucro = DecimalField(default=0)

    ativo = BooleanField(default=True)

class MovimentacaoEstoque(models.Model):
    """Movimentações de estoque."""
    produto = ForeignKey(Produto)
    tipo = CharField(choices=TIPO_CHOICES)  # entrada/saida/ajuste
    quantidade = IntegerField()
    quantidade_anterior = IntegerField()
    quantidade_posterior = IntegerField()
    custo_unitario = DecimalField(null=True)
    motivo = TextField()

    # Origem
    ordem_servico = ForeignKey(OrdemServico, null=True)
    venda = ForeignKey(Venda, null=True)

    usuario = ForeignKey(User)
    data_hora = DateTimeField(auto_now_add=True)

class Inventario(models.Model):
    """Inventários de estoque."""
    produto = ForeignKey(Produto)
    data_inventario = DateField()
    quantidade_sistema = IntegerField()
    quantidade_contada = IntegerField()
    diferenca = IntegerField()
    observacao = TextField(blank=True)
    realizado_por = ForeignKey(User)
    ajuste_realizado = BooleanField(default=False)
```

---

## 6. API REST

### 6.1 Autenticação

O sistema utiliza JWT (JSON Web Tokens) para autenticação.

#### Obter Token

```bash
POST /api/auth/token/
Content-Type: application/json

{
    "username": "admin",
    "password": "sua-senha"
}
```

**Resposta:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Usar Token

```bash
GET /api/clientes/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### Renovar Token

```bash
POST /api/auth/token/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 6.2 Endpoints Disponíveis

#### Clientes

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/clientes/` | Lista clientes (paginado) |
| POST | `/api/clientes/` | Cria cliente |
| GET | `/api/clientes/{id}/` | Detalhes do cliente |
| PUT | `/api/clientes/{id}/` | Atualiza cliente |
| PATCH | `/api/clientes/{id}/` | Atualiza parcial |
| DELETE | `/api/clientes/{id}/` | Remove cliente |
| GET | `/api/clientes/sem-contato/` | Clientes sem contato |
| GET | `/api/clientes/aniversariantes/` | Aniversariantes |
| POST | `/api/clientes/{id}/registrar-contato/` | Registra interação |

**Filtros disponíveis:**
- `?status=ativo`
- `?perfil=diamante`
- `?cidade=São Paulo`
- `?possui_rainbow=true`
- `?search=João`

#### Vendas

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/vendas/` | Lista vendas |
| POST | `/api/vendas/` | Cria venda |
| GET | `/api/vendas/{id}/` | Detalhes da venda |
| GET | `/api/vendas/resumo/` | Resumo de vendas |
| POST | `/api/vendas/{id}/registrar-pagamento/` | Registra pagamento |

#### Aluguéis

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/alugueis/` | Lista contratos |
| POST | `/api/alugueis/` | Cria contrato |
| GET | `/api/alugueis/{id}/` | Detalhes do contrato |
| GET | `/api/alugueis/vencendo/` | Parcelas vencendo |
| GET | `/api/alugueis/atrasados/` | Parcelas atrasadas |

#### Financeiro

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/contas-receber/` | Lista contas a receber |
| GET | `/api/contas-receber/vencidas/` | Contas vencidas |
| POST | `/api/contas-receber/{id}/baixar/` | Baixa conta |
| GET | `/api/contas-pagar/` | Lista contas a pagar |

#### Agenda

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/agendamentos/` | Lista agendamentos |
| GET | `/api/agendamentos/hoje/` | Agendamentos de hoje |
| GET | `/api/agendamentos/semana/` | Agendamentos da semana |

#### Ordens de Serviço

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/ordens-servico/` | Lista OS |
| GET | `/api/ordens-servico/abertas/` | OS abertas |
| GET | `/api/ordens-servico/urgentes/` | OS urgentes |

#### Dashboard e IA

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/dashboard/` | Dados do dashboard |
| POST | `/api/ai/comando/` | Comando para IA |

### 6.3 Paginação

Todos os endpoints de listagem são paginados:

```json
{
    "count": 150,
    "next": "http://api/clientes/?page=2",
    "previous": null,
    "results": [...]
}
```

**Parâmetros:**
- `?page=2` - Página específica
- `?page_size=50` - Itens por página (máx 100)

### 6.4 Ordenação

```
GET /api/clientes/?ordering=-data_cadastro  # Mais recentes primeiro
GET /api/clientes/?ordering=nome            # Ordem alfabética
```

### 6.5 Busca

```
GET /api/clientes/?search=João Silva
GET /api/equipamentos/?search=SRX123456
```

---

## 7. Integração WhatsApp Business

### 7.1 Configuração Inicial

1. Acesse [Meta for Developers](https://developers.facebook.com/)
2. Crie um App do tipo Business
3. Adicione o produto WhatsApp
4. Configure o número de telefone de teste
5. Obtenha o `Phone Number ID` e `Access Token`

### 7.2 Configuração do Webhook

**URL do Webhook:**
```
https://seu-dominio.com/api/webhooks/whatsapp/
```

**Verificação:**
O sistema responde automaticamente ao desafio de verificação do Facebook.

### 7.3 Tipos de Mensagens Suportadas

#### Mensagem de Texto
```python
await whatsapp_service.enviar_mensagem_texto(
    telefone="5511999999999",
    texto="Olá! Como posso ajudar?"
)
```

#### Mensagem com Template
```python
await whatsapp_service.enviar_template(
    telefone="5511999999999",
    template_name="confirmacao_agendamento",
    variaveis=["João", "15/12/2025", "14:00"]
)
```

#### Mensagem com Imagem
```python
await whatsapp_service.enviar_imagem(
    telefone="5511999999999",
    imagem_url="https://exemplo.com/imagem.jpg",
    caption="Veja nosso novo modelo!"
)
```

#### Mensagem com Áudio (TTS)
```python
await whatsapp_service.enviar_audio(
    telefone="5511999999999",
    texto="Olá João, seu agendamento foi confirmado para amanhã às 14 horas."
)
```

#### Botões Interativos
```python
await whatsapp_service.enviar_botoes_interativos(
    telefone="5511999999999",
    texto_header="Confirmação",
    texto_body="Deseja confirmar seu agendamento?",
    botoes=[
        {"id": "sim", "titulo": "Sim, confirmar"},
        {"id": "nao", "titulo": "Não, reagendar"},
        {"id": "cancelar", "titulo": "Cancelar"}
    ]
)
```

#### Lista de Opções
```python
await whatsapp_service.enviar_lista(
    telefone="5511999999999",
    texto_header="Menu",
    texto_body="Escolha uma opção:",
    texto_botao="Ver opções",
    secoes=[
        {
            "titulo": "Vendas",
            "itens": [
                {"id": "orcamento", "titulo": "Solicitar orçamento"},
                {"id": "catalogo", "titulo": "Ver catálogo"}
            ]
        },
        {
            "titulo": "Suporte",
            "itens": [
                {"id": "manutencao", "titulo": "Agendar manutenção"},
                {"id": "duvida", "titulo": "Tirar dúvida"}
            ]
        }
    ]
)
```

### 7.4 Templates

#### Categorias e Custos

| Categoria | Uso | Custo |
|-----------|-----|-------|
| UTILITY | Notificações, confirmações | R$ 0,04 |
| MARKETING | Promoções, campanhas | R$ 0,38 |
| AUTHENTICATION | Códigos de verificação | R$ 0,04 |

#### Criando um Template

1. Acesse o WhatsApp Manager no Meta Business Suite
2. Vá em "Message Templates"
3. Crie o template com variáveis `{{1}}`, `{{2}}`, etc.
4. Aguarde aprovação (24-48h)
5. Cadastre no sistema via Admin

### 7.5 Campanhas em Massa

```python
await whatsapp_service.enviar_campanha(
    destinatarios=[
        {"telefone": "5511999999999", "variaveis": ["João"]},
        {"telefone": "5511888888888", "variaveis": ["Maria"]},
    ],
    template_name="promocao_natal"
)
```

**Limites:**
- 80 mensagens por segundo (máximo)
- Sistema usa 1 mensagem a cada 100ms (conservador)

---

## 8. Assistente de IA

### 8.1 Arquitetura

O assistente utiliza **OpenAI Function Calling** para interpretar comandos em linguagem natural e executar ações no sistema.

```
Usuário → "Quais clientes não ligamos este mês?"
    │
    ▼
OpenAI GPT-4o-mini
    │
    ▼
Function Calling: listar_clientes_sem_contato(dias=30)
    │
    ▼
Execução da função no Django
    │
    ▼
Resposta formatada para o usuário
```

### 8.2 Funções Disponíveis

| Função | Parâmetros | Descrição |
|--------|------------|-----------|
| `buscar_cliente` | nome, telefone, email | Busca cliente por critérios |
| `listar_clientes_sem_contato` | dias | Lista clientes sem contato |
| `listar_clientes_sem_manutencao` | meses | Clientes sem manutenção |
| `registrar_contato` | cliente_id, tipo, canal, descricao | Registra interação |
| `listar_vendas_periodo` | data_inicio, data_fim | Vendas no período |
| `listar_contas_vencidas` | tipo | Contas a receber/pagar vencidas |
| `calcular_resumo_financeiro` | periodo_dias | Resumo financeiro |
| `listar_alugueis_vencendo` | dias | Aluguéis com parcelas vencendo |
| `listar_parcelas_atrasadas` | - | Parcelas de aluguel atrasadas |
| `listar_agendamentos` | data_inicio, data_fim | Agendamentos do período |
| `criar_agendamento` | cliente_id, tipo, data_hora, descricao | Cria agendamento |
| `enviar_whatsapp` | telefone, mensagem | Envia mensagem WhatsApp |
| `enviar_campanha_whatsapp` | template, clientes | Envia campanha |
| `gerar_relatorio_vendas` | periodo_dias | Gera relatório de vendas |
| `ranking_consultores` | periodo_dias | Ranking de vendas |
| `buscar_equipamento` | numero_serie | Busca equipamento |
| `verificar_garantia` | numero_serie | Verifica garantia |

### 8.3 Exemplos de Comandos

```
"Buscar cliente João Silva"
"Quais clientes não receberam contato nos últimos 30 dias?"
"Listar vendas do mês passado"
"Quais aluguéis vencem esta semana?"
"Enviar WhatsApp para Maria: Olá, sua manutenção está agendada!"
"Criar agendamento de visita para amanhã às 14h com o cliente José"
"Gerar relatório de vendas do último trimestre"
"Ranking de vendas dos consultores este mês"
"Verificar garantia do equipamento SRX123456"
```

### 8.4 Uso via API

```bash
curl -X POST http://localhost:8000/api/ai/comando/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "Quais clientes estão sem contato há mais de 15 dias?"}'
```

**Resposta:**
```json
{
    "resposta": "Encontrei 23 clientes sem contato há mais de 15 dias...",
    "dados": [
        {"id": 1, "nome": "João Silva", "ultimo_contato": "2025-11-28"},
        ...
    ],
    "funcao_executada": "listar_clientes_sem_contato"
}
```

---

## 9. Django Admin

### 9.1 Acesso

**URL:** `http://localhost:8000/admin/`

### 9.2 Funcionalidades por Módulo

#### Clientes
- Lista com badges de perfil e status
- Filtros por perfil, status, cidade, consultor
- Busca por nome, email, telefone, CPF
- Ação em massa: marcar ativo/inativo
- Inline de endereços e histórico de interações

#### Vendas
- Lista com valor total e saldo devedor
- Filtros por status, tipo, consultor
- Inline de itens e parcelas
- Ação: aprovar/cancelar vendas

#### Aluguéis
- Lista com status de parcelas
- Filtros por status, cliente
- Inline de parcelas e histórico
- Ação: gerar parcelas, ativar, cancelar

#### Financeiro
- Contas a receber/pagar com alertas de atraso
- Movimentações com cores por tipo
- Ação: baixar contas

#### Ordens de Serviço
- Badge de urgência
- Filtros por status, técnico, urgente
- Inline de itens/peças
- Ação: concluir, entregar

### 9.3 Customizações

Todos os módulos possuem:
- **Badges coloridos** para status
- **Formatação de valores** em Real
- **Cálculos automáticos** (saldo devedor, dias de atraso)
- **Ações em massa** para operações comuns
- **Filtros avançados** por data, status, relacionamentos

---

## 10. Migração de Dados

### 10.1 Script de Migração

O script `scripts/migrate_from_mysql.py` migra dados do sistema antigo.

### 10.2 Uso

```bash
# Modo dry-run (simulação)
python scripts/migrate_from_mysql.py \
  --mysql-host=localhost \
  --mysql-db=lfrainbo_life \
  --mysql-user=root \
  --mysql-password=senha \
  --dry-run

# Execução real
python scripts/migrate_from_mysql.py \
  --mysql-host=localhost \
  --mysql-db=lfrainbo_life \
  --mysql-user=root \
  --mysql-password=senha
```

### 10.3 O que é Migrado

| Tabela MySQL | Modelo Django | Observações |
|--------------|---------------|-------------|
| clientes | Cliente, Endereco | Endereço separado |
| alugueis | ContratoAluguel, ParcelaAluguel | **NORMALIZADO!** |
| vendas | Venda | Parcelas criadas separadamente |

### 10.4 Normalização de Aluguéis

O script converte automaticamente:

```
um_aluguel=150.00    →  ParcelaAluguel(numero=1, valor=150, status='pago')
dois_aluguel=NULL    →  ParcelaAluguel(numero=2, valor=150, status='pendente')
...
```

---

## 11. Deploy em Produção

### 11.1 Google Cloud Run

```bash
# Build e deploy
gcloud run deploy liferainbow \
  --source . \
  --region=us-central1 \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=0 \
  --max-instances=10 \
  --add-cloudsql-instances=PROJECT:REGION:INSTANCE \
  --set-env-vars="DEBUG=False" \
  --set-secrets="SECRET_KEY=secret-key:latest,DATABASE_URL=database-url:latest"
```

### 11.2 Variáveis de Ambiente (Produção)

Configure via Secret Manager:
- `SECRET_KEY`
- `DATABASE_URL`
- `OPENAI_API_KEY`
- `WHATSAPP_ACCESS_TOKEN`
- `REDIS_URL`

### 11.3 Checklist de Deploy

- [ ] Banco de dados PostgreSQL criado
- [ ] Migrações aplicadas
- [ ] Superusuário criado
- [ ] Variáveis de ambiente configuradas
- [ ] Redis configurado (Memorystore)
- [ ] Webhook WhatsApp configurado
- [ ] SSL/HTTPS habilitado
- [ ] Domínio customizado configurado
- [ ] Monitoramento configurado (Sentry)

---

## 12. Segurança

### 12.1 Autenticação

- JWT com expiração de 1 hora (access) e 7 dias (refresh)
- Senhas hasheadas com PBKDF2
- Proteção contra força bruta

### 12.2 Autorização

- Todas as views protegidas com `IsAuthenticated`
- Permissões granulares por modelo
- Auditoria de ações (TODO)

### 12.3 Proteções

- CSRF habilitado
- CORS configurado
- SQL Injection prevenido (ORM)
- XSS prevenido (templates)
- Dados sensíveis em variáveis de ambiente

### 12.4 Boas Práticas

- Nunca commitar `.env`
- Rotacionar tokens periodicamente
- Logs não contêm dados sensíveis
- HTTPS obrigatório em produção

---

## 13. Manutenção e Monitoramento

### 13.1 Logs

```bash
# Desenvolvimento
python manage.py runserver

# Produção (Cloud Run)
gcloud run logs read --service=liferainbow --region=us-central1
```

### 13.2 Monitoramento

**Recomendado:** Sentry para erros
```python
# settings.py
import sentry_sdk
sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN'))
```

### 13.3 Backup

**PostgreSQL:**
```bash
pg_dump -h HOST -U USER -d liferainbow > backup_$(date +%Y%m%d).sql
```

**Cloud SQL:**
```bash
gcloud sql backups create --instance=INSTANCE
```

### 13.4 Tarefas de Manutenção

| Tarefa | Frequência | Comando |
|--------|------------|---------|
| Limpar sessões expiradas | Diária | `python manage.py clearsessions` |
| Backup do banco | Diária | pg_dump |
| Renovar tokens WhatsApp | Mensal | Manual |
| Atualizar dependências | Mensal | `pip install -U -r requirements.txt` |

---

## 14. Apêndices

### 14.1 Glossário

| Termo | Definição |
|-------|-----------|
| Rainbow | Marca de aspiradores vendida pela Life Rainbow |
| Consultor | Vendedor/representante da Life Rainbow |
| Caução | Depósito de segurança em contratos de aluguel |
| OS | Ordem de Serviço para manutenção |
| Follow-up | Acompanhamento pós-venda |
| Template | Mensagem pré-aprovada do WhatsApp |

### 14.2 Códigos de Status

#### Cliente
- `prospecto` - Lead, ainda não comprou
- `ativo` - Cliente ativo
- `inativo` - Sem atividade recente
- `perdido` - Cliente perdido para concorrência

#### Venda
- `orcamento` - Proposta inicial
- `pendente` - Aguardando aprovação/pagamento
- `aprovada` - Pagamento confirmado
- `finalizada` - Entregue e concluída
- `cancelada` - Cancelada

#### Aluguel
- `rascunho` - Em elaboração
- `ativo` - Contrato vigente
- `suspenso` - Temporariamente suspenso
- `finalizado` - Concluído normalmente
- `cancelado` - Cancelado

#### Ordem de Serviço
- `aberta` - Aguardando atendimento
- `em_andamento` - Em execução
- `aguardando_peca` - Aguardando peças
- `aguardando_aprovacao` - Aguardando aprovação do orçamento
- `concluida` - Serviço finalizado
- `entregue` - Equipamento devolvido ao cliente
- `cancelada` - OS cancelada

### 14.3 Referências

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp/)
- [OpenAI API](https://platform.openai.com/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**Versão do Documento:** 1.0
**Última Atualização:** Dezembro 2025
**Autor:** Equipe de Desenvolvimento Life Rainbow
