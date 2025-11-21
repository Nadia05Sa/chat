from authlib.integrations.flask_client import OAuth
import os
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth

oauth = OAuth()

IP_SERVIDOR = "0.0.0.0"
PUERTO = 5001

AES_KEY = bytes([
    49,50,51,52,53,54,55,56,57,48,49,50,51,52,53,54,
    55,56,57,48,49,50,51,52,53,54,55,56,57,48,49,50
])

CLAVE_SECRETA = b"clave_super_secreta"

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "chat_cybersecurity"

ENABLE_DB = True

AUDIT_LOG_FILE = "audit_log.txt"
ENABLE_AUDIT = True

AES_SECRET_KEY = b"1234567890ABCDEF1234567890ABCDEF"   # 32 bytes
AES_IV = b"ABCDEF1234567890"                           # 16 bytes


load_dotenv()

oauth = OAuth()

IP_SERVIDOR = os.getenv("IP_SERVIDOR", "0.0.0.0")
PUERTO = int(os.getenv("PUERTO", 5001))

AES_KEY = bytes(eval(os.getenv("AES_KEY", "[]")))
CLAVE_SECRETA = os.getenv("CLAVE_SECRETA", "secreto").encode()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "chat_cybersecurity")

AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_FILE", "audit_log.txt")
ENABLE_AUDIT = os.getenv("ENABLE_AUDIT", "true") == "true"
