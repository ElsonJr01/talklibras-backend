from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routes import documents, auth, tts, plans
from database import connect_db
import os

app = FastAPI(
    title="TalkLibras API",
    description="API de acessibilidade para leitura de documentos em Libras e Áudio",
    version="1.0.0"
)

# ── CORS — permite qualquer origem ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await connect_db()

app.include_router(auth.router,      prefix="/api/auth",      tags=["Autenticação"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documentos"])
app.include_router(tts.router,       prefix="/api/tts",       tags=["Text-to-Speech"])
app.include_router(plans.router,     prefix="/api/plans",     tags=["Planos"])

@app.get("/")
async def root():
    return {"message": "TalkLibras API v1.0", "status": "online"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)