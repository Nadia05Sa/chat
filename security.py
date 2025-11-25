import hmac
import hashlib
import os
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from config import AES_KEY, CLAVE_SECRETA, AUDIT_LOG_FILE, ENABLE_AUDIT
import base64

def crear_hmac(mensaje_bytes):
    """Crea HMAC-SHA256 de los datos"""
    return hmac.new(CLAVE_SECRETA, mensaje_bytes, hashlib.sha256).hexdigest()

def calcular_hash_sha256(texto):
    """Calcula hash SHA-256 del mensaje para auditoría"""
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def escribir_log_auditoria(usuario, mensaje, hash_sha256):
    """Escribe entrada en el log de auditoría (archivo de texto)"""
    if not ENABLE_AUDIT:
        return
    
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        longitud = len(mensaje)
        
        linea_log = f"[{timestamp}] | {usuario:20} | {hash_sha256} | {longitud:5} chars\n"
        
        if not os.path.exists(AUDIT_LOG_FILE):
            with open(AUDIT_LOG_FILE, 'w', encoding='utf-8') as f:
                f.write("=" * 120 + "\n")
                f.write("AUDIT LOG - CHAT GRUPAL SEGURO v1.2.0\n")
                f.write("=" * 120 + "\n")
                f.write(f"Inicio de auditoría: {timestamp}\n")
                f.write("=" * 120 + "\n")
                f.write(f"{'TIMESTAMP':20} | {'USUARIO':20} | {'HASH SHA-256':64} | {'LONGITUD':10}\n")
                f.write("-" * 120 + "\n")
        
        with open(AUDIT_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(linea_log)
        
    except Exception as e:
        print(f"[ERROR AUDIT] No se pudo escribir en log: {e}")

def descifrar_aes_cbc(cipher_bytes):
    """Descifra usando AES-CBC con padding PKCS7 y limpia caracteres extra"""
    if len(cipher_bytes) < 16:
        raise ValueError(f"Datos cifrados demasiado cortos: {len(cipher_bytes)} bytes")
    
    iv = cipher_bytes[:16]
    ciphertext = cipher_bytes[16:]
    
    try:
        cipher = Cipher(
            algorithms.AES(AES_KEY),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        plaintext_padded = decryptor.update(ciphertext) + decryptor.finalize()
        
        if len(plaintext_padded) == 0:
            raise ValueError("Plaintext vacío después de descifrar")
        
        padding_len = plaintext_padded[-1]
        if padding_len < 1 or padding_len > 16:
            raise ValueError(f"Padding inválido: {padding_len}")
        
        plaintext_bytes = plaintext_padded[:-padding_len]
        
        # Decodificar UTF-8 y eliminar caracteres de control no imprimibles
        texto = plaintext_bytes.decode('utf-8', errors='ignore')
        texto = ''.join(c for c in texto if c.isprintable() or c.isspace())
        
        return texto
    
    except Exception as e:
        raise ValueError(f"Error al descifrar: {str(e)}")
    
def cifrar_aes_cbc(texto: str) -> bytes:
    """
    Cifra un string con AES-CBC + PKCS7 padding.
    Devuelve: IV + ciphertext (en bytes)
    """
    # Convertir a bytes
    mensaje_bytes = texto.encode("utf-8")

    # Padding PKCS7
    padding_len = 16 - (len(mensaje_bytes) % 16)
    mensaje_bytes += bytes([padding_len]) * padding_len

    # IV aleatorio de 16 bytes
    iv = os.urandom(16)

    cipher = Cipher(
        algorithms.AES(AES_KEY),
        modes.CBC(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(mensaje_bytes) + encryptor.finalize()

    # Guardamos IV + ciphertext
    return base64.b64encode(ciphertext).decode("utf-8")