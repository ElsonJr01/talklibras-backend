from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import httpx
import os
import urllib.parse
from models.schemas import TTSRequest, LibrasRequest
from services.document_service import (
    tts_responsivevoice_url, get_vlibras_url,
    get_libras_signs_for_word, chunk_text, tts_voicerss_free
)

router = APIRouter()

@router.post("/speak")
async def text_to_speech(req: TTSRequest):
    """
    Converte texto para áudio usando múltiplos provedores gratuitos:
    1. VoiceRSS (350 req/dia gratuito)
    2. ResponsiveVoice (fallback)
    3. Google TTS via translate (fallback público)
    """
    text = req.text[:2000]  # Limite de segurança
    chunks = chunk_text(text, 180)
    
    # Tenta VoiceRSS primeiro
    voicerss_key = os.getenv("VOICERSS_API_KEY")
    if voicerss_key:
        result = await tts_voicerss_free(text[:500], req.voice or "pt-br")
        if "audio_b64" in result:
            return {
                "provider": "VoiceRSS",
                "audio_b64": result["audio_b64"],
                "format": "mp3",
                "chunks": chunks,
                "total_chars": len(text)
            }
    
    # Fallback: ResponsiveVoice URL
    voice_name = "Brazilian Portuguese Female"
    rv_urls = []
    for chunk in chunks:
        encoded = urllib.parse.quote(chunk)
        url = f"https://code.responsivevoice.org/getaudio?tl=pt&sv=&vn={urllib.parse.quote(voice_name)}&pitch=0.5&rate={req.speed or 0.5}&vol=1&t=1&text={encoded}"
        rv_urls.append(url)
    
    # Google TTS público (sem chave)
    google_urls = []
    for chunk in chunks[:5]:  # Limite para evitar abuso
        encoded = urllib.parse.quote(chunk)
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded}&tl=pt&client=tw-ob"
        google_urls.append(url)
    
    return {
        "provider": "multi",
        "responsive_voice_urls": rv_urls,
        "google_tts_urls": google_urls,
        "chunks": chunks,
        "total_chunks": len(chunks),
        "total_chars": len(text),
        "voice": voice_name,
        "instructions": "Use os URLs para reprodução em sequência no frontend"
    }

@router.post("/libras")
async def text_to_libras(req: LibrasRequest):
    """
    Prepara tradução para Libras usando VLibras (governo brasileiro - gratuito)
    e outros recursos abertos
    """
    text = req.text[:3000]
    
    vlibras_data = await get_vlibras_url(text)
    
    # Palavras únicas para dicionário
    words = list(set(text.lower().split()))[:20]
    word_links = []
    for word in words[:10]:
        clean = ''.join(c for c in word if c.isalpha())
        if clean and len(clean) > 2:
            word_links.append({
                "word": clean,
                "spread_sign_url": f"https://www.spreadthesign.com/pt.br/search/?q={clean}",
                "dict_url": f"https://www.dicionariolibras.com.br/palavra/{clean}"
            })
    
    return {
        "service": "VLibras + Recursos Abertos",
        "vlibras": vlibras_data,
        "word_dictionary": word_links,
        "text_length": len(text),
        "vlibras_widget": {
            "script": "https://vlibras.gov.br/app/vlibras-plugin.js",
            "embed_script": """
                <div vw class="enabled">
                  <div vw-access-button class="active"></div>
                  <div vw-plugin-wrapper>
                    <div class="vw-plugin-top-wrapper"></div>
                  </div>
                </div>
                <script src='https://vlibras.gov.br/app/vlibras-plugin.js'></script>
                <script>new window.VLibras.Widget('https://vlibras.gov.br/app');</script>
            """,
            "description": "Widget oficial do VLibras - Governo Federal do Brasil"
        },
        "hand_talk_info": {
            "website": "https://www.handtalk.me",
            "description": "Tradutor de Libras - trial disponível"
        },
        "acessibilidade_brasil": {
            "url": f"https://www.acessibilidadebrasil.org.br/libras/?palavra={urllib.parse.quote(text[:100])}",
        }
    }

@router.get("/voices")
async def list_voices():
    """Lista todas as vozes disponíveis gratuitamente"""
    return {
        "portuguese_voices": [
            {"name": "Brazilian Portuguese Female", "provider": "ResponsiveVoice", "lang": "pt-BR"},
            {"name": "Brazilian Portuguese Male", "provider": "ResponsiveVoice", "lang": "pt-BR"},
            {"name": "pt-BR", "provider": "Google TTS", "lang": "pt-BR"},
            {"name": "pt-br", "provider": "VoiceRSS", "lang": "pt-BR"},
        ],
        "providers": [
            {
                "name": "VoiceRSS",
                "url": "https://www.voicerss.org",
                "free_limit": "350 requisições/dia",
                "requires_key": True
            },
            {
                "name": "ResponsiveVoice",
                "url": "https://responsivevoice.org",
                "free_limit": "Uso público não comercial",
                "requires_key": False
            },
            {
                "name": "Google TTS",
                "url": "https://translate.google.com",
                "free_limit": "Via endpoint público",
                "requires_key": False,
                "note": "Sujeito a rate limiting"
            },
            {
                "name": "VLibras",
                "url": "https://vlibras.gov.br",
                "free_limit": "Ilimitado - serviço público",
                "requires_key": False,
                "language": "Libras (Língua Brasileira de Sinais)"
            }
        ]
    }
