# firma_digital/firma_service.py
"""
Servicio de Firma Digital
=========================
Implementa firma digital para archivos PDF, TXT y ZIP.
"""

import os
import hashlib
import json
import zipfile
import tempfile
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
import base64


class FirmaDigitalService:
    """
    Servicio para firmar digitalmente archivos.
    
    Soporta:
    - PDF: Firma embebida en metadatos o archivo separado
    - TXT: Firma en archivo .sig separado
    - ZIP: Firma del hash del archivo completo
    """
    
    TIPOS_PERMITIDOS = {'.pdf', '.txt', '.zip'}
    
    def __init__(self, cert_path: str = None, key_path: str = None, upload_folder: str = "uploads"):
        """
        Inicializa el servicio de firma digital.
        
        Args:
            cert_path: Ruta al certificado público (.pem)
            key_path: Ruta a la clave privada (.pem)
            upload_folder: Carpeta para archivos subidos
        """
        self.cert_path = cert_path or os.environ.get("FIRMA_CERT_PATH", "certs/firma_cert.pem")
        self.key_path = key_path or os.environ.get("FIRMA_KEY_PATH", "certs/firma_key.pem")
        self.upload_folder = upload_folder
        
        # Crear carpetas necesarias
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(os.path.join(upload_folder, "firmados"), exist_ok=True)
        os.makedirs(os.path.join(upload_folder, "pendientes"), exist_ok=True)
        
        self._private_key = None
        self._certificate = None
        self._cargar_credenciales()
    
    def _cargar_credenciales(self):
        """Carga el certificado y la clave privada."""
        try:
            if os.path.exists(self.key_path):
                with open(self.key_path, "rb") as f:
                    self._private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None,
                        backend=default_backend()
                    )
                print(f"[+] Clave privada cargada: {self.key_path}")
            
            if os.path.exists(self.cert_path):
                with open(self.cert_path, "rb") as f:
                    self._certificate = x509.load_pem_x509_certificate(
                        f.read(),
                        backend=default_backend()
                    )
                print(f"[+] Certificado cargado: {self.cert_path}")
                
        except Exception as e:
            print(f"[!] Error cargando credenciales de firma: {e}")
            print("   Ejecuta 'python -m firma_digital.generar_certificado_firma' para crear uno nuevo")
    
    def generar_certificado_firma(
        self,
        common_name: str = "Firmador Digital",
        organization: str = "Chat Seguro",
        dias_validez: int = 365
    ) -> Tuple[str, str]:
        """
        Genera un nuevo par de certificado/clave para firma digital.
        
        Returns:
            Tuple con rutas (cert_path, key_path)
        """
        # Generar clave privada RSA
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        # Crear certificado autofirmado
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "MX"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])
        
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=dias_validez))
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=False,
                    content_commitment=True,  # Non-repudiation
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .sign(private_key, hashes.SHA256(), backend=default_backend())
        )
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(self.cert_path) or ".", exist_ok=True)
        
        # Guardar clave privada
        with open(self.key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Guardar certificado
        with open(self.cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        self._private_key = private_key
        self._certificate = cert
        
        print(f"[+] Certificado de firma generado: {self.cert_path}")
        print(f"[+] Clave privada generada: {self.key_path}")
        
        return (self.cert_path, self.key_path)
    
    def _calcular_hash(self, data: bytes) -> bytes:
        """Calcula SHA-256 de los datos."""
        return hashlib.sha256(data).digest()
    
    def _firmar_datos(self, data: bytes) -> bytes:
        """
        Firma datos con la clave privada RSA.
        
        Args:
            data: Datos a firmar
            
        Returns:
            Firma digital en bytes
        """
        if not self._private_key:
            raise ValueError("No hay clave privada configurada para firmar")
        
        signature = self._private_key.sign(
            data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return signature
    
    def _verificar_firma(self, data: bytes, signature: bytes) -> bool:
        """
        Verifica una firma digital.
        
        Args:
            data: Datos originales
            signature: Firma a verificar
            
        Returns:
            True si la firma es válida
        """
        if not self._certificate:
            raise ValueError("No hay certificado configurado para verificar")
        
        try:
            public_key = self._certificate.public_key()
            public_key.verify(
                signature,
                data,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    def firmar_archivo(
        self,
        archivo_path: str,
        firmante_id: str,
        firmante_nombre: str,
        firmante_email: str,
        razon: str = "Firma digital de documento"
    ) -> Dict[str, Any]:
        """
        Firma un archivo y genera el comprobante.
        
        Args:
            archivo_path: Ruta al archivo a firmar
            firmante_id: ID del usuario firmante
            firmante_nombre: Nombre del firmante
            firmante_email: Email del firmante
            razon: Razón de la firma
            
        Returns:
            Diccionario con información de la firma
        """
        if not os.path.exists(archivo_path):
            raise FileNotFoundError(f"Archivo no encontrado: {archivo_path}")
        
        extension = os.path.splitext(archivo_path)[1].lower()
        if extension not in self.TIPOS_PERMITIDOS:
            raise ValueError(f"Tipo de archivo no permitido: {extension}")
        
        # Leer archivo
        with open(archivo_path, "rb") as f:
            contenido = f.read()
        
        # Calcular hash del contenido
        hash_contenido = self._calcular_hash(contenido)
        hash_hex = hash_contenido.hex()
        
        # Crear metadatos de firma
        timestamp = datetime.utcnow().isoformat() + "Z"
        metadatos = {
            "version": "1.0",
            "archivo_original": os.path.basename(archivo_path),
            "hash_sha256": hash_hex,
            "tamaño_bytes": len(contenido),
            "firmante": {
                "id": firmante_id,
                "nombre": firmante_nombre,
                "email": firmante_email
            },
            "firma": {
                "timestamp": timestamp,
                "razon": razon,
                "algoritmo": "RSA-SHA256",
                "certificado_emisor": self._certificate.issuer.rfc4514_string() if self._certificate else "N/A",
                "certificado_serial": str(self._certificate.serial_number) if self._certificate else "N/A"
            }
        }
        
        # Firmar el hash
        firma_bytes = self._firmar_datos(hash_contenido)
        firma_base64 = base64.b64encode(firma_bytes).decode('utf-8')
        metadatos["firma"]["valor"] = firma_base64
        
        # Generar nombre de archivo firmado
        nombre_base = os.path.splitext(os.path.basename(archivo_path))[0]
        timestamp_archivo = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Crear archivo de firma (.sig)
        firma_path = os.path.join(
            self.upload_folder,
            "firmados",
            f"{nombre_base}_{timestamp_archivo}.sig"
        )
        
        with open(firma_path, "w", encoding="utf-8") as f:
            json.dump(metadatos, f, indent=2, ensure_ascii=False)
        
        # Copiar archivo original a carpeta de firmados
        archivo_firmado_path = os.path.join(
            self.upload_folder,
            "firmados",
            f"{nombre_base}_{timestamp_archivo}{extension}"
        )
        
        with open(archivo_firmado_path, "wb") as f:
            f.write(contenido)
        
        return {
            "exito": True,
            "archivo_original": archivo_path,
            "archivo_firmado": archivo_firmado_path,
            "archivo_firma": firma_path,
            "hash": hash_hex,
            "timestamp": timestamp,
            "metadatos": metadatos
        }
    
    def verificar_archivo_firmado(self, archivo_path: str, firma_path: str) -> Dict[str, Any]:
        """
        Verifica la firma de un archivo.
        
        Args:
            archivo_path: Ruta al archivo
            firma_path: Ruta al archivo de firma (.sig)
            
        Returns:
            Diccionario con resultado de la verificación
        """
        # Leer archivo
        with open(archivo_path, "rb") as f:
            contenido = f.read()
        
        # Leer firma
        with open(firma_path, "r", encoding="utf-8") as f:
            metadatos = json.load(f)
        
        # Verificar hash
        hash_actual = self._calcular_hash(contenido).hex()
        hash_guardado = metadatos.get("hash_sha256", "")
        
        if hash_actual != hash_guardado:
            return {
                "valido": False,
                "error": "El archivo ha sido modificado (hash no coincide)",
                "hash_esperado": hash_guardado,
                "hash_actual": hash_actual
            }
        
        # Verificar firma digital
        firma_base64 = metadatos.get("firma", {}).get("valor", "")
        if firma_base64:
            firma_bytes = base64.b64decode(firma_base64)
            hash_bytes = bytes.fromhex(hash_guardado)
            
            firma_valida = self._verificar_firma(hash_bytes, firma_bytes)
            
            if not firma_valida:
                return {
                    "valido": False,
                    "error": "La firma digital no es válida",
                    "metadatos": metadatos
                }
        
        return {
            "valido": True,
            "mensaje": "Archivo verificado correctamente",
            "firmante": metadatos.get("firmante", {}),
            "fecha_firma": metadatos.get("firma", {}).get("timestamp"),
            "metadatos": metadatos
        }
    
    def listar_archivos_pendientes(self) -> list:
        """Lista archivos pendientes de firma."""
        pendientes_dir = os.path.join(self.upload_folder, "pendientes")
        archivos = []
        
        for archivo in os.listdir(pendientes_dir):
            path = os.path.join(pendientes_dir, archivo)
            if os.path.isfile(path):
                ext = os.path.splitext(archivo)[1].lower()
                if ext in self.TIPOS_PERMITIDOS:
                    stat = os.stat(path)
                    archivos.append({
                        "nombre": archivo,
                        "path": path,
                        "tamaño": stat.st_size,
                        "fecha_subida": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        return archivos
    
    def listar_archivos_firmados(self) -> list:
        """Lista archivos ya firmados."""
        firmados_dir = os.path.join(self.upload_folder, "firmados")
        archivos = []
        
        for archivo in os.listdir(firmados_dir):
            if archivo.endswith(".sig"):
                path = os.path.join(firmados_dir, archivo)
                with open(path, "r", encoding="utf-8") as f:
                    metadatos = json.load(f)
                
                archivos.append({
                    "nombre": metadatos.get("archivo_original"),
                    "firma_path": path,
                    "firmante": metadatos.get("firmante", {}),
                    "fecha_firma": metadatos.get("firma", {}).get("timestamp"),
                    "hash": metadatos.get("hash_sha256")
                })
        
        return archivos


# Importación necesaria al inicio (evitar circular)
from datetime import timedelta


