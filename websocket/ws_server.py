from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websocket.connections_manager import manager
from db_manager import db
from datetime import datetime

router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("/{usuario_id}")
async def websocket_endpoint(websocket: WebSocket, usuario_id: str):
    await manager.conectar(usuario_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            canal_id = data["canal_id"]
            mensaje = data["mensaje"]

            # Guardar en DB
            db.db.mensajes.insert_one({
                "usuario_id": usuario_id,
                "canal_id": canal_id,
                "mensaje": mensaje,
                "timestamp": datetime.utcnow()
            })

            # mandar a todos
            await manager.broadcast({
                "usuario_id": usuario_id,
                "canal_id": canal_id,
                "mensaje": mensaje
            })

    except WebSocketDisconnect:
        manager.desconectar(usuario_id)
