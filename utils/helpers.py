import re
import uuid
from datetime import datetime

def generate_serial_code() -> str:
    """Gera código serial único no formato TLK-XXXX-XXXX-XXXX"""
    raw = str(uuid.uuid4()).upper().replace("-", "")
    return f"TLK-{raw[:4]}-{raw[4:8]}-{raw[8:12]}"

def clean_text(text: str) -> str:
    """Limpa e normaliza texto extraído"""
    # Remove múltiplos espaços em branco
    text = re.sub(r'\s+', ' ', text)
    # Remove linhas vazias extras
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def count_words(text: str) -> int:
    """Conta palavras no texto"""
    return len(text.split()) if text else 0

def chunk_text(text: str, max_chars: int = 200) -> list[str]:
    """Divide texto em chunks para TTS"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) <= max_chars:
            current += " " + sentence
        else:
            if current.strip():
                chunks.append(current.strip())
            current = sentence
    if current.strip():
        chunks.append(current.strip())
    return chunks if chunks else [text[:max_chars]]

def sanitize_filename(filename: str) -> str:
    """Remove caracteres problemáticos do nome do arquivo"""
    name = re.sub(r'[^\w\s.-]', '', filename)
    name = re.sub(r'\s+', '_', name)
    return name[:100]  # Limita tamanho

def format_file_size(size_bytes: int) -> str:
    """Formata tamanho de arquivo para leitura humana"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    else:
        return f"{size_bytes/(1024*1024):.1f} MB"

def utcnow_iso() -> str:
    """Retorna data/hora UTC atual em ISO format"""
    return datetime.utcnow().isoformat() + "Z"
