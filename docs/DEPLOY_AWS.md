# 🚀 Guía de Despliegue en AWS / VM

## Índice
1. [Requisitos Previos](#requisitos-previos)
2. [Opción A: EC2 (AWS)](#opción-a-ec2-aws)
3. [Opción B: Máquina Virtual](#opción-b-máquina-virtual)
4. [Configuración SSL/TLS](#configuración-ssltls)
5. [Configuración VPN (Opcional)](#configuración-vpn-opcional)
6. [Google Drive API](#google-drive-api)
7. [Gmail / SMTP](#gmail--smtp)
8. [Monitoreo y Mantenimiento](#monitoreo-y-mantenimiento)

---

## Requisitos Previos

### Software Necesario
- Python 3.10+
- MongoDB Atlas o MongoDB local
- Git
- Nginx (recomendado como reverse proxy)
- Certbot (para SSL con Let's Encrypt)

### Puertos Requeridos
| Puerto | Servicio | Descripción |
|--------|----------|-------------|
| 80 | HTTP | Redirección a HTTPS |
| 443 | HTTPS | Flask (producción) |
| 5001 | WSS | WebSocket seguro |
| 22 | SSH | Acceso remoto |

---

## Opción A: EC2 (AWS)

### 1. Crear Instancia EC2

```bash
# Recomendación mínima:
# - Tipo: t2.small o t3.small
# - AMI: Ubuntu Server 22.04 LTS
# - Almacenamiento: 20 GB SSD
# - Security Group: Abrir puertos 22, 80, 443, 5001
```

### 2. Configurar Security Group

```
Inbound Rules:
- SSH (22): Tu IP
- HTTP (80): 0.0.0.0/0
- HTTPS (443): 0.0.0.0/0
- Custom TCP (5001): 0.0.0.0/0  # WebSocket
```

### 3. Conectar a la Instancia

```bash
# Dar permisos a la clave
chmod 400 tu-clave.pem

# Conectar
ssh -i tu-clave.pem ubuntu@tu-ip-publica
```

### 4. Instalar Dependencias

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python y herramientas
sudo apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx

# Instalar Node.js (opcional, para herramientas de build)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 5. Clonar y Configurar Proyecto

```bash
# Clonar repositorio
cd /home/ubuntu
git clone https://tu-repositorio.git chat-seguro
cd chat-seguro

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requsitos.txt

# Crear archivo .env
cp env.example .env
nano .env  # Editar con tus valores
```

### 6. Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/chat-seguro
```

```nginx
# /etc/nginx/sites-available/chat-seguro

upstream flask_app {
    server 127.0.0.1:5000;
}

upstream websocket_server {
    server 127.0.0.1:5001;
}

server {
    listen 80;
    server_name tu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com;

    # SSL (se configurará con Certbot)
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
    
    # Configuración SSL segura
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    # Headers de seguridad
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000" always;

    # Archivos estáticos
    location /static/ {
        alias /home/ubuntu/chat-seguro/static/;
        expires 30d;
    }

    # WebSocket
    location /ws {
        proxy_pass http://websocket_server;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }

    # Flask App
    location / {
        proxy_pass http://flask_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Uploads
    client_max_body_size 50M;
}
```

```bash
# Activar sitio
sudo ln -s /etc/nginx/sites-available/chat-seguro /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Obtener Certificado SSL (Let's Encrypt)

```bash
sudo certbot --nginx -d tu-dominio.com
```

### 8. Crear Servicio Systemd

```bash
sudo nano /etc/systemd/system/chat-seguro.service
```

```ini
[Unit]
Description=Chat Seguro Flask + WebSocket
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/chat-seguro
Environment="PATH=/home/ubuntu/chat-seguro/venv/bin"
EnvironmentFile=/home/ubuntu/chat-seguro/.env
ExecStart=/home/ubuntu/chat-seguro/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Servicio para WebSocket
sudo nano /etc/systemd/system/chat-ws.service
```

```ini
[Unit]
Description=Chat Seguro WebSocket Server
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/chat-seguro
Environment="PATH=/home/ubuntu/chat-seguro/venv/bin"
EnvironmentFile=/home/ubuntu/chat-seguro/.env
ExecStart=/home/ubuntu/chat-seguro/venv/bin/python ws_server_standalone.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Activar servicios
sudo systemctl daemon-reload
sudo systemctl enable chat-seguro chat-ws
sudo systemctl start chat-seguro chat-ws
```

---

## Opción B: Máquina Virtual

### VirtualBox / VMware

1. **Crear VM con Ubuntu Server 22.04**
2. **Configurar red en modo "Bridged" o "NAT con port forwarding"**
3. **Seguir los mismos pasos de instalación que EC2**

### Port Forwarding (si usas NAT)

```
Host Port -> Guest Port
2222 -> 22 (SSH)
8080 -> 80 (HTTP)
8443 -> 443 (HTTPS)
5001 -> 5001 (WebSocket)
```

---

## Configuración SSL/TLS

### Opción 1: Let's Encrypt (Producción)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d tu-dominio.com

# Renovación automática (ya configurada)
sudo certbot renew --dry-run
```

### Opción 2: Certificados Autofirmados (Desarrollo)

```bash
cd /home/ubuntu/chat-seguro

# Generar certificados
python generar_certificados.py

# O manualmente con OpenSSL
mkdir -p certs
openssl req -x509 -newkey rsa:4096 \
    -keyout certs/key.pem \
    -out certs/cert.pem \
    -days 365 -nodes \
    -subj "/CN=localhost"
```

---

## Configuración VPN (Opcional)

### Opción 1: WireGuard (Recomendado)

```bash
# Instalar WireGuard
sudo apt install wireguard

# Generar claves
wg genkey | tee privatekey | wg pubkey > publickey

# Configurar servidor
sudo nano /etc/wireguard/wg0.conf
```

```ini
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = <CLAVE_PRIVADA_SERVIDOR>

# Permitir tráfico
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
# Cliente 1
PublicKey = <CLAVE_PUBLICA_CLIENTE>
AllowedIPs = 10.0.0.2/32
```

```bash
# Iniciar WireGuard
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0
```

### Opción 2: OpenVPN

```bash
# Instalar OpenVPN
wget https://git.io/vpn -O openvpn-install.sh
chmod +x openvpn-install.sh
sudo ./openvpn-install.sh
```

---

## Google Drive API

### 1. Crear Proyecto en Google Cloud Console

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear nuevo proyecto: "Chat Seguro"
3. Habilitar **Google Drive API**

### 2. Crear Cuenta de Servicio

1. IAM y administración → Cuentas de servicio
2. Crear cuenta de servicio
3. Descargar JSON de credenciales
4. Guardar como `credentials/google_drive_credentials.json`

### 3. Configurar en .env

```env
GOOGLE_DRIVE_CREDENTIALS=credentials/google_drive_credentials.json
```

### 4. Compartir Carpeta de Drive

Para que la cuenta de servicio pueda acceder a una carpeta:
1. Copiar el email de la cuenta de servicio (termina en @...iam.gserviceaccount.com)
2. Compartir la carpeta de Drive con ese email

---

## Gmail / SMTP

### Opción 1: Gmail con App Password

1. Habilitar 2FA en tu cuenta de Google
2. Ir a [Contraseñas de Aplicaciones](https://myaccount.google.com/apppasswords)
3. Crear nueva contraseña para "Mail"
4. Configurar en `.env`:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # Contraseña de aplicación
```

### Opción 2: Amazon SES

```env
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=AKIA...  # AWS Access Key
SMTP_PASSWORD=...   # AWS Secret Key
```

---

## Monitoreo y Mantenimiento

### Ver Logs

```bash
# Logs de Flask
sudo journalctl -u chat-seguro -f

# Logs de WebSocket
sudo journalctl -u chat-ws -f

# Logs de Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Reiniciar Servicios

```bash
sudo systemctl restart chat-seguro
sudo systemctl restart chat-ws
sudo systemctl restart nginx
```

### Actualizar Aplicación

```bash
cd /home/ubuntu/chat-seguro
git pull origin main
source venv/bin/activate
pip install -r requsitos.txt
sudo systemctl restart chat-seguro chat-ws
```

### Backup

```bash
# Backup de archivos firmados
tar -czvf backup_uploads_$(date +%Y%m%d).tar.gz uploads/

# Backup de configuración
tar -czvf backup_config_$(date +%Y%m%d).tar.gz .env certs/
```

### Monitoreo con PM2 (Alternativa)

```bash
# Instalar PM2
npm install -g pm2

# Configurar
pm2 start "gunicorn --workers 4 --bind 127.0.0.1:5000 app:app" --name chat-flask
pm2 start "python ws_server_standalone.py" --name chat-ws
pm2 save
pm2 startup
```

---

## Checklist de Seguridad

- [ ] SSL/TLS configurado con certificados válidos
- [ ] Variables de ambiente protegidas (no en Git)
- [ ] Firewall configurado (UFW / Security Groups)
- [ ] SSH solo con clave pública (deshabilitar password)
- [ ] Actualizaciones automáticas habilitadas
- [ ] Logs de auditoría activos
- [ ] Backup automatizado
- [ ] Rate limiting en Nginx
- [ ] Headers de seguridad configurados

---

## Comandos Útiles

```bash
# Ver estado de servicios
sudo systemctl status chat-seguro chat-ws nginx

# Ver uso de recursos
htop

# Ver conexiones activas
ss -tulpn

# Verificar SSL
openssl s_client -connect tu-dominio.com:443

# Test de WebSocket
websocat wss://tu-dominio.com:5001
```

---

**¿Necesitas ayuda?** Revisa los logs primero:
```bash
sudo journalctl -u chat-seguro --since "1 hour ago"
```




