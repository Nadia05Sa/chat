from fastapi import APIRouter
from db_manager import db

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.get("/{canal_id}")
async def obtener_mensajes(canal_id: str):
    mensajes = db.db.mensajes.find({"canal_id": canal_id})
    return [{"usuario_id": str(m["usuario_id"]), "mensaje": m["mensaje"]} for m in mensajes]
