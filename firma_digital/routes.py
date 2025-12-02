# firma_digital/routes.py
"""
Rutas API para Firma Digital
============================
Endpoints para gestión de firma digital de documentos.
"""

import os
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from datetime import datetime

from .firma_service import FirmaDigitalService
from .drive_service import GoogleDriveService, get_drive_service
from .email_service import EmailService, get_email_service


# Blueprint para rutas de firma
firma_bp = Blueprint('firma', __name__, url_prefix='/firma')

# Configuración
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'zip'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Servicios
firma_service = FirmaDigitalService(upload_folder=UPLOAD_FOLDER)


def archivo_permitido(filename: str) -> bool:
    """Verifica si la extensión del archivo está permitida."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def obtener_usuario_actual():
    """Obtiene el usuario de la sesión actual."""
    if 'user' not in session:
        return None
    return session['user']


# ============================================
# ENDPOINTS DE ARCHIVOS
# ============================================

@firma_bp.route('/')
def firma_home():
    """Página principal del módulo de firma."""
    usuario = obtener_usuario_actual()
    if not usuario:
        return redirect('/login')
    return render_template('firma.html')


@firma_bp.route('/subir', methods=['POST'])
def subir_archivo():
    """
    Sube un archivo para firma.
    
    Request:
        - file: Archivo (PDF, TXT, ZIP)
        
    Response:
        - archivo_id: ID del archivo subido
        - nombre: Nombre del archivo
        - tamaño: Tamaño en bytes
    """
    usuario = obtener_usuario_actual()
    if not usuario:
        return jsonify({'error': 'No autenticado'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    
    archivo = request.files['file']
    
    if archivo.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400
    
    if not archivo_permitido(archivo.filename):
        return jsonify({
            'error': f'Tipo de archivo no permitido. Usa: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    # Verificar tamaño
    archivo.seek(0, 2)  # Ir al final
    size = archivo.tell()
    archivo.seek(0)  # Volver al inicio
    
    if size > MAX_FILE_SIZE:
        return jsonify({
            'error': f'Archivo muy grande. Máximo: {MAX_FILE_SIZE // (1024*1024)} MB'
        }), 400
    
    # Guardar archivo
    filename = secure_filename(archivo.filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    nombre_unico = f"{timestamp}_{filename}"
    
    ruta_destino = os.path.join(UPLOAD_FOLDER, 'pendientes', nombre_unico)
    os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
    archivo.save(ruta_destino)
    
    return jsonify({
        'exito': True,
        'archivo_id': nombre_unico,
        'nombre': filename,
        'tamaño': size,
        'ruta': ruta_destino
    })


@firma_bp.route('/pendientes', methods=['GET'])
def listar_pendientes():
    """Lista archivos pendientes de firma."""
    usuario = obtener_usuario_actual()
    if not usuario:
        return jsonify({'error': 'No autenticado'}), 401
    
    archivos = firma_service.listar_archivos_pendientes()
    return jsonify(archivos)


@firma_bp.route('/firmados', methods=['GET'])
def listar_firmados():
    """Lista archivos ya firmados."""
    usuario = obtener_usuario_actual()
    if not usuario:
        return jsonify({'error': 'No autenticado'}), 401
    
    archivos = firma_service.listar_archivos_firmados()
    return jsonify(archivos)


# ============================================
# ENDPOINTS DE FIRMA
# ============================================

@firma_bp.route('/firmar', methods=['POST'])
def firmar_archivo():
    """
    Firma un archivo digitalmente.
    
    Request JSON:
        - archivo_id: ID del archivo a firmar
        - razon: Razón de la firma (opcional)
        
    Response:
        - Información de la firma generada
    """
    usuario = obtener_usuario_actual()
    if not usuario:
        return jsonify({'error': 'No autenticado'}), 401
    
    data = request.json or {}
    archivo_id = data.get('archivo_id')
    razon = data.get('razon', 'Firma digital de documento')
    
    if not archivo_id:
        return jsonify({'error': 'Se requiere archivo_id'}), 400
    
    # Buscar archivo
    archivo_path = os.path.join(UPLOAD_FOLDER, 'pendientes', archivo_id)
    
    if not os.path.exists(archivo_path):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    try:
        resultado = firma_service.firmar_archivo(
            archivo_path=archivo_path,
            firmante_id=usuario.get('_id'),
            firmante_nombre=usuario.get('name'),
            firmante_email=usuario.get('email'),
            razon=razon
        )
        
        # Eliminar de pendientes
        os.remove(archivo_path)
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@firma_bp.route('/verificar', methods=['POST'])
def verificar_firma():
    """
    Verifica la firma de un archivo.
    
    Request:
        - file: Archivo a verificar
        - signature: Archivo de firma (.sig)
        
    Response:
        - Resultado de la verificación
    """
    if 'file' not in request.files or 'signature' not in request.files:
        return jsonify({'error': 'Se requieren archivo y firma'}), 400
    
    archivo = request.files['file']
    firma = request.files['signature']
    
    # Guardar temporalmente
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as tmp_archivo:
        archivo.save(tmp_archivo.name)
        archivo_path = tmp_archivo.name
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.sig') as tmp_firma:
        firma.save(tmp_firma.name)
        firma_path = tmp_firma.name
    
    try:
        resultado = firma_service.verificar_archivo_firmado(archivo_path, firma_path)
        return jsonify(resultado)
    finally:
        # Limpiar archivos temporales
        os.unlink(archivo_path)
        os.unlink(firma_path)


@firma_bp.route('/descargar/<archivo_id>')
def descargar_archivo(archivo_id):
    """Descarga un archivo firmado."""
    usuario = obtener_usuario_actual()
    if not usuario:
        return jsonify({'error': 'No autenticado'}), 401
    
    # Buscar en firmados
    archivo_path = os.path.join(UPLOAD_FOLDER, 'firmados', archivo_id)
    
    if not os.path.exists(archivo_path):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    return send_file(archivo_path, as_attachment=True)


@firma_bp.route('/previsualizar/<archivo_id>')
def previsualizar_archivo(archivo_id):
    """
    Previsualiza un archivo pendiente de firma.
    Requiere autenticación y permiso de lectura (via token o ser el propietario).
    """
    usuario = obtener_usuario_actual()
    token = request.args.get('token') or session.get('firma_token')
    
    # Verificar autenticación
    if not usuario and not token:
        return jsonify({'error': 'No autenticado'}), 401
    
    # Si hay token, verificar que tenga permiso de lectura
    if token:
        email_service = get_email_service()
        validacion = email_service.validar_token(token)
        
        if not validacion.get('valido'):
            return jsonify({'error': 'Token inválido o expirado'}), 401
        
        if 'lectura' not in validacion.get('permisos', []):
            return jsonify({'error': 'No tienes permiso para ver este documento'}), 403
        
        # Verificar que el archivo del token coincida
        if validacion.get('archivo_id') != archivo_id:
            return jsonify({'error': 'No tienes acceso a este documento'}), 403
        
        # Verificar que el usuario logueado sea el autorizado
        if usuario:
            email_autorizado = validacion.get('usuario_email', '').lower()
            email_usuario = usuario.get('email', '').lower()
            if email_usuario != email_autorizado:
                return jsonify({'error': 'No tienes acceso a este documento'}), 403
    
    # Buscar archivo en pendientes
    archivo_path = os.path.join(UPLOAD_FOLDER, 'pendientes', archivo_id)
    
    if not os.path.exists(archivo_path):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    # Determinar el tipo MIME
    extension = os.path.splitext(archivo_id)[1].lower()
    mime_types = {
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.zip': 'application/zip'
    }
    mimetype = mime_types.get(extension, 'application/octet-stream')
    
    # Para PDF y TXT, mostrar en el navegador; para ZIP, descargar
    if extension in ['.pdf', '.txt']:
        return send_file(archivo_path, mimetype=mimetype, as_attachment=False)
    else:
        return send_file(archivo_path, as_attachment=True)


@firma_bp.route('/info-archivo/<archivo_id>')
def info_archivo(archivo_id):
    """
    Obtiene información de un archivo pendiente.
    Requiere autenticación.
    """
    usuario = obtener_usuario_actual()
    token = request.args.get('token') or session.get('firma_token')
    
    if not usuario and not token:
        return jsonify({'error': 'No autenticado'}), 401
    
    # Verificar token si existe
    if token:
        email_service = get_email_service()
        validacion = email_service.validar_token(token)
        
        if not validacion.get('valido'):
            return jsonify({'error': 'Token inválido'}), 401
        
        if validacion.get('archivo_id') != archivo_id:
            return jsonify({'error': 'No tienes acceso a este documento'}), 403
    
    archivo_path = os.path.join(UPLOAD_FOLDER, 'pendientes', archivo_id)
    
    if not os.path.exists(archivo_path):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    stat = os.stat(archivo_path)
    extension = os.path.splitext(archivo_id)[1].lower()
    
    return jsonify({
        'nombre': archivo_id,
        'tamaño': stat.st_size,
        'extension': extension,
        'puede_previsualizar': extension in ['.pdf', '.txt'],
        'fecha_subida': datetime.fromtimestamp(stat.st_mtime).isoformat()
    })


# ============================================
# ENDPOINTS DE AUTORIZACIÓN
# ============================================

@firma_bp.route('/solicitar-autorizacion', methods=['POST'])
def solicitar_autorizacion():
    """
    Envía una solicitud de autorización por email.
    Solo permite enviar a usuarios registrados en el sistema.
    
    Request JSON:
        - archivo_id: ID del archivo
        - email_autorizado: Email de quien puede firmar (debe ser usuario registrado)
        - nombre_autorizado: Nombre del autorizado
        - mensaje: Mensaje adicional (opcional)
        
    Response:
        - Confirmación del envío
    """
    usuario = obtener_usuario_actual()
    if not usuario:
        return jsonify({'error': 'No autenticado'}), 401
    
    data = request.json or {}
    archivo_id = data.get('archivo_id')
    email_autorizado = data.get('email_autorizado')
    nombre_autorizado = data.get('nombre_autorizado', email_autorizado)
    mensaje = data.get('mensaje')
    
    if not archivo_id or not email_autorizado:
        return jsonify({'error': 'Se requieren archivo_id y email_autorizado'}), 400
    
    # Verificar que el archivo existe
    archivo_path = os.path.join(UPLOAD_FOLDER, 'pendientes', archivo_id)
    if not os.path.exists(archivo_path):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    try:
        email_service = get_email_service()
        
        # VALIDACIÓN: Verificar que el email pertenece a un usuario registrado
        verificacion = email_service.verificar_usuario_registrado(email_autorizado)
        if not verificacion.get('existe'):
            return jsonify({
                'error': 'El destinatario no está registrado en el sistema. Solo puedes enviar autorizaciones a usuarios del chat.'
            }), 400
        
        # Usar el nombre del usuario registrado si no se proporcionó
        usuario_destino = verificacion.get('usuario', {})
        if not nombre_autorizado or nombre_autorizado == email_autorizado:
            nombre_autorizado = usuario_destino.get('nombre', email_autorizado)
        
        resultado = email_service.enviar_autorizacion_firma(
            destinatario_email=email_autorizado,
            destinatario_nombre=nombre_autorizado,
            archivo_nombre=archivo_id,
            archivo_id=archivo_id,
            solicitante_nombre=usuario.get('name'),
            solicitante_id=usuario.get('_id'),
            mensaje_adicional=mensaje
        )
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@firma_bp.route('/autorizar')
def autorizar_firma():
    """
    Página de autorización de firma (desde el email).
    Requiere que el usuario esté autenticado y que su email coincida con el autorizado.
    
    Query params:
        - token: Token de autorización
    """
    token = request.args.get('token')
    
    if not token:
        return render_template('denied.html', mensaje="Token no proporcionado")
    
    email_service = get_email_service()
    validacion = email_service.validar_token(token)
    
    if not validacion.get('valido'):
        return render_template('denied.html', mensaje=validacion.get('error', 'Token inválido'))
    
    # Verificar que el usuario esté autenticado
    usuario = obtener_usuario_actual()
    if not usuario:
        # Redirigir a login con return URL
        from urllib.parse import quote
        return_url = quote(request.url, safe='')
        return redirect(f'/login?next={return_url}&msg=Debes iniciar sesión para firmar el documento')
    
    # Verificar que el email del usuario logueado coincida con el autorizado
    email_autorizado = validacion.get('usuario_email', '').lower()
    email_usuario = usuario.get('email', '').lower()
    
    if email_usuario != email_autorizado:
        return render_template('denied.html', 
                              mensaje=f"Este documento fue autorizado para {email_autorizado}. Debes iniciar sesión con esa cuenta.")
    
    # Guardar token en sesión para uso posterior
    session['firma_token'] = token
    session['firma_archivo_id'] = validacion.get('archivo_id')
    session['firma_usuario_email'] = email_autorizado
    
    # Obtener información del usuario autorizado
    usuario_info = validacion.get('usuario_info', {})
    
    return render_template('firma_autorizada.html', 
                          archivo_id=validacion.get('archivo_id'),
                          permisos=validacion.get('permisos'),
                          usuario_nombre=usuario_info.get('nombre', usuario.get('name')),
                          usuario_email=email_autorizado,
                          puede_previsualizar='lectura' in validacion.get('permisos', []))


@firma_bp.route('/ejecutar-firma-autorizada', methods=['POST'])
def ejecutar_firma_autorizada():
    """
    Ejecuta la firma con un token de autorización.
    Requiere autenticación y que el email coincida con el autorizado.
    
    Request JSON:
        - token: Token de autorización
        - razon: Razón de la firma
    """
    # Verificar autenticación
    usuario = obtener_usuario_actual()
    if not usuario:
        return jsonify({'error': 'Debes iniciar sesión para firmar'}), 401
    
    data = request.json or {}
    token = data.get('token') or session.get('firma_token')
    razon = data.get('razon', 'Firma digital autorizada')
    
    if not token:
        return jsonify({'error': 'Token no proporcionado'}), 400
    
    email_service = get_email_service()
    validacion = email_service.validar_token(token)
    
    if not validacion.get('valido'):
        return jsonify({'error': validacion.get('error')}), 401
    
    # Verificar que el email del usuario logueado coincida con el autorizado
    email_autorizado = validacion.get('usuario_email', '').lower()
    email_usuario = usuario.get('email', '').lower()
    
    if email_usuario != email_autorizado:
        return jsonify({
            'error': f'Este documento fue autorizado para {email_autorizado}. Debes usar esa cuenta.'
        }), 403
    
    if 'firma' not in validacion.get('permisos', []):
        return jsonify({'error': 'No tienes permiso para firmar'}), 403
    
    archivo_id = validacion.get('archivo_id')
    archivo_path = os.path.join(UPLOAD_FOLDER, 'pendientes', archivo_id)
    
    if not os.path.exists(archivo_path):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    # Obtener información correcta del firmante
    usuario_info = validacion.get('usuario_info', {})
    firmante_id = usuario_info.get('_id') or usuario.get('_id')
    firmante_nombre = usuario_info.get('nombre') or usuario.get('name')
    firmante_email = email_autorizado
    
    try:
        resultado = firma_service.firmar_archivo(
            archivo_path=archivo_path,
            firmante_id=firmante_id,
            firmante_nombre=firmante_nombre,
            firmante_email=firmante_email,
            razon=razon
        )
        
        # Marcar token como usado
        email_service.marcar_token_usado(token)
        
        # Limpiar sesión de firma
        session.pop('firma_token', None)
        session.pop('firma_archivo_id', None)
        session.pop('firma_usuario_email', None)
        
        # Eliminar de pendientes
        os.remove(archivo_path)
        
        # Enviar confirmación al firmante
        email_service.enviar_confirmacion_firma(
            destinatario_email=firmante_email,
            destinatario_nombre=firmante_nombre,
            archivo_nombre=archivo_id,
            hash_documento=resultado.get('hash')
        )
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# ENDPOINTS DE GOOGLE DRIVE
# ============================================

@firma_bp.route('/subir-drive', methods=['POST'])
def subir_a_drive():
    """
    Sube un archivo firmado a Google Drive.
    
    Request JSON:
        - archivo_id: ID del archivo firmado
        - compartir_con: Lista de emails para compartir
        
    Response:
        - Links del archivo en Drive
    """
    usuario = obtener_usuario_actual()
    if not usuario:
        return jsonify({'error': 'No autenticado'}), 401
    
    data = request.json or {}
    archivo_id = data.get('archivo_id')
    compartir_con = data.get('compartir_con', [])
    
    if not archivo_id:
        return jsonify({'error': 'Se requiere archivo_id'}), 400
    
    # Buscar archivo y firma
    archivo_path = os.path.join(UPLOAD_FOLDER, 'firmados', archivo_id)
    firma_path = archivo_id.replace(os.path.splitext(archivo_id)[1], '.sig')
    firma_path = os.path.join(UPLOAD_FOLDER, 'firmados', firma_path)
    
    if not os.path.exists(archivo_path):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    try:
        drive_service = get_drive_service()
        
        resultado = drive_service.subir_documento_firmado(
            archivo_path=archivo_path,
            firma_path=firma_path if os.path.exists(firma_path) else archivo_path,
            firmante_email=usuario.get('email')
        )
        
        # Compartir si se especificaron emails
        for email in compartir_con:
            drive_service.compartir_archivo(
                file_id=resultado['archivo']['id'],
                email=email,
                rol='reader',
                mensaje=f"Documento firmado compartido por {usuario.get('name')}"
            )
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@firma_bp.route('/drive/archivos')
def listar_drive():
    """Lista archivos en Google Drive."""
    usuario = obtener_usuario_actual()
    if not usuario:
        return jsonify({'error': 'No autenticado'}), 401
    
    try:
        drive_service = get_drive_service()
        archivos = drive_service.listar_archivos()
        return jsonify(archivos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# ENDPOINTS DE CERTIFICADOS
# ============================================

@firma_bp.route('/generar-certificado', methods=['POST'])
def generar_certificado():
    """
    Genera un nuevo certificado de firma.
    Solo para administradores.
    """
    usuario = obtener_usuario_actual()
    if not usuario:
        return jsonify({'error': 'No autenticado'}), 401
    
    # TODO: Verificar si es administrador
    
    data = request.json or {}
    common_name = data.get('common_name', 'Firmador Digital')
    organization = data.get('organization', 'Chat Seguro')
    
    try:
        cert_path, key_path = firma_service.generar_certificado_firma(
            common_name=common_name,
            organization=organization
        )
        
        return jsonify({
            'exito': True,
            'certificado': cert_path,
            'clave': key_path
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@firma_bp.route('/certificado/info')
def info_certificado():
    """Obtiene información del certificado de firma actual."""
    if firma_service._certificate:
        cert = firma_service._certificate
        return jsonify({
            'emisor': cert.issuer.rfc4514_string(),
            'sujeto': cert.subject.rfc4514_string(),
            'serial': str(cert.serial_number),
            'valido_desde': cert.not_valid_before.isoformat(),
            'valido_hasta': cert.not_valid_after.isoformat()
        })
    else:
        return jsonify({'error': 'No hay certificado configurado'}), 404




