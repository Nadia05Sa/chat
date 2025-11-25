# firma_digital/email_service.py
"""
Servicio de Email
=================
Envío de notificaciones y autorizaciones por correo electrónico.
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
from datetime import datetime
import secrets


class EmailService:
    """
    Servicio para enviar correos electrónicos.
    
    Soporta:
    - SMTP con TLS/SSL
    - Gmail API (opcional)
    - Plantillas HTML
    - Adjuntos
    """
    
    def __init__(
        self,
        smtp_server: str = None,
        smtp_port: int = None,
        smtp_user: str = None,
        smtp_password: str = None,
        use_tls: bool = True
    ):
        """
        Inicializa el servicio de email.
        
        Args:
            smtp_server: Servidor SMTP
            smtp_port: Puerto SMTP
            smtp_user: Usuario SMTP
            smtp_password: Contraseña SMTP
            use_tls: Usar TLS
        """
        self.smtp_server = smtp_server or os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.environ.get("SMTP_USER")
        self.smtp_password = smtp_password or os.environ.get("SMTP_PASSWORD")
        self.use_tls = use_tls
        
        self.sender_name = os.environ.get("EMAIL_SENDER_NAME", "Sistema de Firma Digital")
        self.base_url = os.environ.get("APP_BASE_URL", "http://localhost:5000")
        
        # Almacén de tokens de autorización (en producción usar Redis/DB)
        self._tokens_autorizacion = {}
    
    def _crear_conexion(self):
        """Crea conexión SMTP."""
        if not self.smtp_user or not self.smtp_password:
            raise ValueError(
                "Credenciales SMTP no configuradas.\n"
                "Configura SMTP_USER y SMTP_PASSWORD en las variables de ambiente."
            )
        
        context = ssl.create_default_context()
        
        if self.use_tls:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls(context=context)
        else:
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
        
        server.login(self.smtp_user, self.smtp_password)
        return server
    
    def enviar_email(
        self,
        destinatario: str,
        asunto: str,
        cuerpo_html: str,
        cuerpo_texto: str = None,
        adjuntos: List[str] = None,
        cc: List[str] = None,
        bcc: List[str] = None
    ) -> Dict[str, Any]:
        """
        Envía un correo electrónico.
        
        Args:
            destinatario: Email del destinatario
            asunto: Asunto del correo
            cuerpo_html: Contenido HTML
            cuerpo_texto: Contenido texto plano (opcional)
            adjuntos: Lista de rutas a archivos adjuntos
            cc: Lista de emails en copia
            bcc: Lista de emails en copia oculta
            
        Returns:
            Diccionario con resultado del envío
        """
        msg = MIMEMultipart('alternative')
        msg['Subject'] = asunto
        msg['From'] = f"{self.sender_name} <{self.smtp_user}>"
        msg['To'] = destinatario
        
        if cc:
            msg['Cc'] = ', '.join(cc)
        
        # Texto plano
        if cuerpo_texto:
            msg.attach(MIMEText(cuerpo_texto, 'plain', 'utf-8'))
        
        # HTML
        msg.attach(MIMEText(cuerpo_html, 'html', 'utf-8'))
        
        # Adjuntos
        if adjuntos:
            for archivo_path in adjuntos:
                if os.path.exists(archivo_path):
                    with open(archivo_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{os.path.basename(archivo_path)}"'
                    )
                    msg.attach(part)
        
        # Todos los destinatarios
        todos_destinatarios = [destinatario]
        if cc:
            todos_destinatarios.extend(cc)
        if bcc:
            todos_destinatarios.extend(bcc)
        
        try:
            server = self._crear_conexion()
            server.sendmail(self.smtp_user, todos_destinatarios, msg.as_string())
            server.quit()
            
            print(f"✓ Email enviado a: {destinatario}")
            
            return {
                'exito': True,
                'destinatario': destinatario,
                'asunto': asunto,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"✗ Error enviando email: {e}")
            return {
                'exito': False,
                'error': str(e),
                'destinatario': destinatario
            }
    
    def generar_token_autorizacion(
        self,
        usuario_id: str,
        archivo_id: str,
        permisos: List[str] = None,
        expiracion_horas: int = 24
    ) -> str:
        """
        Genera un token de autorización para firma.
        
        Args:
            usuario_id: ID del usuario autorizado
            archivo_id: ID del archivo a firmar
            permisos: Lista de permisos ['firma', 'lectura', 'descarga']
            expiracion_horas: Horas hasta expiración
            
        Returns:
            Token de autorización
        """
        token = secrets.token_urlsafe(32)
        
        from datetime import timedelta
        expiracion = datetime.utcnow() + timedelta(hours=expiracion_horas)
        
        self._tokens_autorizacion[token] = {
            'usuario_id': usuario_id,
            'archivo_id': archivo_id,
            'permisos': permisos or ['firma'],
            'expiracion': expiracion.isoformat(),
            'usado': False
        }
        
        return token
    
    def validar_token(self, token: str) -> Dict[str, Any]:
        """
        Valida un token de autorización.
        
        Args:
            token: Token a validar
            
        Returns:
            Información del token si es válido
        """
        if token not in self._tokens_autorizacion:
            return {'valido': False, 'error': 'Token no encontrado'}
        
        info = self._tokens_autorizacion[token]
        
        if info['usado']:
            return {'valido': False, 'error': 'Token ya fue utilizado'}
        
        expiracion = datetime.fromisoformat(info['expiracion'])
        if datetime.utcnow() > expiracion:
            return {'valido': False, 'error': 'Token expirado'}
        
        return {
            'valido': True,
            'usuario_id': info['usuario_id'],
            'archivo_id': info['archivo_id'],
            'permisos': info['permisos']
        }
    
    def marcar_token_usado(self, token: str):
        """Marca un token como utilizado."""
        if token in self._tokens_autorizacion:
            self._tokens_autorizacion[token]['usado'] = True
    
    def enviar_autorizacion_firma(
        self,
        destinatario_email: str,
        destinatario_nombre: str,
        archivo_nombre: str,
        archivo_id: str,
        solicitante_nombre: str,
        mensaje_adicional: str = None
    ) -> Dict[str, Any]:
        """
        Envía un correo de autorización para firmar un documento.
        
        Args:
            destinatario_email: Email del autorizado
            destinatario_nombre: Nombre del autorizado
            archivo_nombre: Nombre del archivo
            archivo_id: ID del archivo
            solicitante_nombre: Nombre de quien solicita
            mensaje_adicional: Mensaje extra
            
        Returns:
            Resultado del envío con token
        """
        # Generar token
        token = self.generar_token_autorizacion(
            usuario_id=destinatario_email,
            archivo_id=archivo_id,
            permisos=['firma', 'lectura']
        )
        
        # URL de autorización
        url_firma = f"{self.base_url}/firma/autorizar?token={token}"
        
        # Plantilla HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white !important;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .button:hover {{
                    opacity: 0.9;
                }}
                .info-box {{
                    background: white;
                    border-left: 4px solid #667eea;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .warning {{
                    color: #856404;
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    padding: 10px;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .footer {{
                    text-align: center;
                    color: #888;
                    font-size: 12px;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔐 Solicitud de Firma Digital</h1>
            </div>
            <div class="content">
                <p>Hola <strong>{destinatario_nombre}</strong>,</p>
                
                <p><strong>{solicitante_nombre}</strong> te ha autorizado para firmar digitalmente el siguiente documento:</p>
                
                <div class="info-box">
                    <p><strong>📄 Documento:</strong> {archivo_nombre}</p>
                    <p><strong>📅 Fecha de solicitud:</strong> {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC</p>
                    <p><strong>⏰ Válido por:</strong> 24 horas</p>
                </div>
                
                {f'<p><em>Mensaje adicional:</em> {mensaje_adicional}</p>' if mensaje_adicional else ''}
                
                <p style="text-align: center;">
                    <a href="{url_firma}" class="button">✍️ Firmar Documento</a>
                </p>
                
                <div class="warning">
                    <strong>⚠️ Importante:</strong>
                    <ul>
                        <li>Este enlace es de un solo uso</li>
                        <li>Expira en 24 horas</li>
                        <li>No compartas este enlace</li>
                    </ul>
                </div>
                
                <p>Si no solicitaste esta autorización, puedes ignorar este mensaje.</p>
            </div>
            <div class="footer">
                <p>Este es un mensaje automático del Sistema de Firma Digital</p>
                <p>© {datetime.utcnow().year} Chat Seguro - Todos los derechos reservados</p>
            </div>
        </body>
        </html>
        """
        
        texto_plano = f"""
        Solicitud de Firma Digital
        ==========================
        
        Hola {destinatario_nombre},
        
        {solicitante_nombre} te ha autorizado para firmar digitalmente el documento: {archivo_nombre}
        
        Para firmar, visita: {url_firma}
        
        Este enlace expira en 24 horas y es de un solo uso.
        
        ---
        Sistema de Firma Digital
        """
        
        resultado = self.enviar_email(
            destinatario=destinatario_email,
            asunto=f"🔐 Autorización para firmar: {archivo_nombre}",
            cuerpo_html=html,
            cuerpo_texto=texto_plano
        )
        
        resultado['token'] = token
        resultado['url_firma'] = url_firma
        
        return resultado
    
    def enviar_confirmacion_firma(
        self,
        destinatario_email: str,
        destinatario_nombre: str,
        archivo_nombre: str,
        hash_documento: str,
        link_drive: str = None
    ) -> Dict[str, Any]:
        """
        Envía confirmación de que un documento fue firmado.
        
        Args:
            destinatario_email: Email del firmante
            destinatario_nombre: Nombre del firmante
            archivo_nombre: Nombre del archivo firmado
            hash_documento: Hash SHA-256 del documento
            link_drive: Link al documento en Drive (opcional)
            
        Returns:
            Resultado del envío
        """
        timestamp = datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .success-box {{
                    background: #d4edda;
                    border: 1px solid #28a745;
                    color: #155724;
                    padding: 20px;
                    border-radius: 5px;
                    text-align: center;
                }}
                .hash-box {{
                    background: #e9ecef;
                    padding: 10px;
                    border-radius: 5px;
                    font-family: monospace;
                    font-size: 11px;
                    word-break: break-all;
                }}
                .button {{
                    display: inline-block;
                    background: #28a745;
                    color: white !important;
                    padding: 12px 25px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>✅ Documento Firmado Exitosamente</h1>
            </div>
            <div class="content">
                <div class="success-box">
                    <h2>¡Firma completada!</h2>
                    <p>Tu firma digital ha sido aplicada correctamente.</p>
                </div>
                
                <h3>Detalles de la firma:</h3>
                <ul>
                    <li><strong>Documento:</strong> {archivo_nombre}</li>
                    <li><strong>Firmante:</strong> {destinatario_nombre}</li>
                    <li><strong>Fecha/Hora:</strong> {timestamp} UTC</li>
                </ul>
                
                <h4>Hash SHA-256 del documento:</h4>
                <div class="hash-box">{hash_documento}</div>
                
                {f'<p style="text-align: center;"><a href="{link_drive}" class="button">📁 Ver en Google Drive</a></p>' if link_drive else ''}
                
                <p><small>Guarda este correo como comprobante de tu firma digital.</small></p>
            </div>
        </body>
        </html>
        """
        
        return self.enviar_email(
            destinatario=destinatario_email,
            asunto=f"✅ Documento firmado: {archivo_nombre}",
            cuerpo_html=html
        )


# Singleton
_email_service = None

def get_email_service() -> EmailService:
    """Obtiene la instancia singleton del servicio de email."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

