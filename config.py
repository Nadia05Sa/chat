# config.py
import os
import base64
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

# Cargar variables de ambiente
load_dotenv()

oauth = OAuth()

# ----------------------------------
# Configuración del servidor WebSocket
# ----------------------------------
IP_SERVIDOR = os.environ.get("WS_HOST", "0.0.0.0")
PUERTO = int(os.environ.get("WS_PORT", 5001))

# ----------------------------------
# Claves de encriptación
# ----------------------------------
def _get_aes_key():
    """
    Obtiene la clave AES de las variables de ambiente.
    La clave debe estar codificada en base64.
    """
    key_base64 = os.environ.get("AES_KEY_BASE64")
    if not key_base64:
        raise ValueError(
            "[ERROR] AES_KEY_BASE64 no esta configurada en las variables de ambiente.\n"
            "Genera una clave con: python -c \"import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())\""
        )
    
    key_bytes = base64.b64decode(key_base64)
    if len(key_bytes) != 32:
        raise ValueError(f"[ERROR] AES_KEY debe ser de 32 bytes, se recibieron {len(key_bytes)} bytes")
    
    return key_bytes

def _get_hmac_key():
    """
    Obtiene la clave HMAC de las variables de ambiente.
    """
    key = os.environ.get("HMAC_SECRET_KEY")
    if not key:
        raise ValueError(
            "[ERROR] HMAC_SECRET_KEY no esta configurada en las variables de ambiente."
        )
    return key.encode('utf-8')

# Cargar claves (se validarán al importar el módulo)
AES_KEY = _get_aes_key()
CLAVE_SECRETA = _get_hmac_key()

# ----------------------------------
# Configuración de MongoDB
# ----------------------------------
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise ValueError("[ERROR] MONGO_URI no esta configurada en las variables de ambiente.")

DB_NAME = os.environ.get("DB_NAME", "chat-cybersecurity")
ENABLE_DB = os.environ.get("ENABLE_DB", "true").lower() == "true"

# ----------------------------------
# Configuración de Auditoría
# ----------------------------------
AUDIT_LOG_FILE = os.environ.get("AUDIT_LOG_FILE", "audit_log.txt")
ENABLE_AUDIT = os.environ.get("ENABLE_AUDIT", "true").lower() == "true"

# ----------------------------------
# Configuración SSL/TLS
# ----------------------------------
SSL_ENABLED = os.environ.get("SSL_ENABLED", "false").lower() == "true"
SSL_CERT_PATH = os.environ.get("SSL_CERT_PATH", "certs/cert.pem")
SSL_KEY_PATH = os.environ.get("SSL_KEY_PATH", "certs/key.pem")

# ----------------------------------
# Configuración de Flask
# ----------------------------------
FLASK_PORT = int(os.environ.get("FLASK_PORT", 5000))
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
