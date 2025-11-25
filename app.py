#app.py
import threading
import asyncio
import os
import ssl
from flask import Flask
from ws_server import iniciar_ws 
from config import (
    oauth, 
    SSL_ENABLED, 
    SSL_CERT_PATH, 
    SSL_KEY_PATH,
    FLASK_PORT,
    FLASK_DEBUG
)
from index import rutas
from firma_digital.routes import firma_bp
from dotenv import load_dotenv


load_dotenv()  # carga variables desde .env

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET')

if not app.secret_key:
    raise ValueError("❌ ERROR: FLASK_SECRET no está configurada en las variables de ambiente.")

# Configuración de subida de archivos
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB máximo

oauth.init_app(app)
oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'},
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
)

# Registrar blueprints
app.register_blueprint(rutas)
app.register_blueprint(firma_bp)  # Módulo de firma digital 


@app.get("/")
def home():
    return {"mensaje": "Flask y WebSocket funcionando", "ssl_enabled": SSL_ENABLED}


@app.get("/config/ws")
def ws_config():
    """
    Endpoint para que el frontend obtenga la configuración del WebSocket.
    Esto permite que el JavaScript sepa si usar WS o WSS dinámicamente.
    """
    ws_port = os.environ.get('WS_PORT', '5001')
    return {
        "ssl_enabled": SSL_ENABLED,
        "ws_port": ws_port
    }


def lanzar_ws():
    """Inicia el servidor WebSocket dentro de un hilo."""
    asyncio.run(iniciar_ws())


def _crear_contexto_ssl_flask():
    """
    Crea contexto SSL para Flask (HTTPS).
    """
    if not os.path.exists(SSL_CERT_PATH):
        raise FileNotFoundError(
            f"❌ ERROR: Certificado SSL no encontrado en: {SSL_CERT_PATH}\n"
            "Genera certificados autofirmados con:\n"
            "  mkdir certs\n"
            '  openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/CN=localhost"'
        )
    
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(SSL_CERT_PATH, SSL_KEY_PATH)
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    
    return ssl_context


if __name__ == "__main__":
    print("\n======================")
    print("🚀 INICIANDO SERVIDOR")
    print("======================")

    # Lanzar servidor WebSocket en segundo plano
    hilo_ws = threading.Thread(target=lanzar_ws, daemon=True)
    hilo_ws.start()

    try:
        protocolo = "https" if SSL_ENABLED else "http"
        print(f"🌐 Iniciando Flask en {protocolo}://127.0.0.1:{FLASK_PORT} ...")
        
        if SSL_ENABLED:
            print("🔒 SSL/TLS habilitado para Flask (HTTPS)")
            ssl_context = _crear_contexto_ssl_flask()
            app.run(
                debug=FLASK_DEBUG, 
                port=FLASK_PORT, 
                use_reloader=False,
                ssl_context=ssl_context
            )
        else:
            print("⚠️  SSL/TLS deshabilitado (no recomendado para producción)")
            app.run(
                debug=FLASK_DEBUG, 
                port=FLASK_PORT, 
                use_reloader=False
            )

    except KeyboardInterrupt:
        print("\n======================")
        print("🛑 Servidor detenido con CTRL+C")
        print("======================")

    finally:
        # cierre seguro
        from db_manager import db_manager
        if db_manager.conectado:
            db_manager.cerrar()

        print("✓ Recursos limpiados correctamente")
        print("======================\n")
