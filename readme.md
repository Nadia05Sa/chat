# CHAT GRUPAL SEGURO - DOCUMENTACIÓN

=====================================

## INFORMACIÓN DEL PROYECTO

- Nombre: Chat Grupal Seguro
- Versión Actual: v4.0.0
- Fecha de Inicio: 18/11/2025
- EQUIPO DE CIBERSEGURIDAD

## DESCRIPCIÓN

Sistema de chat grupal en tiempo real con arquitectura híbrida (Flask + WebSockets) y múltiples capas de seguridad, diseñado para cumplir requisitos estrictos de integridad, confidencialidad y auditoría.

Incluye:

### SEGURIDAD

 - AES-256-CBC
 - HMAC-SHA256
 - SHA-256 para auditoría
 - Sanidad avanzada de caracteres
 - Padding PKCS7
 - Validación de integridad antes del descifrado

### BACKEND

- Servidor WebSocket dedicado
- API REST con Flask
- Manejo de canales y usuarios
- Sistema de auditoría con archivo de logs

### FRONTEND

- Cliente moderno con:
- Web Crypto API
- Manejo de canales
- Pantallas: login, chat, perfil, acceso denegado
- Validación de comandos
- Protección del historial para usuarios no autenticados

## REQUISITOS DEL SISTEMA

### Python (Servidor)

-Python 3.10+
-Dependencias:
pip install websockets cryptography flask pymongo

### Cliente Web (Frontend)

- Navegador web moderno con soporte para:
  - WebSockets
  - Web Crypto API
  - ES6+ JavaScript

## INSTALACIÓN

1. Instalar dependencias de Python:

   ```
   pip install -r requisitos.txt
   ```

2. Configurar claves en config.py

Incluye:

- AES_KEY (32 bytes)
- CLAVE_SECRETA (HMAC)
- ENABLE_AUDIT
- AUDIT_LOG_FILE

3. Configurar archivo .env

Incluye:

- FLASK_SECRET
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET

4. Iniciar servidor Flask + WebSocket

   ```
      python app.py
   ```

5. Abrir el cliente

Abrir en navegador: http://localhost:5000/login

## ESTRUCTURA DE ARCHIVOS

```
chat_python_v3/
├── __pycache__
│
├── static/
│   ├── css/
│   │   └── index.css
│   └── js/
│       ├── chat.js        # Lógica principal del chat
│       ├── login.js       # Lógica de inicio de sesión
│       └── crypto.js      # Cifrado AES, HMAC, derivación de claves
│
├── templates/
│   ├── chat.html
│   ├── login.html
│   ├── denied.html
│   └── perfil.html
│
├── .env                 # Variables de entorno
│
├── app.py                 # Arranque Flask + coordinación con WebSocket
├── config.py              # Claves, configuración de seguridad, rutas de log
├── db_manager.py          # MongoDB: usuarios, canales, mensajes
├── index.py               # API REST (autenticación, perfiles, canales)
├── keys.py                # Generación RSA opcional
├── fernet_generator.py    # Genera claves Fernet (uso opcional)
├── calcular_md5.py        # Hash MD5 para integridad de archivos
├── security.py            # AES, HMAC, SHA256, auditoría, sanitización
├── manejadores.py         # Lógica de mensajes WS y validación de paquetes
└── ws_server.py           # Servidor WebSocket independiente
```

## HISTORIAL DE VERSIONES

### v1.0.0 (18/11/2025)

**Archivos:**

- chat_server.py (MD5: PENDIENTE_CALCULAR)
- index.html (MD5: PENDIENTE_CALCULAR)

**Características Implementadas:**
✓ Servidor WebSocket básico
✓ Cifrado AES-256-CBC
✓ HMAC-SHA256 para integridad
✓ Interfaz de usuario moderna
✓ Lista de usuarios en tiempo real
✓ Manejo de múltiples conexiones simultáneas

**Seguridad:**

- Cifrado simétrico de 256 bits
- Verificación de integridad con HMAC
- IV aleatorio por mensaje
- Padding PKCS7

**Pendiente para v1.1.0:**

- Implementar hash SHA-256 de mensajes
- Agregar logs de auditoría
- Implementar múltiples salas de chat
- Agregar autenticación de usuarios

## CONFIGURACIÓN DE SEGURIDAD

### Claves de Cifrado

**IMPORTANTE:** Las claves deben ser idénticas en servidor y cliente.

**Servidor (chat_server.py):**

```python
AES_KEY = bytes([...])  # 32 bytes para AES-256
CLAVE_SECRETA = b"clave_super_secreta"  # Para HMAC
```

**Cliente (index.html):**

```javascript
const AES_KEY = new Uint8Array([...]);  // Mismos 32 bytes
const CLAVE_SECRETA = "clave_super_secreta";  // Misma clave
```

### Generar Claves Seguras

Para producción, generar claves aleatorias:

```python
import secrets
key = secrets.token_bytes(32)
print(f"Nueva clave: bytes({list(key)})")
```

## ARQUITECTURA DE SEGURIDAD

### Flujo de Cifrado (Cliente → Servidor)

1. Usuario escribe mensaje en texto plano
2. Se genera IV aleatorio de 16 bytes
3. Mensaje se cifra con AES-256-CBC
4. Se aplica padding PKCS7
5. Se calcula HMAC-SHA256 del (IV + ciphertext)
6. Se envía: base64(IV+ciphertext)|HMAC_hex
7. Servidor verifica HMAC
8. Servidor descifra con AES-256-CBC
9. Servidor remueve padding
10. Mensaje se distribuye a otros usuarios

### Formato de Paquete

```
[IV:16bytes][Ciphertext:variable] | [HMAC:64chars_hex]
         ↓                              ↓
    Base64 URL-safe                 Hexadecimal
```

## USO DEL SISTEMA

### Iniciar Servidor

```bash
python app.py
```

Salida esperada:

```
✓ Longitud de AES_KEY: 32 bytes = 256 bits
============================================================
🚀 Servidor WebSocket Iniciado
📡 Escuchando en: ws://0.0.0.0:5001
🔐 Cifrado: AES-256-CBC + HMAC-SHA256
============================================================
```

### Conectar Cliente

1. Abrir index.html en navegador
2. Ingresar nombre de usuario cuando se solicite
3. Comenzar a chatear

### Verificar Conexión

En la consola del navegador (F12) debe aparecer:

```
✓ Longitud de AES_KEY: 32 bytes = 256 bits
✓ Conectado al servidor WebSocket
```

## SOLUCIÓN DE PROBLEMAS

### Error: "could not bind on any address"

- Verifica que el puerto 5001 no esté en uso
- Ejecuta: `netstat -ano | findstr :5001`
- Cambia IP_SERVIDOR a "0.0.0.0" o "localhost"

### Error: "Invalid key size"

- Las claves AES_KEY deben tener exactamente 32 bytes
- Verifica que cliente y servidor usen la misma clave
- Revisa los logs de debug en consola

### Error: "HMAC inválido"

- La CLAVE_SECRETA debe ser idéntica en cliente y servidor
- Verifica que no haya espacios extra o caracteres ocultos
- Asegúrate de usar la misma codificación (UTF-8)

### No se conecta el WebSocket

- Verifica la IP y puerto en index.html
- Si el servidor usa 0.0.0.0, el cliente debe usar la IP real
- Revisa el firewall y permisos de red

## SEGURIDAD Y MEJORES PRÁCTICAS

### ⚠️ ADVERTENCIAS DE SEGURIDAD

1. **NO usar en producción sin cambiar las claves por defecto**
2. **NO compartir las claves de cifrado públicamente**
3. **Usar HTTPS/WSS en entornos de producción**
4. **Implementar rate limiting para prevenir spam**
5. **Sanitizar entrada de usuario para prevenir XSS**

### Recomendaciones

- Cambiar claves cada 30-90 días
- Usar certificados SSL/TLS válidos
- Implementar autenticación de usuarios
- Agregar logs de auditoría
- Hacer respaldos periódicos
- Monitorear conexiones sospechosas

### v1.1.0

- [ ] Hash SHA-256 de mensajes para auditoría
- [ ] Logs detallados con timestamps
- [ ] Archivo de registro de mensajes

### v1.2.0

- [ ] Múltiples salas de chat
- [ ] Mensajes privados entre usuarios
- [ ] Historial de mensajes

### v1.3.0

- [ ] Autenticación de usuarios
- [ ] Perfiles de usuario
- [ ] Administración de permisos

### v2.0.0

- [ ] Base de datos persistente
- [ ] Cifrado de extremo a extremo
- [ ] Compartir archivos cifrados

### v3.0.0 – Actual (18/11/2025)

✔ Nuevo en esta versión:

- Reestructuración completa del proyecto
- security.py con:
      - AES-256-CBC robusto
      - HMAC-SHA256
      - SHA-256 para auditoría
      - Sanitización de caracteres
- Auditoría habilitada con ENABLE_AUDIT
- WebSocket separado (ws_server.py)
- API REST con Flask (index.py)
- Múltiples canales con MongoDB
- Manejo de sesiones, perfiles y acceso denegado
- Cliente reorganizado en pantallas
- Validación de comandos en el frontend
- Limpieza de historial al salir

FLUJO DE SEGURIDAD (v3.0.0)
1. Cliente → Servidor

Texto plano → UTF-8

AES-256-CBC con:
- IV aleatorio
- PKCS7

Se genera:
- cipher = IV + ciphertext
- hmac = HMAC_SHA256(cipher)

Cliente envía:

{
  "mensaje": "<base64>",
  "hmac": "<hex>",
  "canal_id": "...",
  "fecha": "ISO8601"
}

2. Servidor valida

- Valida HMAC
- Descifra AES
- Sanitiza texto
- Calcula SHA-256 para auditoría
- Registra log si ENABLE_AUDIT = True

3. Servidor → Otros usuarios

Reenvía mensaje en texto plano con usuario, fecha, canal, contenido.

## SISTEMA DE AUDITORÍA (v3.0.0)
Ubicación:
logs/audit.log

Cada entrada incluye:

- Timestamp
- Usuario
- Hash SHA-256
- Longitud del mensaje
- Canal

Ejemplo:

[2025-11-18 22:11:03] | usuario123 | 2a9c...ff12 |   45 chars

## CONFIGURACIÓN DE SEGURIDAD
# Generar AES_KEY segura:
import secrets
key = secrets.token_bytes(32)
print(list(key))

# Generar clave HMAC:
import secrets
secrets.token_bytes(64)

### SOLUCIÓN DE PROBLEMAS
# HMAC inválido
✔ Desincronización de CLAVE_SECRETA
✔ Mensaje alterado
✔ Diferente codificación

# AES falla al descifrar
✔ Clave incorrecta
✔ IV corrupto
✔ Padding inválido

# No se conecta WebSocket
✔ Revisar IP en chat.js
✔ Puerto bloqueado
✔ Firewall

## ROADMAP FUTURO
- Implementación de endpoint para inicio de sesión con Goolgle OAuth
- Correccion de de detalles en frontend
- Implementación de algunas nuevas características implementadas ya en el servidor

## CONTACTO Y SOPORTE

- Desarrollador: [Tu Email]
- Repositorio: [URL del repositorio]
- Documentación: Ver CONTROL_CAMBIOS.txt

## LICENCIA

[Especificar licencia del proyecto]

## NOTAS FINALES

Este sistema está diseñado para comunicaciones seguras en entornos
controlados. Para uso en producción, se recomienda auditoría de
seguridad profesional.

---

Última actualización: 15/10/2025
Versión del documento: 2.0
