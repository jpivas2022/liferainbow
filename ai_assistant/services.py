"""
=============================================================================
LIFE RAINBOW 2.0 - Assistente de IA com Function Calling
Integração OpenAI GPT-4o-mini para comandos inteligentes
=============================================================================
"""

import json
import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from openai import OpenAI

logger = logging.getLogger(__name__)


class AIAssistant:
    """
    Assistente de IA com Function Calling para o sistema Life Rainbow.
    Processa comandos em linguagem natural e executa ações no sistema.
    """

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS

        # System prompt para contextualizar a IA
        self.system_prompt = """Você é o assistente inteligente da Life Rainbow, empresa especializada em aspiradores Rainbow e equipamentos de limpeza de alta performance.

Seu papel é:
1. Ajudar a equipe de vendas e atendimento a gerenciar clientes, vendas e aluguéis
2. Responder dúvidas sobre produtos Rainbow
3. Executar ações no sistema quando solicitado
4. Analisar dados e fornecer insights

Regras importantes:
- Sempre seja profissional e cortês
- Ao executar ações, confirme o que foi feito
- Se não tiver certeza, pergunte antes de agir
- Use linguagem clara e objetiva
- Para consultas no banco, retorne dados formatados de forma legível

Contexto do negócio:
- Produtos principais: Aspiradores Rainbow, Power Nozzle, AquaMate, RainMate, MiniJet
- Modelos: Rainbow E2, Rainbow SRX
- Clientes são classificados por perfil: Diamante, Ouro, Prata, Bronze, Standard
- Sistema de pontuação para consultores
- Aluguéis mensais com prazo de 12 meses tipicamente"""

        # Definição das funções disponíveis
        self.tools = self._definir_tools()

    def _definir_tools(self) -> List[Dict]:
        """
        Define todas as funções/tools disponíveis para Function Calling.
        """
        return [
            # ===== CLIENTES =====
            {
                "type": "function",
                "function": {
                    "name": "buscar_cliente",
                    "description": "Busca informações de um cliente pelo nome, telefone ou CPF",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "termo": {
                                "type": "string",
                                "description": "Nome, telefone ou CPF do cliente"
                            }
                        },
                        "required": ["termo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "listar_clientes_sem_contato",
                    "description": "Lista clientes que não recebem contato há X dias",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dias": {
                                "type": "integer",
                                "description": "Número de dias sem contato",
                                "default": 30
                            },
                            "consultor": {
                                "type": "string",
                                "description": "Filtrar por consultor específico (opcional)"
                            },
                            "limite": {
                                "type": "integer",
                                "description": "Máximo de resultados",
                                "default": 20
                            }
                        },
                        "required": ["dias"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "listar_clientes_sem_manutencao",
                    "description": "Lista clientes com equipamentos que precisam de manutenção",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dias_atraso": {
                                "type": "integer",
                                "description": "Dias de atraso na manutenção",
                                "default": 0
                            },
                            "limite": {
                                "type": "integer",
                                "description": "Máximo de resultados",
                                "default": 20
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "registrar_contato",
                    "description": "Registra um contato/interação com o cliente",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cliente_id": {
                                "type": "integer",
                                "description": "ID do cliente"
                            },
                            "tipo": {
                                "type": "string",
                                "enum": ["ligacao", "whatsapp", "email", "visita"],
                                "description": "Tipo de contato"
                            },
                            "descricao": {
                                "type": "string",
                                "description": "Descrição/resumo do contato"
                            },
                            "resultado": {
                                "type": "string",
                                "description": "Resultado do contato"
                            },
                            "proxima_acao": {
                                "type": "string",
                                "description": "Próxima ação a ser tomada"
                            },
                            "data_proxima_acao": {
                                "type": "string",
                                "description": "Data da próxima ação (YYYY-MM-DD)"
                            }
                        },
                        "required": ["cliente_id", "tipo", "descricao"]
                    }
                }
            },

            # ===== VENDAS E FINANCEIRO =====
            {
                "type": "function",
                "function": {
                    "name": "listar_vendas_periodo",
                    "description": "Lista vendas realizadas em um período",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "data_inicio": {
                                "type": "string",
                                "description": "Data inicial (YYYY-MM-DD)"
                            },
                            "data_fim": {
                                "type": "string",
                                "description": "Data final (YYYY-MM-DD)"
                            },
                            "consultor": {
                                "type": "string",
                                "description": "Filtrar por consultor"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["pendente", "concluida", "cancelada"],
                                "description": "Status da venda"
                            }
                        },
                        "required": ["data_inicio", "data_fim"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "listar_contas_vencidas",
                    "description": "Lista contas a receber vencidas",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dias_atraso": {
                                "type": "integer",
                                "description": "Mínimo de dias de atraso",
                                "default": 1
                            },
                            "consultor": {
                                "type": "string",
                                "description": "Filtrar por consultor"
                            },
                            "limite": {
                                "type": "integer",
                                "description": "Máximo de resultados",
                                "default": 50
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calcular_resumo_financeiro",
                    "description": "Calcula resumo financeiro (receitas, despesas, lucro) de um período",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mes": {
                                "type": "integer",
                                "description": "Mês (1-12)"
                            },
                            "ano": {
                                "type": "integer",
                                "description": "Ano (ex: 2024)"
                            }
                        },
                        "required": ["mes", "ano"]
                    }
                }
            },

            # ===== ALUGUÉIS =====
            {
                "type": "function",
                "function": {
                    "name": "listar_alugueis_vencendo",
                    "description": "Lista contratos de aluguel que vencem nos próximos dias",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dias": {
                                "type": "integer",
                                "description": "Dias até o vencimento",
                                "default": 30
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "listar_parcelas_atrasadas",
                    "description": "Lista parcelas de aluguel em atraso",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dias_atraso": {
                                "type": "integer",
                                "description": "Mínimo de dias de atraso",
                                "default": 1
                            },
                            "limite": {
                                "type": "integer",
                                "description": "Máximo de resultados",
                                "default": 50
                            }
                        }
                    }
                }
            },

            # ===== AGENDA =====
            {
                "type": "function",
                "function": {
                    "name": "listar_agendamentos",
                    "description": "Lista agendamentos de um período",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "string",
                                "description": "Data específica (YYYY-MM-DD) ou 'hoje', 'amanha', 'semana'"
                            },
                            "responsavel": {
                                "type": "string",
                                "description": "Filtrar por responsável"
                            },
                            "tipo": {
                                "type": "string",
                                "enum": ["demonstracao", "visita", "manutencao", "entrega"],
                                "description": "Tipo de agendamento"
                            }
                        },
                        "required": ["data"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "criar_agendamento",
                    "description": "Cria um novo agendamento",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cliente_id": {
                                "type": "integer",
                                "description": "ID do cliente"
                            },
                            "tipo": {
                                "type": "string",
                                "enum": ["demonstracao", "visita", "manutencao", "entrega"],
                                "description": "Tipo de agendamento"
                            },
                            "data": {
                                "type": "string",
                                "description": "Data (YYYY-MM-DD)"
                            },
                            "hora": {
                                "type": "string",
                                "description": "Hora (HH:MM)"
                            },
                            "titulo": {
                                "type": "string",
                                "description": "Título/descrição"
                            },
                            "responsavel": {
                                "type": "string",
                                "description": "Nome do responsável"
                            }
                        },
                        "required": ["cliente_id", "tipo", "data", "hora", "titulo"]
                    }
                }
            },

            # ===== WHATSAPP =====
            {
                "type": "function",
                "function": {
                    "name": "enviar_whatsapp",
                    "description": "Envia mensagem de WhatsApp para um cliente",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cliente_id": {
                                "type": "integer",
                                "description": "ID do cliente"
                            },
                            "mensagem": {
                                "type": "string",
                                "description": "Texto da mensagem"
                            },
                            "tipo": {
                                "type": "string",
                                "enum": ["texto", "audio", "template"],
                                "description": "Tipo de mensagem",
                                "default": "texto"
                            },
                            "template_name": {
                                "type": "string",
                                "description": "Nome do template (se tipo=template)"
                            }
                        },
                        "required": ["cliente_id", "mensagem"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "enviar_campanha_whatsapp",
                    "description": "Envia campanha de WhatsApp para múltiplos clientes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "template_name": {
                                "type": "string",
                                "description": "Nome do template aprovado"
                            },
                            "filtro_perfil": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Filtrar por perfis (ex: ['diamante', 'ouro'])"
                            },
                            "filtro_consultor": {
                                "type": "string",
                                "description": "Filtrar por consultor"
                            },
                            "filtro_dias_sem_contato": {
                                "type": "integer",
                                "description": "Clientes sem contato há X dias"
                            }
                        },
                        "required": ["template_name"]
                    }
                }
            },

            # ===== ANÁLISES E RELATÓRIOS =====
            {
                "type": "function",
                "function": {
                    "name": "gerar_relatorio_vendas",
                    "description": "Gera relatório detalhado de vendas",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mes": {
                                "type": "integer",
                                "description": "Mês (1-12)"
                            },
                            "ano": {
                                "type": "integer",
                                "description": "Ano"
                            },
                            "agrupar_por": {
                                "type": "string",
                                "enum": ["consultor", "produto", "cliente", "dia"],
                                "description": "Agrupamento do relatório"
                            }
                        },
                        "required": ["mes", "ano"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ranking_consultores",
                    "description": "Mostra ranking de consultores por vendas/pontos",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mes": {
                                "type": "integer",
                                "description": "Mês (1-12)"
                            },
                            "ano": {
                                "type": "integer",
                                "description": "Ano"
                            },
                            "criterio": {
                                "type": "string",
                                "enum": ["valor", "pontos", "quantidade"],
                                "description": "Critério de ordenação",
                                "default": "valor"
                            }
                        },
                        "required": ["mes", "ano"]
                    }
                }
            },

            # ===== EQUIPAMENTOS =====
            {
                "type": "function",
                "function": {
                    "name": "buscar_equipamento",
                    "description": "Busca informações de um equipamento pelo número de série",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "numero_serie": {
                                "type": "string",
                                "description": "Número de série do equipamento"
                            }
                        },
                        "required": ["numero_serie"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "verificar_garantia",
                    "description": "Verifica status de garantia de um equipamento",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "numero_serie": {
                                "type": "string",
                                "description": "Número de série"
                            }
                        },
                        "required": ["numero_serie"]
                    }
                }
            }
        ]

    async def processar_comando(
        self,
        mensagem: str,
        contexto: Dict[str, Any] = None,
        usuario: Any = None
    ) -> Dict[str, Any]:
        """
        Processa um comando/mensagem do usuário.
        Usa Function Calling para executar ações quando necessário.
        """
        try:
            # Construir mensagens para a API
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]

            # Adicionar contexto se houver
            if contexto:
                context_str = f"\nContexto atual:\n{json.dumps(contexto, ensure_ascii=False, indent=2)}"
                messages[0]["content"] += context_str

            # Adicionar informações do usuário
            if usuario:
                user_info = f"\nUsuário atual: {usuario.get_full_name() or usuario.username}"
                messages[0]["content"] += user_info

            # Adicionar mensagem do usuário
            messages.append({"role": "user", "content": mensagem})

            # Primeira chamada à API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                max_tokens=self.max_tokens
            )

            assistant_message = response.choices[0].message

            # Verificar se há chamadas de função
            if assistant_message.tool_calls:
                # Executar cada função chamada
                tool_results = []

                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    logger.info(f"Executando função: {function_name} com args: {function_args}")

                    # Executar a função
                    result = await self._executar_funcao(function_name, function_args, usuario)

                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": json.dumps(result, ensure_ascii=False, default=str)
                    })

                # Adicionar resultados e fazer segunda chamada
                messages.append(assistant_message)
                messages.extend(tool_results)

                # Segunda chamada para gerar resposta final
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens
                )

                return {
                    "success": True,
                    "resposta": final_response.choices[0].message.content,
                    "funcoes_executadas": [tc.function.name for tc in assistant_message.tool_calls],
                    "tokens_usados": final_response.usage.total_tokens
                }

            else:
                # Resposta direta sem chamada de função
                return {
                    "success": True,
                    "resposta": assistant_message.content,
                    "funcoes_executadas": [],
                    "tokens_usados": response.usage.total_tokens
                }

        except Exception as e:
            logger.error(f"Erro no processamento da IA: {e}")
            return {
                "success": False,
                "error": str(e),
                "resposta": "Desculpe, ocorreu um erro ao processar seu comando. Tente novamente."
            }

    async def _executar_funcao(
        self,
        nome: str,
        args: Dict[str, Any],
        usuario: Any
    ) -> Any:
        """
        Executa a função chamada pela IA.
        """
        # Importar aqui para evitar imports circulares
        from . import functions

        # Mapear nomes para funções reais
        funcoes_disponiveis = {
            'buscar_cliente': functions.buscar_cliente,
            'listar_clientes_sem_contato': functions.listar_clientes_sem_contato,
            'listar_clientes_sem_manutencao': functions.listar_clientes_sem_manutencao,
            'registrar_contato': functions.registrar_contato,
            'listar_vendas_periodo': functions.listar_vendas_periodo,
            'listar_contas_vencidas': functions.listar_contas_vencidas,
            'calcular_resumo_financeiro': functions.calcular_resumo_financeiro,
            'listar_alugueis_vencendo': functions.listar_alugueis_vencendo,
            'listar_parcelas_atrasadas': functions.listar_parcelas_atrasadas,
            'listar_agendamentos': functions.listar_agendamentos,
            'criar_agendamento': functions.criar_agendamento,
            'enviar_whatsapp': functions.enviar_whatsapp,
            'enviar_campanha_whatsapp': functions.enviar_campanha_whatsapp,
            'gerar_relatorio_vendas': functions.gerar_relatorio_vendas,
            'ranking_consultores': functions.ranking_consultores,
            'buscar_equipamento': functions.buscar_equipamento,
            'verificar_garantia': functions.verificar_garantia,
        }

        if nome not in funcoes_disponiveis:
            return {"erro": f"Função '{nome}' não encontrada"}

        try:
            # Adicionar usuário aos argumentos se necessário
            if usuario and nome in ['registrar_contato', 'criar_agendamento', 'enviar_whatsapp']:
                args['usuario'] = usuario

            resultado = await funcoes_disponiveis[nome](**args)
            return resultado

        except Exception as e:
            logger.error(f"Erro ao executar função {nome}: {e}")
            return {"erro": str(e)}


# Instância global do assistente
ai_assistant = AIAssistant()
