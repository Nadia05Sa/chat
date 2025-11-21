import asyncio
import websockets
from manejadores import manejar_cliente
from db_manager import db_manager
from config import IP_SERVIDOR, PUERTO

async def iniciar_ws():
    print("[WS] Conectando Mongo...")
    db_manager.conectar()

    print(f"[WS] Servidor en ws://{IP_SERVIDOR}:{PUERTO}")
    server = await websockets.serve(manejar_cliente, IP_SERVIDOR, PUERTO)

    await server.wait_closed()
