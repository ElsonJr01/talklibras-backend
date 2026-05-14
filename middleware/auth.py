from fastapi import HTTPException, Header, Depends
from database import get_db
import jwt
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET", "TalkLib-secret-2026")

async def get_current_user(authorization: str = Header(None)):
    """Extrai e valida o token JWT do header Authorization"""
    if not authorization:
        return None
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception:
        return None

async def require_auth(authorization: str = Header(None)):
    """Requer autenticação, lança 401 se não autenticado"""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticação necessária")
    return user

async def require_pro(authorization: str = Header(None)):
    """Requer plano PRO ou superior"""
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticação necessária")
    if user.get("plan", "free") not in ["pro", "pro_max"]:
        raise HTTPException(status_code=403, detail="Recurso disponível apenas para planos PRO e PRO MAX")
    return user
