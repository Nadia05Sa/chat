import hmac
import hashlib
import os
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from config import AES_KEY, CLAVE_SECRETA, AUDIT_LOG_FILE, ENABLE_AUDIT
import base64


# -----------------------------------------------------------
# HMAC
# -----------------------------------------------------------
def crear_hmac(mensaje_bytes):
    return hmac.new(CLAVE_SECRETA, mensaje_bytes, hashlib.sha256).hexdigest()


# -----------------------------------------------------------
# HASH
# -----------------------------------------------------------
def calcular_hash_sha256(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# -----------------------------------------------------------
# AUDITORÍA
# -----------------------------------------------------------
def escribir_log_auditoria(usuario, mensaje, hash_sha256):
    if not ENABLE_AUDIT:
        return

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        longitud = len(mensaje)

        linea = f"[{timestamp}] | {usuario:20} | {hash_sha256} | {longitud:5} chars\n"

        nuevo = not os.path.exists(AUDIT_LOG_FILE)
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            if nuevo:
                f.write("=" * 120 + "\n")
                f.write("AUDIT LOG - CHAT SEGURO\n")
                f.write("=" * 120 + "\n\n")

            f.write(linea)

    except Exception as e:
        print("[AUDIT ERROR]", e)


# -----------------------------------------------------------
# AES CBC — CORREGIDO
# -----------------------------------------------------------
def cifrar_aes_cbc(texto: str) -> str:
    data = texto.encode("utf-8")

    # PKCS7
    pad_len = 16 - (len(data) % 16)
    data += bytes([pad_len]) * pad_len

    iv = os.urandom(16)

    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()

    # CORRECCIÓN: retorna iv + ciphertext
    combinado = iv + ciphertext

    return base64.b64encode(combinado).decode("utf-8")


def descifrar_aes_cbc(cipher_base64):
    cipher_bytes = base64.b64decode(cipher_base64)

    iv = cipher_bytes[:16]
    ciphertext = cipher_bytes[16:]

    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()

    pad_len = padded[-1]
    plaintext = padded[:-pad_len]

    return plaintext.decode("utf-8", errors="ignore")
