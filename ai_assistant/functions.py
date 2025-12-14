"""
=============================================================================
LIFE RAINBOW 2.0 - Funções para Function Calling da IA
Implementações das funções que a IA pode chamar
=============================================================================
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


# =============================================================================
# FUNÇÕES DE CLIENTES
# =============================================================================

async def buscar_cliente(termo: str) -> Dict[str, Any]:
    """
    Busca cliente por nome, telefone ou CPF.
    """
    from clientes.models import Cliente

    clientes = Cliente.objects.filter(
        Q(nome__icontains=termo) |
        Q(telefone__icontains=termo) |
        Q(cpf_cnpj__icontains=termo)
    ).select_related('consultor_responsavel')[:10]

    if not clientes:
        return {"encontrado": False, "mensagem": f"Nenhum cliente encontrado para '{termo}'"}

    resultados = []
    for c in clientes:
        resultados.append({
            "id": c.id,
            "nome": c.nome,
            "telefone": c.telefone,
            "email": c.email,
            "perfil": c.get_perfil_display(),
            "status": c.get_status_display(),
            "consultor": c.consultor_responsavel.get_full_name() if c.consultor_responsavel else None,
            "possui_rainbow": c.possui_rainbow,
            "ultimo_contato": c.data_ultimo_contato.strftime("%d/%m/%Y") if c.data_ultimo_contato else "Nunca",
            "proxima_ligacao": c.data_proxima_ligacao.strftime("%d/%m/%Y") if c.data_proxima_ligacao else None,
        })

    return {
        "encontrado": True,
        "quantidade": len(resultados),
        "clientes": resultados
    }


async def listar_clientes_sem_contato(
    dias: int = 30,
    consultor: str = None,
    limite: int = 20
) -> Dict[str, Any]:
    """
    Lista clientes sem contato há X dias.
    """
    from clientes.models import Cliente

    data_limite = timezone.now() - timedelta(days=dias)

    query = Cliente.objects.filter(
        Q(data_ultimo_contato__lt=data_limite) |
        Q(data_ultimo_contato__isnull=True),
        status='ativo'
    ).select_related('consultor_responsavel')

    if consultor:
        query = query.filter(
            consultor_responsavel__first_name__icontains=consultor
        )

    clientes = query.order_by('data_ultimo_contato')[:limite]

    resultados = []
    for c in clientes:
        dias_sem_contato = c.dias_sem_contato or "Nunca contatado"
        resultados.append({
            "id": c.id,
            "nome": c.nome,
            "telefone": c.telefone,
            "perfil": c.get_perfil_display(),
            "dias_sem_contato": dias_sem_contato,
            "consultor": c.consultor_responsavel.get_full_name() if c.consultor_responsavel else "Não atribuído",
        })

    return {
        "criterio": f"Sem contato há mais de {dias} dias",
        "quantidade": len(resultados),
        "clientes": resultados
    }


async def listar_clientes_sem_manutencao(
    dias_atraso: int = 0,
    limite: int = 20
) -> Dict[str, Any]:
    """
    Lista clientes com equipamentos precisando de manutenção.
    """
    from equipamentos.models import Equipamento
    from clientes.models import Cliente

    data_limite = timezone.now().date() + timedelta(days=dias_atraso)

    equipamentos = Equipamento.objects.filter(
        data_proxima_manutencao__lte=data_limite,
        status='vendido',
        cliente__isnull=False
    ).select_related('cliente', 'modelo')[:limite]

    resultados = []
    for eq in equipamentos:
        dias = (timezone.now().date() - eq.data_proxima_manutencao).days
        resultados.append({
            "cliente_id": eq.cliente.id,
            "cliente_nome": eq.cliente.nome,
            "cliente_telefone": eq.cliente.telefone,
            "equipamento": eq.modelo.nome,
            "numero_serie": eq.numero_serie,
            "ultima_manutencao": eq.data_ultima_manutencao.strftime("%d/%m/%Y") if eq.data_ultima_manutencao else "Nunca",
            "dias_atraso": dias if dias > 0 else 0,
            "data_prevista": eq.data_proxima_manutencao.strftime("%d/%m/%Y"),
        })

    return {
        "criterio": f"Manutenção atrasada ou próxima ({dias_atraso} dias de tolerância)",
        "quantidade": len(resultados),
        "equipamentos": resultados
    }


async def registrar_contato(
    cliente_id: int,
    tipo: str,
    descricao: str,
    resultado: str = None,
    proxima_acao: str = None,
    data_proxima_acao: str = None,
    usuario: Any = None
) -> Dict[str, Any]:
    """
    Registra um contato/interação com cliente.
    """
    from clientes.models import Cliente, HistoricoInteracao

    try:
        cliente = Cliente.objects.get(id=cliente_id)

        interacao = HistoricoInteracao.objects.create(
            cliente=cliente,
            tipo=tipo,
            direcao='saida',
            descricao=descricao,
            resultado=resultado,
            proxima_acao=proxima_acao,
            data_proxima_acao=datetime.strptime(data_proxima_acao, "%Y-%m-%d").date() if data_proxima_acao else None,
            usuario=usuario,
            gerado_por_ia=True
        )

        # Atualizar data do último contato
        cliente.data_ultimo_contato = timezone.now()
        if data_proxima_acao:
            cliente.data_proxima_ligacao = datetime.strptime(data_proxima_acao, "%Y-%m-%d").date()
        cliente.save()

        return {
            "sucesso": True,
            "mensagem": f"Contato registrado para {cliente.nome}",
            "interacao_id": interacao.id
        }

    except Cliente.DoesNotExist:
        return {"sucesso": False, "erro": f"Cliente ID {cliente_id} não encontrado"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


# =============================================================================
# FUNÇÕES DE VENDAS E FINANCEIRO
# =============================================================================

async def listar_vendas_periodo(
    data_inicio: str,
    data_fim: str,
    consultor: str = None,
    status: str = None
) -> Dict[str, Any]:
    """
    Lista vendas de um período.
    """
    from vendas.models import Venda

    dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
    dt_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()

    query = Venda.objects.filter(
        data_venda__gte=dt_inicio,
        data_venda__lte=dt_fim
    ).select_related('cliente', 'vendedor')

    if consultor:
        query = query.filter(vendedor__first_name__icontains=consultor)
    if status:
        query = query.filter(status=status)

    vendas = query.order_by('-data_venda')[:50]

    resultados = []
    total_valor = 0
    total_pontos = 0

    for v in vendas:
        total_valor += float(v.valor_total)
        total_pontos += float(v.pontos)
        resultados.append({
            "numero": v.numero,
            "cliente": v.cliente.nome,
            "data": v.data_venda.strftime("%d/%m/%Y"),
            "valor": float(v.valor_total),
            "status": v.get_status_display(),
            "vendedor": v.vendedor.get_full_name() if v.vendedor else None,
            "pontos": float(v.pontos),
        })

    return {
        "periodo": f"{data_inicio} a {data_fim}",
        "quantidade": len(resultados),
        "total_valor": total_valor,
        "total_pontos": total_pontos,
        "vendas": resultados
    }


async def listar_contas_vencidas(
    dias_atraso: int = 1,
    consultor: str = None,
    limite: int = 50
) -> Dict[str, Any]:
    """
    Lista contas a receber vencidas.
    """
    from financeiro.models import ContaReceber

    data_limite = timezone.now().date() - timedelta(days=dias_atraso)

    query = ContaReceber.objects.filter(
        data_vencimento__lt=data_limite,
        status='pendente'
    ).select_related('cliente', 'consultor')

    if consultor:
        query = query.filter(consultor__first_name__icontains=consultor)

    contas = query.order_by('data_vencimento')[:limite]

    resultados = []
    total_valor = 0

    for c in contas:
        dias = c.dias_atraso
        total_valor += float(c.valor)
        resultados.append({
            "id": c.id,
            "descricao": c.descricao,
            "cliente": c.cliente.nome if c.cliente else "N/A",
            "telefone": c.cliente.telefone if c.cliente else "N/A",
            "valor": float(c.valor),
            "vencimento": c.data_vencimento.strftime("%d/%m/%Y"),
            "dias_atraso": dias,
            "consultor": c.consultor.get_full_name() if c.consultor else "N/A",
        })

    return {
        "criterio": f"Vencidas há mais de {dias_atraso} dias",
        "quantidade": len(resultados),
        "total_valor": total_valor,
        "contas": resultados
    }


async def calcular_resumo_financeiro(mes: int, ano: int) -> Dict[str, Any]:
    """
    Calcula resumo financeiro de um mês.
    """
    from vendas.models import Venda
    from financeiro.models import Movimentacao

    # Vendas do mês
    vendas = Venda.objects.filter(
        data_venda__year=ano,
        data_venda__month=mes,
        status='concluida'
    ).aggregate(
        total_vendas=Sum('valor_total'),
        total_custo=Sum('valor_custo'),
        quantidade=Count('id')
    )

    # Movimentações
    entradas = Movimentacao.objects.filter(
        data__year=ano,
        data__month=mes,
        tipo='entrada'
    ).aggregate(total=Sum('valor'))['total'] or 0

    saidas = Movimentacao.objects.filter(
        data__year=ano,
        data__month=mes,
        tipo='saida'
    ).aggregate(total=Sum('valor'))['total'] or 0

    total_vendas = float(vendas['total_vendas'] or 0)
    total_custo = float(vendas['total_custo'] or 0)
    lucro_bruto = total_vendas - total_custo
    lucro_liquido = float(entradas) - float(saidas)

    return {
        "periodo": f"{mes:02d}/{ano}",
        "vendas": {
            "total": total_vendas,
            "custo": total_custo,
            "lucro_bruto": lucro_bruto,
            "quantidade": vendas['quantidade'] or 0,
            "margem": round((lucro_bruto / total_vendas * 100), 2) if total_vendas > 0 else 0
        },
        "fluxo_caixa": {
            "entradas": float(entradas),
            "saidas": float(saidas),
            "saldo": lucro_liquido
        }
    }


# =============================================================================
# FUNÇÕES DE ALUGUÉIS
# =============================================================================

async def listar_alugueis_vencendo(dias: int = 30) -> Dict[str, Any]:
    """
    Lista contratos de aluguel que vencem nos próximos X dias.
    """
    from alugueis.models import ContratoAluguel

    data_limite = timezone.now().date() + timedelta(days=dias)

    contratos = ContratoAluguel.objects.filter(
        data_fim_prevista__lte=data_limite,
        status='ativo'
    ).select_related('cliente', 'equipamento__modelo')[:50]

    resultados = []
    for c in contratos:
        dias_restantes = (c.data_fim_prevista - timezone.now().date()).days
        resultados.append({
            "numero": c.numero,
            "cliente": c.cliente.nome,
            "telefone": c.cliente.telefone,
            "equipamento": c.equipamento.modelo.nome,
            "valor_mensal": float(c.valor_mensal),
            "meses_pagos": c.meses_pagos,
            "meses_total": c.duracao_meses,
            "data_fim": c.data_fim_prevista.strftime("%d/%m/%Y"),
            "dias_restantes": dias_restantes,
        })

    return {
        "criterio": f"Vencendo nos próximos {dias} dias",
        "quantidade": len(resultados),
        "contratos": resultados
    }


async def listar_parcelas_atrasadas(
    dias_atraso: int = 1,
    limite: int = 50
) -> Dict[str, Any]:
    """
    Lista parcelas de aluguel em atraso.
    """
    from alugueis.models import ParcelaAluguel

    data_limite = timezone.now().date() - timedelta(days=dias_atraso)

    parcelas = ParcelaAluguel.objects.filter(
        data_vencimento__lt=data_limite,
        status='pendente'
    ).select_related('contrato__cliente')[:limite]

    resultados = []
    total_valor = 0

    for p in parcelas:
        dias = p.dias_atraso
        total_valor += float(p.valor)
        resultados.append({
            "contrato": p.contrato.numero,
            "cliente": p.contrato.cliente.nome,
            "telefone": p.contrato.cliente.telefone,
            "parcela": f"{p.numero}/{p.contrato.duracao_meses}",
            "mes_ref": p.mes_referencia,
            "valor": float(p.valor),
            "valor_com_multa": float(p.calcular_valor_com_multa()),
            "vencimento": p.data_vencimento.strftime("%d/%m/%Y"),
            "dias_atraso": dias,
        })

    return {
        "criterio": f"Parcelas com mais de {dias_atraso} dias de atraso",
        "quantidade": len(resultados),
        "total_valor": total_valor,
        "parcelas": resultados
    }


# =============================================================================
# FUNÇÕES DE AGENDA
# =============================================================================

async def listar_agendamentos(
    data: str,
    responsavel: str = None,
    tipo: str = None
) -> Dict[str, Any]:
    """
    Lista agendamentos de uma data/período.
    """
    from agenda.models import Agendamento

    # Interpretar data
    hoje = timezone.now().date()
    if data == 'hoje':
        dt = hoje
    elif data == 'amanha':
        dt = hoje + timedelta(days=1)
    elif data == 'semana':
        dt_inicio = hoje
        dt_fim = hoje + timedelta(days=7)
    else:
        dt = datetime.strptime(data, "%Y-%m-%d").date()
        dt_inicio = dt_fim = dt

    # Query
    if data == 'semana':
        query = Agendamento.objects.filter(
            data__gte=dt_inicio,
            data__lte=dt_fim
        )
    else:
        query = Agendamento.objects.filter(data=dt)

    if responsavel:
        query = query.filter(responsavel__first_name__icontains=responsavel)
    if tipo:
        query = query.filter(tipo=tipo)

    agendamentos = query.select_related('cliente', 'responsavel').order_by('data', 'hora_inicio')

    resultados = []
    for a in agendamentos:
        resultados.append({
            "id": a.id,
            "titulo": a.titulo,
            "tipo": a.get_tipo_display(),
            "cliente": a.cliente.nome,
            "telefone": a.cliente.telefone,
            "data": a.data.strftime("%d/%m/%Y"),
            "hora": a.hora_inicio.strftime("%H:%M"),
            "status": a.get_status_display(),
            "responsavel": a.responsavel.get_full_name() if a.responsavel else "N/A",
            "local": a.local_descricao,
        })

    return {
        "data_consulta": data,
        "quantidade": len(resultados),
        "agendamentos": resultados
    }


async def criar_agendamento(
    cliente_id: int,
    tipo: str,
    data: str,
    hora: str,
    titulo: str,
    responsavel: str = None,
    usuario: Any = None
) -> Dict[str, Any]:
    """
    Cria um novo agendamento.
    """
    from agenda.models import Agendamento
    from clientes.models import Cliente

    try:
        cliente = Cliente.objects.get(id=cliente_id)

        # Buscar responsável
        resp = None
        if responsavel:
            resp = User.objects.filter(first_name__icontains=responsavel).first()
        elif usuario:
            resp = usuario

        agendamento = Agendamento.objects.create(
            cliente=cliente,
            tipo=tipo,
            data=datetime.strptime(data, "%Y-%m-%d").date(),
            hora_inicio=datetime.strptime(hora, "%H:%M").time(),
            titulo=titulo,
            responsavel=resp,
            status='agendado'
        )

        return {
            "sucesso": True,
            "mensagem": f"Agendamento criado: {titulo} para {cliente.nome} em {data} às {hora}",
            "agendamento_id": agendamento.id
        }

    except Cliente.DoesNotExist:
        return {"sucesso": False, "erro": f"Cliente ID {cliente_id} não encontrado"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


# =============================================================================
# FUNÇÕES DE WHATSAPP
# =============================================================================

async def enviar_whatsapp(
    cliente_id: int,
    mensagem: str,
    tipo: str = "texto",
    template_name: str = None,
    usuario: Any = None
) -> Dict[str, Any]:
    """
    Envia mensagem de WhatsApp para um cliente.
    """
    from clientes.models import Cliente
    from whatsapp_integration.services import whatsapp_service

    try:
        cliente = Cliente.objects.get(id=cliente_id)

        if not cliente.whatsapp and not cliente.telefone:
            return {"sucesso": False, "erro": "Cliente não possui telefone cadastrado"}

        telefone = cliente.whatsapp or cliente.telefone

        if tipo == "texto":
            resultado = await whatsapp_service.enviar_mensagem_texto(telefone, mensagem)
        elif tipo == "audio":
            resultado = await whatsapp_service.enviar_audio(telefone, mensagem)
        elif tipo == "template" and template_name:
            resultado = await whatsapp_service.enviar_template(telefone, template_name, [mensagem])
        else:
            resultado = await whatsapp_service.enviar_mensagem_texto(telefone, mensagem)

        if resultado.get('success'):
            return {
                "sucesso": True,
                "mensagem": f"Mensagem enviada para {cliente.nome} ({telefone})",
                "message_id": resultado.get('message_id')
            }
        else:
            return {
                "sucesso": False,
                "erro": resultado.get('error', 'Erro desconhecido')
            }

    except Cliente.DoesNotExist:
        return {"sucesso": False, "erro": f"Cliente ID {cliente_id} não encontrado"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


async def enviar_campanha_whatsapp(
    template_name: str,
    filtro_perfil: List[str] = None,
    filtro_consultor: str = None,
    filtro_dias_sem_contato: int = None
) -> Dict[str, Any]:
    """
    Prepara e envia campanha de WhatsApp.
    """
    from clientes.models import Cliente
    from whatsapp_integration.models import CampanhaMensagem, Template
    from whatsapp_integration.services import whatsapp_service

    try:
        # Verificar template
        template = Template.objects.filter(nome=template_name, status='APPROVED').first()
        if not template:
            return {"sucesso": False, "erro": f"Template '{template_name}' não encontrado ou não aprovado"}

        # Construir query de clientes
        query = Cliente.objects.filter(
            status='ativo',
            aceita_whatsapp=True
        ).exclude(
            Q(telefone__isnull=True) & Q(whatsapp__isnull=True)
        )

        if filtro_perfil:
            query = query.filter(perfil__in=filtro_perfil)

        if filtro_consultor:
            query = query.filter(consultor_responsavel__first_name__icontains=filtro_consultor)

        if filtro_dias_sem_contato:
            data_limite = timezone.now() - timedelta(days=filtro_dias_sem_contato)
            query = query.filter(
                Q(data_ultimo_contato__lt=data_limite) |
                Q(data_ultimo_contato__isnull=True)
            )

        clientes = list(query)

        if not clientes:
            return {"sucesso": False, "erro": "Nenhum cliente encontrado com os filtros aplicados"}

        # Calcular custo estimado
        custo_unitario = 0.04 if template.categoria == 'UTILITY' else 0.38
        custo_estimado = len(clientes) * custo_unitario

        return {
            "sucesso": True,
            "preview": True,
            "mensagem": f"Campanha preparada para {len(clientes)} clientes",
            "template": template_name,
            "categoria": template.get_categoria_display(),
            "total_destinatarios": len(clientes),
            "custo_estimado": f"R$ {custo_estimado:.2f}",
            "filtros_aplicados": {
                "perfil": filtro_perfil,
                "consultor": filtro_consultor,
                "dias_sem_contato": filtro_dias_sem_contato
            },
            "instrucao": "Para confirmar o envio, diga 'confirmar campanha' ou 'enviar campanha'"
        }

    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


# =============================================================================
# FUNÇÕES DE RELATÓRIOS
# =============================================================================

async def gerar_relatorio_vendas(
    mes: int,
    ano: int,
    agrupar_por: str = "consultor"
) -> Dict[str, Any]:
    """
    Gera relatório de vendas agrupado.
    """
    from vendas.models import Venda

    vendas = Venda.objects.filter(
        data_venda__year=ano,
        data_venda__month=mes,
        status='concluida'
    ).select_related('cliente', 'vendedor')

    if agrupar_por == "consultor":
        agrupado = vendas.values('vendedor__first_name', 'vendedor__last_name').annotate(
            total=Sum('valor_total'),
            quantidade=Count('id'),
            pontos=Sum('pontos')
        ).order_by('-total')

        resultados = [
            {
                "consultor": f"{item['vendedor__first_name']} {item['vendedor__last_name']}".strip() or "Não atribuído",
                "total": float(item['total']),
                "quantidade": item['quantidade'],
                "pontos": float(item['pontos'] or 0),
                "ticket_medio": float(item['total']) / item['quantidade'] if item['quantidade'] > 0 else 0
            }
            for item in agrupado
        ]

    elif agrupar_por == "produto":
        from vendas.models import ItemVenda
        agrupado = ItemVenda.objects.filter(
            venda__data_venda__year=ano,
            venda__data_venda__month=mes,
            venda__status='concluida'
        ).values('modelo__nome').annotate(
            total=Sum('valor_total'),
            quantidade=Sum('quantidade')
        ).order_by('-total')

        resultados = [
            {
                "produto": item['modelo__nome'],
                "total": float(item['total']),
                "quantidade": item['quantidade']
            }
            for item in agrupado
        ]

    else:
        resultados = []

    total_geral = sum(r.get('total', 0) for r in resultados)

    return {
        "periodo": f"{mes:02d}/{ano}",
        "agrupamento": agrupar_por,
        "total_geral": total_geral,
        "dados": resultados
    }


async def ranking_consultores(
    mes: int,
    ano: int,
    criterio: str = "valor"
) -> Dict[str, Any]:
    """
    Gera ranking de consultores.
    """
    from vendas.models import Venda

    order_field = {
        "valor": "-total",
        "pontos": "-pontos",
        "quantidade": "-quantidade"
    }.get(criterio, "-total")

    ranking = Venda.objects.filter(
        data_venda__year=ano,
        data_venda__month=mes,
        status='concluida'
    ).values('vendedor__first_name', 'vendedor__last_name').annotate(
        total=Sum('valor_total'),
        quantidade=Count('id'),
        pontos=Sum('pontos')
    ).order_by(order_field)

    resultados = []
    for i, item in enumerate(ranking, 1):
        resultados.append({
            "posicao": i,
            "consultor": f"{item['vendedor__first_name']} {item['vendedor__last_name']}".strip() or "Não atribuído",
            "total_vendas": float(item['total']),
            "quantidade_vendas": item['quantidade'],
            "pontos": float(item['pontos'] or 0)
        })

    return {
        "periodo": f"{mes:02d}/{ano}",
        "criterio": criterio,
        "ranking": resultados
    }


# =============================================================================
# FUNÇÕES DE EQUIPAMENTOS
# =============================================================================

async def buscar_equipamento(numero_serie: str) -> Dict[str, Any]:
    """
    Busca informações de equipamento pelo número de série.
    """
    from equipamentos.models import Equipamento

    equipamento = Equipamento.objects.filter(
        numero_serie__icontains=numero_serie
    ).select_related('modelo', 'cliente').first()

    if not equipamento:
        return {"encontrado": False, "mensagem": f"Equipamento com série '{numero_serie}' não encontrado"}

    return {
        "encontrado": True,
        "equipamento": {
            "id": equipamento.id,
            "modelo": equipamento.modelo.nome,
            "numero_serie": equipamento.numero_serie,
            "status": equipamento.get_status_display(),
            "cliente": equipamento.cliente.nome if equipamento.cliente else None,
            "telefone_cliente": equipamento.cliente.telefone if equipamento.cliente else None,
            "data_venda": equipamento.data_venda.strftime("%d/%m/%Y") if equipamento.data_venda else None,
            "em_garantia": equipamento.em_garantia,
            "fim_garantia": equipamento.data_fim_garantia.strftime("%d/%m/%Y") if equipamento.data_fim_garantia else None,
            "ultima_manutencao": equipamento.data_ultima_manutencao.strftime("%d/%m/%Y") if equipamento.data_ultima_manutencao else None,
            "proxima_manutencao": equipamento.data_proxima_manutencao.strftime("%d/%m/%Y") if equipamento.data_proxima_manutencao else None,
            "manutencao_atrasada": equipamento.manutencao_atrasada,
        }
    }


async def verificar_garantia(numero_serie: str) -> Dict[str, Any]:
    """
    Verifica status de garantia de um equipamento.
    """
    from equipamentos.models import Equipamento

    equipamento = Equipamento.objects.filter(
        numero_serie__icontains=numero_serie
    ).select_related('modelo').first()

    if not equipamento:
        return {"encontrado": False, "mensagem": f"Equipamento com série '{numero_serie}' não encontrado"}

    em_garantia = equipamento.em_garantia

    if equipamento.data_fim_garantia:
        if em_garantia:
            dias_restantes = (equipamento.data_fim_garantia - timezone.now().date()).days
            status_garantia = f"Em garantia - {dias_restantes} dias restantes"
        else:
            dias_vencida = (timezone.now().date() - equipamento.data_fim_garantia).days
            status_garantia = f"Garantia vencida há {dias_vencida} dias"
    else:
        status_garantia = "Sem informação de garantia"

    return {
        "encontrado": True,
        "numero_serie": equipamento.numero_serie,
        "modelo": equipamento.modelo.nome,
        "em_garantia": em_garantia,
        "status": status_garantia,
        "data_venda": equipamento.data_venda.strftime("%d/%m/%Y") if equipamento.data_venda else None,
        "fim_garantia": equipamento.data_fim_garantia.strftime("%d/%m/%Y") if equipamento.data_fim_garantia else None,
        "garantia_meses": equipamento.modelo.garantia_meses
    }
