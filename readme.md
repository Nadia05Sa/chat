# 🔐 CHAT GRUPAL SEGURO

> Sistema de chat en tiempo real con firma digital, cifrado de extremo a extremo y múltiples capas de seguridad.

![Version](https://img.shields.io/badge/version-4.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalación Rápida](#-instalación-rápida)
- [Configuración](#-configuración)
- [Ejecución](#-ejecución)
- [Módulos](#-módulos)
- [API Endpoints](#-api-endpoints)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Despliegue en Producción](#-despliegue-en-producción)
- [Solución de Problemas](#-solución-de-problemas)

---

## ✨ Características

### 🔒 Seguridad
| Característica | Descripción |
|----------------|-------------|
| **SSL/TLS** | HTTPS y WSS (WebSocket Secure) |
| **Variables de Ambiente** | Sin credenciales hardcodeadas |
| **AES-256-CBC** | Cifrado simétrico de mensajes |
| **HMAC-SHA256** | Verificación de integridad |
| **OAuth 2.0** | Autenticación con Google |
| **Firma Digital RSA** | Firma de documentos PDF, TXT, ZIP |

### 💬 Chat
- Canales públicos y privados
- Mensajes en tiempo real con WebSockets
- Historial de mensajes persistente
- Sistema de administradores por canal
- Comandos de chat (`/crear`, `/unir`, `/salir`, etc.)

### 📝 Firma Digital (NUEVO v4.0)
- Firma de archivos PDF, TXT y ZIP
- Verificación de firmas
- Integración con Google Drive
- Envío de autorizaciones por email
- Tokens de un solo uso

---

## 📦 Requisitos

- **Python** 3.10 o superior
- **MongoDB** (Atlas o local)
- **Node.js** (opcional, para desarrollo frontend)

### Navegador Web
- Chrome, Firefox, Edge, Safari (versiones modernas)
- Soporte para WebSockets y ES6+

---

## 🚀 Instalación Rápida

### 1. Clonar el Proyecto

```bash
git clone <tu-repositorio>
cd chat_python_v4
```

### 2. Crear Entorno Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requsitos.txt
```

### 4. Configurar Variables de Ambiente

```bash
# Windows (PowerShell)
copy env.example .env

# Linux/Mac
cp env.example .env
```

### 5. Editar `.env` con tus Valores

Abre el archivo `.env` y configura las siguientes variables **obligatorias**:

```env
# === OBLIGATORIAS ===

# Flask
FLASK_SECRET=genera_una_clave_aleatoria_aqui

# MongoDB
MONGO_URI=mongodb+srv://usuario:password@cluster.mongodb.net
DB_NAME=chat-cybersecurity

# Claves de Cifrado
AES_KEY_BASE64=<ver paso 6>
HMAC_SECRET_KEY=<ver paso 6>

# Google OAuth (obtener en Google Cloud Console)
GOOGLE_CLIENT_ID=tu_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu_client_secret
```

### 6. Generar Claves de Cifrado

```bash
# Generar AES_KEY_BASE64 (copia el resultado a .env)
python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"

# Generar HMAC_SECRET_KEY (copia el resultado a .env)
python -c "import secrets; print(secrets.token_hex(32))"

# Generar FLASK_SECRET (copia el resultado a .env)
python -c "import secrets; print(secrets.token_hex(24))"
```

### 7. Ejecutar el Proyecto

```bash
python app.py
```

### 8. Abrir en el Navegador

```
http://localhost:5000/login
```

---

## ⚙️ Configuración

### Variables de Ambiente Completas

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `FLASK_SECRET` | Clave secreta de Flask | ✅ |
| `FLASK_PORT` | Puerto de Flask (default: 5000) | ❌ |
| `FLASK_DEBUG` | Modo debug (default: false) | ❌ |
| `MONGO_URI` | URI de conexión MongoDB | ✅ |
| `DB_NAME` | Nombre de la base de datos | ✅ |
| `AES_KEY_BASE64` | Clave AES-256 en Base64 | ✅ |
| `HMAC_SECRET_KEY` | Clave para HMAC | ✅ |
| `GOOGLE_CLIENT_ID` | Client ID de Google OAuth | ✅ |
| `GOOGLE_CLIENT_SECRET` | Client Secret de Google | ✅ |
| `WS_HOST` | Host del WebSocket (default: 0.0.0.0) | ❌ |
| `WS_PORT` | Puerto del WebSocket (default: 5001) | ❌ |
| `SSL_ENABLED` | Habilitar SSL (default: false) | ❌ |
| `SSL_CERT_PATH` | Ruta al certificado SSL | ❌ |
| `SSL_KEY_PATH` | Ruta a la clave privada SSL | ❌ |

### Variables para Firma Digital (Opcional)

| Variable | Descripción |
|----------|-------------|
| `FIRMA_CERT_PATH` | Certificado para firmas |
| `FIRMA_KEY_PATH` | Clave privada para firmas |
| `UPLOAD_FOLDER` | Carpeta de uploads |
| `GOOGLE_DRIVE_CREDENTIALS` | Credenciales de Google Drive |
| `SMTP_SERVER` | Servidor SMTP |
| `SMTP_PORT` | Puerto SMTP |
| `SMTP_USER` | Usuario SMTP |
| `SMTP_PASSWORD` | Contraseña SMTP |
| `APP_BASE_URL` | URL base de la aplicación |

---

## ▶️ Ejecución

### Modo Desarrollo (Recomendado para pruebas)

```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Ejecutar
python app.py
```

**Salida esperada:**

```
======================
🚀 INICIANDO SERVIDOR
======================
[WS] Conectando Mongo...
✓ Conectado a MongoDB: chat-cybersecurity
✓ Colecciones e índices inicializados
[WS] ⚠️  SSL/TLS deshabilitado (no recomendado para producción)
[WS] Iniciando en ws://0.0.0.0:5001
🌐 Iniciando Flask en http://127.0.0.1:5000 ...
```

### Modo Producción con SSL

```bash
# 1. Generar certificados
python generar_certificados.py

# 2. Editar .env
# SSL_ENABLED=true

# 3. Ejecutar
python app.py
```

### Ejecutar Solo WebSocket (Producción)

```bash
python ws_server_standalone.py
```

### URLs Disponibles

| URL | Descripción |
|-----|-------------|
| `http://localhost:5000/login` | Página de login |
| `http://localhost:5000/chat` | Chat principal |
| `http://localhost:5000/perfil` | Perfil de usuario |
| `http://localhost:5000/firma/` | **Módulo de Firma Digital** |
| `ws://localhost:5001` | WebSocket |

---

## 📦 Módulos

### 💬 Chat (Principal)

Sistema de chat en tiempo real con:

- **Canales públicos**: Cualquier usuario puede unirse
- **Canales privados**: Solo miembros invitados
- **Comandos disponibles**:

```
/crear nombre       - Crear canal público
/crear_priv nombre  - Crear canal privado
/unir nombre        - Unirse a un canal
/salir              - Volver al canal general
/agregar email canal    - Agregar usuario (admin)
/remover email canal    - Remover usuario (admin)
/dar_admin email canal  - Dar permisos admin
/quitar_admin email canal - Quitar permisos admin
```

### 🔐 Firma Digital (v4.0)

Módulo para firmar digitalmente documentos:

**Acceso:** `http://localhost:5000/firma/`

**Funcionalidades:**

1. **Subir documentos** (PDF, TXT, ZIP hasta 50MB)
2. **Firmar documentos** con certificado digital RSA
3. **Verificar firmas** existentes
4. **Enviar autorizaciones** por email
5. **Subir a Google Drive** documentos firmados

**Configuración adicional:**

```bash
# Generar certificado de firma
python -c "from firma_digital import FirmaDigitalService; FirmaDigitalService().generar_certificado_firma()"
```

**Para Google Drive:**
1. Crear proyecto en [Google Cloud Console](https://console.cloud.google.com/)
2. Habilitar Google Drive API
3. Crear cuenta de servicio
4. Descargar credenciales JSON
5. Guardar como `credentials/google_drive_credentials.json`

**Para emails:**
- Configurar SMTP en `.env`
- Para Gmail: usar [contraseña de aplicación](https://myaccount.google.com/apppasswords)

---

## 🔌 API Endpoints

### Autenticación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/login` | Página de login |
| POST | `/login` | Login con email/password |
| POST | `/register` | Registrar usuario |
| GET | `/login_google` | Login con Google OAuth |
| GET | `/auth` | Callback de Google OAuth |
| GET | `/session_user` | Obtener usuario de sesión |

### Chat

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/chat` | Página de chat |
| GET | `/canales` | Listar todos los canales |
| GET | `/canales/<usuario_id>` | Canales del usuario |
| GET | `/usuarios` | Listar usuarios |
| GET | `/perfil/<usuario_id>` | Perfil de usuario |

### Firma Digital

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/firma/` | Panel de firma digital |
| POST | `/firma/subir` | Subir archivo |
| GET | `/firma/pendientes` | Archivos pendientes |
| GET | `/firma/firmados` | Archivos firmados |
| POST | `/firma/firmar` | Firmar archivo |
| POST | `/firma/verificar` | Verificar firma |
| POST | `/firma/solicitar-autorizacion` | Enviar autorización |
| GET | `/firma/autorizar?token=xxx` | Autorizar firma |
| POST | `/firma/subir-drive` | Subir a Google Drive |
| GET | `/firma/certificado/info` | Info del certificado |

---

## 📁 Estructura del Proyecto

```
chat_python_v4/
│
├── 📄 app.py                    # Punto de entrada principal
├── 📄 config.py                 # Configuración y variables de ambiente
├── 📄 db_manager.py             # Gestor de MongoDB
├── 📄 index.py                  # Rutas principales (auth, chat)
├── 📄 ws_server.py              # Servidor WebSocket
├── 📄 ws_server_standalone.py   # WebSocket standalone (producción)
├── 📄 manejadores.py            # Lógica de mensajes WebSocket
├── 📄 security.py               # Cifrado AES, HMAC, auditoría
├── 📄 generar_certificados.py   # Generador de certificados SSL
│
├── 📁 firma_digital/            # Módulo de Firma Digital
│   ├── __init__.py
│   ├── firma_service.py         # Servicio de firma RSA
│   ├── drive_service.py         # Google Drive API
│   ├── email_service.py         # Envío de emails
│   └── routes.py                # Endpoints de firma
│
├── 📁 static/
│   ├── css/
│   │   └── index.css
│   └── js/
│       ├── chat.js              # Lógica del chat
│       └── login.js             # Lógica de login
│
├── 📁 templates/
│   ├── chat.html
│   ├── login.html
│   ├── perfil.html
│   ├── denied.html
│   ├── firma.html               # Panel de firma digital
│   └── firma_autorizada.html    # Autorización de firma
│
├── 📁 docs/
│   └── DEPLOY_AWS.md            # Guía de despliegue
│
├── 📁 uploads/                  # Archivos subidos (generado)
│   ├── pendientes/
│   └── firmados/
│
├── 📁 certs/                    # Certificados SSL (generado)
│
├── 📄 env.example               # Plantilla de variables
├── 📄 requsitos.txt             # Dependencias Python
└── 📄 readme.md                 # Este archivo
```

---

## 🌐 Despliegue en Producción

Ver la guía completa en [`docs/DEPLOY_AWS.md`](docs/DEPLOY_AWS.md)

### Resumen Rápido

1. **Servidor**: AWS EC2, DigitalOcean, o VM con Ubuntu 22.04
2. **Reverse Proxy**: Nginx
3. **SSL**: Let's Encrypt (Certbot)
4. **Proceso**: Systemd o PM2

```bash
# Instalar Gunicorn para producción
pip install gunicorn

# Ejecutar Flask con Gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 app:app

# Ejecutar WebSocket en paralelo
python ws_server_standalone.py
```

---

## 🔧 Solución de Problemas

### Error: "FLASK_SECRET no está configurada"

```bash
# Verifica que .env existe y tiene la variable
cat .env | grep FLASK_SECRET

# Genera una nueva clave
python -c "import secrets; print(secrets.token_hex(24))"
```

### Error: "AES_KEY_BASE64 no está configurada"

```bash
# Genera la clave y agrégala a .env
python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

### Error: "MONGO_URI no está configurada"

Verifica tu conexión a MongoDB Atlas o local en el archivo `.env`.

### WebSocket no conecta

1. Verifica que el puerto 5001 esté libre
2. Revisa el firewall
3. En producción, asegúrate de usar WSS con SSL

```bash
# Ver puertos en uso
netstat -ano | findstr :5001
```

### Error de certificados SSL

```bash
# Regenerar certificados
python generar_certificados.py
```

---

## 📜 Historial de Versiones

### v4.0.0 (Actual)
- ✅ Módulo de Firma Digital completo
- ✅ Integración con Google Drive
- ✅ Envío de emails con autorización
- ✅ Interfaz web para firmas
- ✅ Documentación de despliegue AWS/VM

### v3.5.0
- ✅ Variables de ambiente (sin hardcoding)
- ✅ SSL/TLS para Flask y WebSocket
- ✅ Detección automática WS/WSS

### v3.0.0
- ✅ Sistema de canales públicos y privados
- ✅ OAuth con Google
- ✅ MongoDB para persistencia
- ✅ Auditoría de mensajes

---

## 👥 Equipo

- **Equipo de Ciberseguridad**

## 📄 Licencia

MIT License - Ver archivo LICENSE

---

**Última actualización:** 25/11/2025  
**Versión del documento:** 4.0
