# ws_server.py
import asyncio
import ssl
import os
import websockets
from manejadores import manejar_cliente
from db_manager import db_manager
from config import IP_SERVIDOR, PUERTO, SSL_ENABLED, SSL_CERT_PATH, SSL_KEY_PATH


def _crear_contexto_ssl():
    """
    Crea y configura el contexto SSL para WebSockets seguros (WSS).
    """
    if not os.path.exists(SSL_CERT_PATH):
        raise FileNotFoundError(
            f"❌ ERROR: Certificado SSL no encontrado en: {SSL_CERT_PATH}\n"
            "Genera certificados autofirmados con:\n"
            "  mkdir certs\n"
            '  openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/CN=localhost"'
        )
    
    if not os.path.exists(SSL_KEY_PATH):
        raise FileNotFoundError(
            f"❌ ERROR: Clave privada SSL no encontrada en: {SSL_KEY_PATH}"
        )
    
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(SSL_CERT_PATH, SSL_KEY_PATH)
    
    # Configuración de seguridad adicional
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.set_ciphers('ECDHE+AESGCM:DHE+AESGCM:ECDHE+CHACHA20:DHE+CHACHA20')
    
    return ssl_context


async def iniciar_ws():
    print("[WS] Conectando Mongo...")
    db_manager.conectar()

    if SSL_ENABLED:
        ssl_context = _crear_contexto_ssl()
        protocolo = "wss"
        print(f"[WS] 🔒 SSL/TLS habilitado")
        print(f"[WS] Certificado: {SSL_CERT_PATH}")
        print(f"[WS] Iniciando en {protocolo}://{IP_SERVIDOR}:{PUERTO}")
        
        server = await websockets.serve(
            manejar_cliente,
            IP_SERVIDOR,
            PUERTO,
            ssl=ssl_context
        )
    else:
        protocolo = "ws"
        print(f"[WS] ⚠️  SSL/TLS deshabilitado (no recomendado para producción)")
        print(f"[WS] Iniciando en {protocolo}://{IP_SERVIDOR}:{PUERTO}")
        
        server = await websockets.serve(
            manejar_cliente,
            IP_SERVIDOR,
            PUERTO
        )

    await server.wait_closed()
