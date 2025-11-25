#!/usr/bin/env python3
"""
Script para generar certificados SSL autofirmados para desarrollo.

USO:
    python generar_certificados.py

Esto creará:
    - certs/cert.pem  (certificado público)
    - certs/key.pem   (clave privada)

⚠️ IMPORTANTE: Estos certificados son SOLO para desarrollo.
   En producción, usa certificados de una CA real (ej: Let's Encrypt).
"""

import os
import datetime
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generar_certificados(
    directorio: str = "certs",
    dias_validez: int = 365,
    common_name: str = "localhost"
):
    """
    Genera un par de certificados SSL autofirmados.
    
    Args:
        directorio: Carpeta donde guardar los certificados
        dias_validez: Días de validez del certificado
        common_name: Nombre común (CN) del certificado
    """
    # Crear directorio si no existe
    os.makedirs(directorio, exist_ok=True)
    
    cert_path = os.path.join(directorio, "cert.pem")
    key_path = os.path.join(directorio, "key.pem")
    
    print("=" * 50)
    print("🔐 Generando certificados SSL autofirmados")
    print("=" * 50)
    
    # 1. Generar clave privada RSA
    print("\n[1/3] Generando clave privada RSA (4096 bits)...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )
    
    # 2. Crear certificado autofirmado
    print("[2/3] Creando certificado autofirmado...")
    
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "MX"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Estado"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Ciudad"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Chat Seguro Dev"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=dias_validez))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )
    
    # 3. Guardar archivos
    print("[3/3] Guardando archivos...")
    
    # Guardar clave privada
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Guardar certificado
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    print("\n" + "=" * 50)
    print("✅ Certificados generados exitosamente!")
    print("=" * 50)
    print(f"\n📁 Ubicación:")
    print(f"   Certificado: {os.path.abspath(cert_path)}")
    print(f"   Clave privada: {os.path.abspath(key_path)}")
    print(f"\n📅 Válido por: {dias_validez} días")
    print(f"🏷️  Common Name: {common_name}")
    print("\n⚠️  IMPORTANTE:")
    print("   - Estos certificados son SOLO para desarrollo")
    print("   - El navegador mostrará una advertencia de seguridad")
    print("   - En producción, usa Let's Encrypt u otra CA real")
    print("\n🔧 Para habilitar SSL, configura en .env:")
    print("   SSL_ENABLED=true")
    print("   SSL_CERT_PATH=certs/cert.pem")
    print("   SSL_KEY_PATH=certs/key.pem")
    print("=" * 50)


if __name__ == "__main__":
    generar_certificados()

