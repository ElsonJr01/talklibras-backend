# routes/auth.py
from fastapi import APIRouter, HTTPException
from database import get_db
from models.schemas import UserCreate, UserLogin
import hashlib
import uuid
import jwt
import os
from datetime import datetime, timedelta

router = APIRouter()
SECRET_KEY = os.getenv("JWT_SECRET", "TalkLib-secret-2026")

def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

def create_token(user_id: str, plan: str) -> str:
    payload = {
        "user_id": user_id,
        "plan": plan,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

@router.post("/register")
async def register(data: UserCreate):
    db = get_db()
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    user = {
        "_id": str(uuid.uuid4()),
        "name": data.name,
        "email": data.email,
        "password": hash_password(data.password),
        "plan": "free",
        "documents_used": 0,
        "serial_codes": [],
        "created_at": datetime.utcnow()
    }
    await db.users.insert_one(user)
    token = create_token(user["_id"], "free")
    return {"token": token, "user": {"id": user["_id"], "name": user["name"], "email": user["email"], "plan": "free"}}

@router.post("/login")
async def login(data: UserLogin):
    db = get_db()
    user = await db.users.find_one({"email": data.email})
    if not user or user["password"] != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    token = create_token(user["_id"], user["plan"])
    return {"token": token, "user": {"id": user["_id"], "name": user["name"], "email": user["email"], "plan": user["plan"], "documents_used": user["documents_used"]}}

@router.post("/guest-session")
async def create_guest_session():
    db = get_db()
    session_id = str(uuid.uuid4())
    await db.sessions.insert_one({
        "session_id": session_id,
        "documents_count": 0,
        "created_at": datetime.utcnow()
    })
    return {"session_id": session_id}
