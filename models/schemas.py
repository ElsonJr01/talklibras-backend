from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"
    PRO_MAX = "pro_max"

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    plan: PlanType
    documents_used: int
    serial_codes: List[str] = []
    created_at: datetime

class DocumentCreate(BaseModel):
    title: Optional[str] = "Documento sem título"

class DocumentResponse(BaseModel):
    id: str
    title: str
    cloudinary_url: str
    extracted_text: str
    serial_code: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime
    file_type: str
    page_count: Optional[int] = None

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "pt-BR"
    speed: Optional[float] = 1.0

class LibrasRequest(BaseModel):
    text: str

class PlanUpgrade(BaseModel):
    plan: PlanType
    payment_token: Optional[str] = None

class SerialLookup(BaseModel):
    serial_code: str

class GuestSession(BaseModel):
    session_id: str
    documents_count: int = 0
