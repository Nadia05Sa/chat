# firma_digital/__init__.py
"""
Módulo de Firma Digital
=======================
Permite firmar digitalmente archivos PDF, TXT y ZIP.

Características:
- Firma digital con certificados X.509
- Integración con Google Drive
- Notificaciones por correo electrónico
- Verificación de firmas
"""

from .firma_service import FirmaDigitalService
from .drive_service import GoogleDriveService
from .email_service import EmailService

__all__ = ['FirmaDigitalService', 'GoogleDriveService', 'EmailService']
__version__ = '1.0.0'




