#!/usr/bin/env python3
"""
Servidor WebSocket Standalone
=============================
Ejecutar este script directamente para iniciar solo el servidor WebSocket.
Útil para despliegue en producción donde Flask y WS corren por separado.

Uso:
    python ws_server_standalone.py
"""

import asyncio
from dotenv import load_dotenv

# Cargar variables de ambiente
load_dotenv()

from ws_server import iniciar_ws


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🔌 SERVIDOR WEBSOCKET STANDALONE")
    print("=" * 50)
    
    try:
        asyncio.run(iniciar_ws())
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("[x] Servidor WebSocket detenido")
        print("=" * 50)


