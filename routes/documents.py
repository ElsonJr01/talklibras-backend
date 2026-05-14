from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from database import get_db
from models.schemas import DocumentResponse, SerialLookup
from services.document_service import (
    upload_to_cloudinary, extract_text, generate_serial_code, PLAN_LIMITS
)
from datetime import datetime
import uuid

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = "Documento sem título",
    session_id: str = Header(None, alias="X-Session-Id"),
    user_id: str = Header(None, alias="X-User-Id")
):
    db = get_db()
    
    # Validar tamanho
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Arquivo muito grande. Limite: 10MB")
    
    # Verificar plano e limites
    plan = "free"
    docs_used = 0
    serial_code = None
    
    if user_id:
        user = await db.users.find_one({"_id": user_id})
        if user:
            plan = user.get("plan", "free")
            docs_used = user.get("documents_used", 0)
    elif session_id:
        session = await db.sessions.find_one({"session_id": session_id})
        if session:
            docs_used = session.get("documents_count", 0)
    
    limit = PLAN_LIMITS.get(plan, 3)
    if docs_used >= limit:
        return JSONResponse(
            status_code=402,
            content={
                "error": "LIMIT_REACHED",
                "message": f"Você atingiu o limite de {limit} documentos do plano {plan.upper()}",
                "current_plan": plan,
                "docs_used": docs_used,
                "upgrade_required": True
            }
        )
    
    # Extrair texto
    text, pages, file_type = await extract_text(contents, file.filename or "document.txt")
    
    if not text:
        raise HTTPException(status_code=422, detail="Não foi possível extrair texto do documento")
    
    # Upload para Cloudinary
    cloud_result = await upload_to_cloudinary(contents, file.filename or "doc", folder="TalkLib/docs")
    
    # Gerar serial apenas para usuários PRO/PRO_MAX
    if plan in ["pro", "pro_max"]:
        serial_code = generate_serial_code()
    
    # Salvar no banco
    doc_data = {
        "_id": str(uuid.uuid4()),
        "title": title or file.filename,
        "cloudinary_url": cloud_result["url"],
        "cloudinary_public_id": cloud_result["public_id"],
        "extracted_text": text,
        "serial_code": serial_code,
        "user_id": user_id,
        "session_id": session_id,
        "file_type": file_type,
        "page_count": pages,
        "file_size": len(contents),
        "created_at": datetime.utcnow()
    }
    
    await db.documents.insert_one(doc_data)
    
    # Atualizar contadores
    if user_id:
        await db.users.update_one(
            {"_id": user_id},
            {"$inc": {"documents_used": 1}}
        )
        if serial_code:
            await db.users.update_one(
                {"_id": user_id},
                {"$push": {"serial_codes": serial_code}}
            )
    elif session_id:
        await db.sessions.update_one(
            {"session_id": session_id},
            {"$inc": {"documents_count": 1}},
            upsert=True
        )
    
    return {
        "id": doc_data["_id"],
        "title": doc_data["title"],
        "extracted_text": text,
        "serial_code": serial_code,
        "file_type": file_type,
        "page_count": pages,
        "cloudinary_url": cloud_result["url"],
        "created_at": doc_data["created_at"].isoformat(),
        "word_count": len(text.split()),
        "char_count": len(text)
    }

@router.post("/lookup")
async def lookup_by_serial(payload: SerialLookup, user_id: str = Header(None, alias="X-User-Id")):
    db = get_db()
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Login necessário para consultar por código serial")
    
    user = await db.users.find_one({"_id": user_id})
    if not user or user.get("plan", "free") == "free":
        raise HTTPException(status_code=403, detail="Recurso disponível apenas para planos PRO e PRO MAX")
    
    doc = await db.documents.find_one({"serial_code": payload.serial_code})
    if not doc:
        raise HTTPException(status_code=404, detail="Código serial não encontrado")
    
    return {
        "id": doc["_id"],
        "title": doc["title"],
        "extracted_text": doc["extracted_text"],
        "serial_code": doc["serial_code"],
        "file_type": doc["file_type"],
        "page_count": doc.get("page_count"),
        "created_at": doc["created_at"].isoformat()
    }

@router.get("/my-documents")
async def get_my_documents(user_id: str = Header(None, alias="X-User-Id")):
    db = get_db()
    if not user_id:
        raise HTTPException(status_code=401, detail="Login necessário")
    
    cursor = db.documents.find({"user_id": user_id}).sort("created_at", -1).limit(50)
    docs = await cursor.to_list(length=50)
    
    return [{
        "id": d["_id"],
        "title": d["title"],
        "serial_code": d.get("serial_code"),
        "file_type": d["file_type"],
        "page_count": d.get("page_count"),
        "created_at": d["created_at"].isoformat(),
        "word_count": len(d.get("extracted_text", "").split())
    } for d in docs]

@router.get("/{doc_id}/text")
async def get_document_text(
    doc_id: str,
    user_id: str = Header(None, alias="X-User-Id"),
    session_id: str = Header(None, alias="X-Session-Id")
):
    db = get_db()
    doc = await db.documents.find_one({"_id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    # Verificar acesso
    if doc.get("user_id") and doc["user_id"] != user_id:
        if doc.get("session_id") != session_id:
            raise HTTPException(status_code=403, detail="Acesso negado")
    
    return {
        "id": doc["_id"],
        "title": doc["title"],
        "extracted_text": doc["extracted_text"],
        "file_type": doc["file_type"],
        "word_count": len(doc["extracted_text"].split()),
        "char_count": len(doc["extracted_text"])
    }
