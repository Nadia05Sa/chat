# firma_digital/drive_service.py
"""
Servicio de Google Drive
========================
Integración con Google Drive para subir documentos firmados.
"""

import os
import io
import json
from typing import Optional, Dict, Any, List
from datetime import datetime


class GoogleDriveService:
    """
    Servicio para interactuar con Google Drive API.
    
    Permite:
    - Subir archivos firmados
    - Crear carpetas de organización
    - Compartir archivos con permisos específicos
    - Listar documentos
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.metadata.readonly'
    ]
    
    def __init__(self, credentials_path: str = None):
        """
        Inicializa el servicio de Google Drive.
        
        Args:
            credentials_path: Ruta al archivo de credenciales JSON de Google
        """
        self.credentials_path = credentials_path or os.environ.get(
            "GOOGLE_DRIVE_CREDENTIALS",
            "credentials/google_drive_credentials.json"
        )
        self.service = None
        self._folder_id_cache = {}
        
    def _get_service(self):
        """
        Obtiene el servicio de Google Drive autenticado.
        
        Returns:
            Servicio de Google Drive
        """
        if self.service:
            return self.service
        
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(
                    f"Credenciales de Google Drive no encontradas: {self.credentials_path}\n"
                    "Descarga las credenciales desde Google Cloud Console"
                )
            
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            
            self.service = build('drive', 'v3', credentials=credentials)
            print("✓ Conectado a Google Drive")
            return self.service
            
        except ImportError:
            raise ImportError(
                "Instala las dependencias de Google:\n"
                "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            )
    
    def crear_carpeta(self, nombre: str, parent_id: str = None) -> str:
        """
        Crea una carpeta en Google Drive.
        
        Args:
            nombre: Nombre de la carpeta
            parent_id: ID de la carpeta padre (opcional)
            
        Returns:
            ID de la carpeta creada
        """
        service = self._get_service()
        
        file_metadata = {
            'name': nombre,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        folder_id = folder.get('id')
        print(f"✓ Carpeta creada: {nombre} (ID: {folder_id})")
        
        return folder_id
    
    def obtener_o_crear_carpeta(self, nombre: str, parent_id: str = None) -> str:
        """
        Obtiene una carpeta existente o la crea si no existe.
        
        Args:
            nombre: Nombre de la carpeta
            parent_id: ID de la carpeta padre
            
        Returns:
            ID de la carpeta
        """
        cache_key = f"{parent_id or 'root'}:{nombre}"
        if cache_key in self._folder_id_cache:
            return self._folder_id_cache[cache_key]
        
        service = self._get_service()
        
        # Buscar carpeta existente
        query = f"name='{nombre}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            folder_id = files[0]['id']
        else:
            folder_id = self.crear_carpeta(nombre, parent_id)
        
        self._folder_id_cache[cache_key] = folder_id
        return folder_id
    
    def subir_archivo(
        self,
        archivo_path: str,
        nombre_destino: str = None,
        folder_id: str = None,
        descripcion: str = None
    ) -> Dict[str, Any]:
        """
        Sube un archivo a Google Drive.
        
        Args:
            archivo_path: Ruta al archivo local
            nombre_destino: Nombre del archivo en Drive (opcional)
            folder_id: ID de la carpeta destino
            descripcion: Descripción del archivo
            
        Returns:
            Diccionario con información del archivo subido
        """
        from googleapiclient.http import MediaFileUpload
        
        service = self._get_service()
        
        if not os.path.exists(archivo_path):
            raise FileNotFoundError(f"Archivo no encontrado: {archivo_path}")
        
        nombre = nombre_destino or os.path.basename(archivo_path)
        
        # Determinar MIME type
        mime_types = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.zip': 'application/zip',
            '.sig': 'application/json'
        }
        ext = os.path.splitext(archivo_path)[1].lower()
        mime_type = mime_types.get(ext, 'application/octet-stream')
        
        file_metadata = {
            'name': nombre,
            'description': descripcion or f"Subido el {datetime.utcnow().isoformat()}"
        }
        
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        media = MediaFileUpload(
            archivo_path,
            mimetype=mime_type,
            resumable=True
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink, webContentLink'
        ).execute()
        
        print(f"✓ Archivo subido: {nombre}")
        
        return {
            'id': file.get('id'),
            'nombre': file.get('name'),
            'link_vista': file.get('webViewLink'),
            'link_descarga': file.get('webContentLink')
        }
    
    def subir_documento_firmado(
        self,
        archivo_path: str,
        firma_path: str,
        firmante_email: str
    ) -> Dict[str, Any]:
        """
        Sube un documento firmado junto con su firma a Drive.
        
        Args:
            archivo_path: Ruta al archivo firmado
            firma_path: Ruta al archivo de firma (.sig)
            firmante_email: Email del firmante
            
        Returns:
            Diccionario con información de los archivos subidos
        """
        # Crear estructura de carpetas
        root_folder = self.obtener_o_crear_carpeta("Documentos_Firmados")
        
        # Carpeta por fecha
        fecha = datetime.utcnow().strftime("%Y-%m")
        fecha_folder = self.obtener_o_crear_carpeta(fecha, root_folder)
        
        # Subir archivo
        archivo_info = self.subir_archivo(
            archivo_path,
            folder_id=fecha_folder,
            descripcion=f"Documento firmado por {firmante_email}"
        )
        
        # Subir firma
        firma_info = self.subir_archivo(
            firma_path,
            folder_id=fecha_folder,
            descripcion=f"Firma digital - {firmante_email}"
        )
        
        return {
            'archivo': archivo_info,
            'firma': firma_info,
            'carpeta_id': fecha_folder
        }
    
    def compartir_archivo(
        self,
        file_id: str,
        email: str,
        rol: str = 'reader',
        enviar_notificacion: bool = True,
        mensaje: str = None
    ) -> Dict[str, Any]:
        """
        Comparte un archivo con un usuario específico.
        
        Args:
            file_id: ID del archivo en Drive
            email: Email del usuario
            rol: 'reader', 'writer', 'commenter'
            enviar_notificacion: Si enviar email de notificación
            mensaje: Mensaje personalizado
            
        Returns:
            Información del permiso creado
        """
        service = self._get_service()
        
        permission = {
            'type': 'user',
            'role': rol,
            'emailAddress': email
        }
        
        result = service.permissions().create(
            fileId=file_id,
            body=permission,
            sendNotificationEmail=enviar_notificacion,
            emailMessage=mensaje
        ).execute()
        
        print(f"✓ Archivo compartido con {email} ({rol})")
        
        return {
            'permission_id': result.get('id'),
            'email': email,
            'rol': rol
        }
    
    def listar_archivos(self, folder_id: str = None, limite: int = 100) -> List[Dict]:
        """
        Lista archivos en una carpeta.
        
        Args:
            folder_id: ID de la carpeta (None para root)
            limite: Número máximo de resultados
            
        Returns:
            Lista de archivos
        """
        service = self._get_service()
        
        query = "trashed=false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        
        results = service.files().list(
            q=query,
            pageSize=limite,
            fields="files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)"
        ).execute()
        
        return results.get('files', [])
    
    def obtener_link_archivo(self, file_id: str) -> str:
        """
        Obtiene el link de visualización de un archivo.
        
        Args:
            file_id: ID del archivo
            
        Returns:
            URL de visualización
        """
        service = self._get_service()
        
        file = service.files().get(
            fileId=file_id,
            fields='webViewLink'
        ).execute()
        
        return file.get('webViewLink')


# Singleton para uso global
_drive_service = None

def get_drive_service() -> GoogleDriveService:
    """Obtiene la instancia singleton del servicio de Drive."""
    global _drive_service
    if _drive_service is None:
        _drive_service = GoogleDriveService()
    return _drive_service

