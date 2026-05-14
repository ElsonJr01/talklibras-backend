from fastapi import APIRouter, HTTPException, Header
from database import get_db
from datetime import datetime

router = APIRouter()

PLANS = {
    "free": {"name": "Gratuito", "price": 0, "documents": 3, "serial": False, "audio": True, "libras": True},
    "pro": {"name": "PRO", "price": 20.00, "documents": 30, "serial": True, "audio": True, "libras": True, "priority": True},
    "pro_max": {"name": "PRO MAX", "price": 49.90, "documents": 999999, "serial": True, "audio": True, "libras": True, "priority": True, "api_access": True}
}

@router.get("/")
async def list_plans():
    return {"plans": PLANS}

@router.post("/upgrade")
async def upgrade_plan(
    plan: str,
    user_id: str = Header(None, alias="X-User-Id")
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Login necessário para upgrade")
    if plan not in ["pro", "pro_max"]:
        raise HTTPException(status_code=400, detail="Plano inválido")
    
    db = get_db()
    # Em produção: integrar com Stripe/PagSeguro/Mercado Pago
    # Aqui simulamos o upgrade
    await db.users.update_one(
        {"_id": user_id},
        {"$set": {"plan": plan, "upgraded_at": datetime.utcnow()}}
    )
    return {
        "success": True,
        "new_plan": plan,
        "message": f"Plano atualizado para {PLANS[plan]['name']}!",
        "payment_note": "Integração com Mercado Pago/Stripe disponível em produção"
    }

@router.get("/status")
async def plan_status(user_id: str = Header(None, alias="X-User-Id")):
    if not user_id:
        return {"plan": "free", "documents_used": 0, "documents_limit": 3}
    
    db = get_db()
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    plan = user.get("plan", "free")
    plan_info = PLANS.get(plan, PLANS["free"])
    
    return {
        "plan": plan,
        "plan_name": plan_info["name"],
        "documents_used": user.get("documents_used", 0),
        "documents_limit": plan_info["documents"],
        "serial_codes": user.get("serial_codes", []),
        "features": plan_info
    }
