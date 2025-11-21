from fastapi import APIRouter, Request
from db_manager import db

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
async def register_user(data: dict, req: Request):
    nombre = data.get("nombre")
    apellido = data.get("apellido")
    email = data.get("email")
    password = data.get("password")
    ip = req.client.host

    user_id = db.crear_usuario_classico(nombre, apellido, email, password, ip)
    if not user_id:
        return {"ok": False, "msg": "Usuario ya existe"}

    return {"ok": True, "user_id": user_id}

@router.post("/login")
async def login_user(data: dict, req: Request):
    email = data.get("email")
    password = data.get("password")
    ip = req.client.host

    user_id = db.login_usuario_classico(email, password, ip)
    if not user_id:
        return {"ok": False, "msg": "Credenciales inválidas"}

    return {"ok": True, "user_id": user_id}
