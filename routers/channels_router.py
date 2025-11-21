from fastapi import APIRouter
from db_manager import db

router = APIRouter(prefix="/channels", tags=["Channels"])

@router.get("/")
async def obtener_canales():
    return db.obtener_canales_db()

@router.post("/create")
async def crear_canal(data: dict):
    nombre = data.get("nombre")
    creador = data.get("creador_id")
    private = data.get("private", False)

    canal_id = (db.crear_canal_privado if private else db.crear_canal)(nombre, creador)
    if not canal_id:
        return {"ok": False, "msg": "Canal ya existe"}

    return {"ok": True, "canal_id": canal_id}
