"""
=============================================================================
LIFE RAINBOW 2.0 - WhatsApp Business API Service
Serviço para envio e recebimento de mensagens via WhatsApp Cloud API
=============================================================================
"""

import httpx
import logging
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.utils import timezone
from gtts import gTTS
import tempfile
import base64

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Serviço para integração com WhatsApp Business Cloud API.
    """

    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }

    # =========================================================================
    # ENVIO DE MENSAGENS
    # =========================================================================

    async def enviar_mensagem_texto(
        self,
        telefone: str,
        texto: str,
        preview_url: bool = False
    ) -> Dict[str, Any]:
        """
        Envia mensagem de texto simples.
        Custo: Gratuito (dentro da janela 24h) ou R$0.04-0.38 (template)
        """
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': self._formatar_telefone(telefone),
            'type': 'text',
            'text': {
                'preview_url': preview_url,
                'body': texto
            }
        }

        return await self._fazer_requisicao(payload)

    async def enviar_template(
        self,
        telefone: str,
        template_name: str,
        variaveis: List[str] = None,
        idioma: str = 'pt_BR'
    ) -> Dict[str, Any]:
        """
        Envia mensagem usando template aprovado.
        Necessário para iniciar conversa ou fora da janela 24h.
        Custo: R$0.04 (UTILITY) ou R$0.38 (MARKETING)
        """
        components = []

        if variaveis:
            parameters = [
                {'type': 'text', 'text': var}
                for var in variaveis
            ]
            components.append({
                'type': 'body',
                'parameters': parameters
            })

        payload = {
            'messaging_product': 'whatsapp',
            'to': self._formatar_telefone(telefone),
            'type': 'template',
            'template': {
                'name': template_name,
                'language': {'code': idioma},
                'components': components
            }
        }

        return await self._fazer_requisicao(payload)

    async def enviar_imagem(
        self,
        telefone: str,
        imagem_url: str,
        caption: str = None
    ) -> Dict[str, Any]:
        """
        Envia imagem (URL pública ou media_id).
        """
        payload = {
            'messaging_product': 'whatsapp',
            'to': self._formatar_telefone(telefone),
            'type': 'image',
            'image': {
                'link': imagem_url,
            }
        }

        if caption:
            payload['image']['caption'] = caption

        return await self._fazer_requisicao(payload)

    async def enviar_audio(
        self,
        telefone: str,
        texto: str
    ) -> Dict[str, Any]:
        """
        Converte texto em áudio (TTS) e envia via WhatsApp.
        Usa Google TTS para gerar o áudio.
        """
        try:
            # Gerar áudio com gTTS
            tts = gTTS(text=texto, lang='pt-br', slow=False)

            # Salvar temporariamente
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as fp:
                tts.save(fp.name)
                fp.seek(0)

                # Upload do áudio para WhatsApp
                media_id = await self._upload_media(fp.name, 'audio/mpeg')

                if media_id:
                    payload = {
                        'messaging_product': 'whatsapp',
                        'to': self._formatar_telefone(telefone),
                        'type': 'audio',
                        'audio': {
                            'id': media_id
                        }
                    }
                    return await self._fazer_requisicao(payload)

        except Exception as e:
            logger.error(f'Erro ao enviar áudio: {e}')
            return {'success': False, 'error': str(e)}

    async def enviar_documento(
        self,
        telefone: str,
        documento_url: str,
        filename: str,
        caption: str = None
    ) -> Dict[str, Any]:
        """
        Envia documento (PDF, etc).
        """
        payload = {
            'messaging_product': 'whatsapp',
            'to': self._formatar_telefone(telefone),
            'type': 'document',
            'document': {
                'link': documento_url,
                'filename': filename
            }
        }

        if caption:
            payload['document']['caption'] = caption

        return await self._fazer_requisicao(payload)

    async def enviar_localizacao(
        self,
        telefone: str,
        latitude: float,
        longitude: float,
        nome: str = None,
        endereco: str = None
    ) -> Dict[str, Any]:
        """
        Envia localização no mapa.
        """
        location = {
            'latitude': latitude,
            'longitude': longitude,
        }

        if nome:
            location['name'] = nome
        if endereco:
            location['address'] = endereco

        payload = {
            'messaging_product': 'whatsapp',
            'to': self._formatar_telefone(telefone),
            'type': 'location',
            'location': location
        }

        return await self._fazer_requisicao(payload)

    async def enviar_botoes_interativos(
        self,
        telefone: str,
        texto_header: str,
        texto_body: str,
        botoes: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Envia mensagem com botões de resposta rápida.
        Máximo 3 botões.
        """
        buttons = [
            {
                'type': 'reply',
                'reply': {
                    'id': btn.get('id', f'btn_{i}'),
                    'title': btn['titulo'][:20]  # Max 20 caracteres
                }
            }
            for i, btn in enumerate(botoes[:3])
        ]

        payload = {
            'messaging_product': 'whatsapp',
            'to': self._formatar_telefone(telefone),
            'type': 'interactive',
            'interactive': {
                'type': 'button',
                'header': {
                    'type': 'text',
                    'text': texto_header
                },
                'body': {
                    'text': texto_body
                },
                'action': {
                    'buttons': buttons
                }
            }
        }

        return await self._fazer_requisicao(payload)

    async def enviar_lista(
        self,
        telefone: str,
        texto_header: str,
        texto_body: str,
        texto_botao: str,
        secoes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Envia mensagem com lista de opções.
        Ideal para menus e seleções.
        """
        sections = []
        for secao in secoes:
            rows = [
                {
                    'id': item.get('id', f'item_{i}'),
                    'title': item['titulo'][:24],  # Max 24 caracteres
                    'description': item.get('descricao', '')[:72]  # Max 72
                }
                for i, item in enumerate(secao.get('itens', []))
            ]
            sections.append({
                'title': secao.get('titulo', 'Opções'),
                'rows': rows
            })

        payload = {
            'messaging_product': 'whatsapp',
            'to': self._formatar_telefone(telefone),
            'type': 'interactive',
            'interactive': {
                'type': 'list',
                'header': {
                    'type': 'text',
                    'text': texto_header
                },
                'body': {
                    'text': texto_body
                },
                'action': {
                    'button': texto_botao[:20],
                    'sections': sections
                }
            }
        }

        return await self._fazer_requisicao(payload)

    # =========================================================================
    # ENVIO EM MASSA
    # =========================================================================

    async def enviar_campanha(
        self,
        destinatarios: List[Dict[str, Any]],
        template_name: str,
        callback_progresso=None
    ) -> Dict[str, Any]:
        """
        Envia mensagem de template para múltiplos destinatários.
        Respeita rate limits do WhatsApp.
        """
        resultados = {
            'total': len(destinatarios),
            'sucesso': 0,
            'falha': 0,
            'erros': []
        }

        for i, dest in enumerate(destinatarios):
            try:
                variaveis = dest.get('variaveis', [])
                resultado = await self.enviar_template(
                    telefone=dest['telefone'],
                    template_name=template_name,
                    variaveis=variaveis
                )

                if resultado.get('success'):
                    resultados['sucesso'] += 1
                else:
                    resultados['falha'] += 1
                    resultados['erros'].append({
                        'telefone': dest['telefone'],
                        'erro': resultado.get('error')
                    })

                # Callback de progresso
                if callback_progresso:
                    callback_progresso(i + 1, len(destinatarios))

                # Rate limiting: 80 mensagens por segundo (máximo)
                # Ser conservador: 1 por 100ms
                import asyncio
                await asyncio.sleep(0.1)

            except Exception as e:
                resultados['falha'] += 1
                resultados['erros'].append({
                    'telefone': dest.get('telefone'),
                    'erro': str(e)
                })

        return resultados

    # =========================================================================
    # WEBHOOK HANDLER
    # =========================================================================

    def processar_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa payload recebido do webhook do WhatsApp.
        Retorna dados estruturados da mensagem/evento.
        """
        try:
            entry = payload.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})

            # Mensagens recebidas
            messages = value.get('messages', [])
            if messages:
                msg = messages[0]
                return self._processar_mensagem_recebida(msg, value)

            # Status de mensagem enviada
            statuses = value.get('statuses', [])
            if statuses:
                status = statuses[0]
                return self._processar_status(status)

            return {'tipo': 'desconhecido', 'payload': payload}

        except Exception as e:
            logger.error(f'Erro ao processar webhook: {e}')
            return {'tipo': 'erro', 'erro': str(e)}

    def _processar_mensagem_recebida(
        self,
        msg: Dict,
        value: Dict
    ) -> Dict[str, Any]:
        """
        Processa mensagem recebida do cliente.
        """
        contacts = value.get('contacts', [{}])[0]

        resultado = {
            'tipo': 'mensagem_recebida',
            'wamid': msg.get('id'),
            'wa_id': msg.get('from'),
            'timestamp': msg.get('timestamp'),
            'tipo_mensagem': msg.get('type'),
            'nome_contato': contacts.get('profile', {}).get('name'),
            'telefone': msg.get('from'),
        }

        # Extrair conteúdo baseado no tipo
        tipo = msg.get('type')

        if tipo == 'text':
            resultado['conteudo'] = msg.get('text', {}).get('body')

        elif tipo == 'image':
            resultado['media_id'] = msg.get('image', {}).get('id')
            resultado['caption'] = msg.get('image', {}).get('caption')
            resultado['mime_type'] = msg.get('image', {}).get('mime_type')

        elif tipo == 'audio':
            resultado['media_id'] = msg.get('audio', {}).get('id')
            resultado['mime_type'] = msg.get('audio', {}).get('mime_type')

        elif tipo == 'document':
            resultado['media_id'] = msg.get('document', {}).get('id')
            resultado['filename'] = msg.get('document', {}).get('filename')
            resultado['mime_type'] = msg.get('document', {}).get('mime_type')

        elif tipo == 'location':
            loc = msg.get('location', {})
            resultado['latitude'] = loc.get('latitude')
            resultado['longitude'] = loc.get('longitude')
            resultado['nome_local'] = loc.get('name')
            resultado['endereco'] = loc.get('address')

        elif tipo == 'interactive':
            interactive = msg.get('interactive', {})
            inter_type = interactive.get('type')

            if inter_type == 'button_reply':
                resultado['resposta_botao'] = {
                    'id': interactive.get('button_reply', {}).get('id'),
                    'titulo': interactive.get('button_reply', {}).get('title')
                }
            elif inter_type == 'list_reply':
                resultado['resposta_lista'] = {
                    'id': interactive.get('list_reply', {}).get('id'),
                    'titulo': interactive.get('list_reply', {}).get('title'),
                    'descricao': interactive.get('list_reply', {}).get('description')
                }

        return resultado

    def _processar_status(self, status: Dict) -> Dict[str, Any]:
        """
        Processa atualização de status de mensagem enviada.
        """
        return {
            'tipo': 'status_atualizado',
            'wamid': status.get('id'),
            'status': status.get('status'),  # sent, delivered, read, failed
            'timestamp': status.get('timestamp'),
            'telefone': status.get('recipient_id'),
            'erro': status.get('errors', [{}])[0] if status.get('errors') else None
        }

    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================

    async def _fazer_requisicao(self, payload: Dict) -> Dict[str, Any]:
        """
        Faz requisição para a API do WhatsApp.
        """
        url = f'{self.api_url}/{self.phone_number_id}/messages'

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        'success': True,
                        'message_id': data.get('messages', [{}])[0].get('id'),
                        'response': data
                    }
                else:
                    error_data = response.json()
                    logger.error(f'Erro WhatsApp API: {error_data}')
                    return {
                        'success': False,
                        'error': error_data.get('error', {}).get('message'),
                        'error_code': error_data.get('error', {}).get('code'),
                        'response': error_data
                    }

        except Exception as e:
            logger.error(f'Erro na requisição WhatsApp: {e}')
            return {
                'success': False,
                'error': str(e)
            }

    async def _upload_media(
        self,
        file_path: str,
        mime_type: str
    ) -> Optional[str]:
        """
        Faz upload de arquivo para o WhatsApp e retorna media_id.
        """
        url = f'{self.api_url}/{self.phone_number_id}/media'

        try:
            async with httpx.AsyncClient() as client:
                with open(file_path, 'rb') as f:
                    files = {
                        'file': (file_path, f, mime_type),
                        'messaging_product': (None, 'whatsapp'),
                        'type': (None, mime_type)
                    }
                    headers = {'Authorization': f'Bearer {self.access_token}'}

                    response = await client.post(
                        url,
                        files=files,
                        headers=headers,
                        timeout=60.0
                    )

                    if response.status_code == 200:
                        return response.json().get('id')

        except Exception as e:
            logger.error(f'Erro no upload de mídia: {e}')

        return None

    def _formatar_telefone(self, telefone: str) -> str:
        """
        Formata número de telefone para padrão WhatsApp (sem +, apenas números).
        """
        # Remover caracteres não numéricos
        apenas_numeros = ''.join(filter(str.isdigit, telefone))

        # Adicionar código do Brasil se não tiver
        if len(apenas_numeros) == 11:  # DDD + número
            apenas_numeros = '55' + apenas_numeros
        elif len(apenas_numeros) == 10:  # DDD + número sem 9
            apenas_numeros = '55' + apenas_numeros

        return apenas_numeros


# Instância global do serviço
whatsapp_service = WhatsAppService()
