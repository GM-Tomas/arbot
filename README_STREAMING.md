# 🤖 Sistema de Arbitraje Triangular - Streaming en Tiempo Real

Este sistema proporciona una API de streaming y un dashboard web para monitorear oportunidades de arbitraje triangular en tiempo real usando datos de Binance.

## 🚀 Características

- **API de Streaming**: FastAPI con WebSocket para datos en tiempo real
- **Dashboard Web**: Interfaz interactiva con Dash y Plotly
- **Monitoreo de Precios**: Velas de 1 minuto de múltiples pares
- **Detección de Arbitraje**: Búsqueda automática de oportunidades triangulares
- **Actualizaciones en Tiempo Real**: WebSocket para actualizaciones instantáneas
- **Gráficos Interactivos**: Visualización de precios y oportunidades

## 📁 Estructura del Proyecto

```
Arbitbot/
├── api/
│   ├── streaming_api.py    # API FastAPI con WebSocket
│   └── config.py          # Configuración para diferentes entornos
├── web/
│   └── dashboard.py       # Dashboard Dash
├── classes/               # Clases del bot original
├── start_arbitrage_system.py  # Script de inicio completo
└── README_STREAMING.md    # Este archivo
```

## 🛠️ Instalación

### 1. Instalar Dependencias

```bash
pip install -r support/requirements.txt
```

### 2. Configurar Credenciales

Edita `input/config.json` con tus credenciales de Binance:

```json
{
    "binance": {
        "api_key": "tu_api_key",
        "api_secret": "tu_api_secret"
    }
}
```

### 3. Ejecutar el Sistema

```bash
python start_arbitrage_system.py
```

## 🌐 Acceso al Sistema

Una vez ejecutado, accede a:

- **Dashboard Web**: http://localhost:8050
- **API REST**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws

## 📊 Endpoints de la API

### REST Endpoints

- `GET /` - Información de la API
- `GET /api/prices` - Precios actuales de todos los pares
- `GET /api/prices/{symbol}` - Historial de precios de un par específico
- `GET /api/opportunities` - Oportunidades de arbitraje encontradas
- `GET /api/status` - Estado del sistema
- `GET /api/stream/prices` - Stream de precios (Server-Sent Events)

### WebSocket

- `ws://localhost:8000/ws` - WebSocket para actualizaciones en tiempo real

**Mensajes enviados por WebSocket:**
```json
{
    "type": "price_update",
    "data": {
        "symbol": "BTCUSDT",
        "price": 50000.0,
        "timestamp": 1640995200000,
        "datetime": "2022-01-01T00:00:00"
    }
}
```

```json
{
    "type": "arbitrage_opportunity",
    "data": {
        "id": 1,
        "route": "BTCUSDT -> ETHUSDT -> BNBUSDT",
        "profit_percentage": 0.75,
        "timestamp": "2022-01-01T00:00:00",
        "prices": {
            "BTCUSDT": 50000.0,
            "ETHUSDT": 3000.0,
            "BNBUSDT": 400.0
        }
    }
}
```

## 🏗️ Hosting y Despliegue

### Opción 1: VPS/Servidor Dedicado (Recomendado)

**Ventajas:**
- Control total del servidor
- Mejor rendimiento
- Costo fijo mensual
- SSL/TLS personalizado

**Proveedores Recomendados:**
- DigitalOcean ($5-20/mes)
- Linode ($5-20/mes)
- Vultr ($2.50-20/mes)
- AWS EC2 (pay-as-you-go)

**Configuración:**

1. **Instalar dependencias:**
```bash
sudo apt update
sudo apt install python3 python3-pip nginx certbot python3-certbot-nginx
```

2. **Configurar firewall:**
```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

3. **Crear usuario para la aplicación:**
```bash
sudo adduser arbitrage
sudo usermod -aG sudo arbitrage
```

4. **Configurar systemd service:**
```bash
sudo nano /etc/systemd/system/arbitrage-api.service
```

```ini
[Unit]
Description=Arbitraje Triangular API
After=network.target

[Service]
Type=simple
User=arbitrage
WorkingDirectory=/home/arbitrage/arbitbot
Environment=ENVIRONMENT=production
ExecStart=/usr/bin/python3 api/streaming_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

5. **Configurar nginx:**
```bash
sudo nano /etc/nginx/sites-available/arbitrage
```

```nginx
server {
    listen 80;
    server_name tu-dominio.com;
    
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location / {
        proxy_pass http://localhost:8050;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

6. **Activar configuración:**
```bash
sudo ln -s /etc/nginx/sites-available/arbitrage /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

7. **Configurar SSL:**
```bash
sudo certbot --nginx -d tu-dominio.com
```

8. **Iniciar servicios:**
```bash
sudo systemctl enable arbitrage-api
sudo systemctl start arbitrage-api
```

### Opción 2: Cloud Platforms

#### Heroku

1. **Crear Procfile:**
```
web: uvicorn api.streaming_api:main --host 0.0.0.0 --port $PORT
```

2. **Crear runtime.txt:**
```
python-3.9.18
```

3. **Desplegar:**
```bash
heroku create tu-app-name
git push heroku main
```

#### Railway

1. **Conectar repositorio a Railway**
2. **Configurar variables de entorno:**
   - `ENVIRONMENT=cloud`
   - `PORT=$PORT`

#### Render

1. **Crear nuevo Web Service**
2. **Configurar:**
   - Build Command: `pip install -r support/requirements.txt`
   - Start Command: `uvicorn api.streaming_api:main --host 0.0.0.0 --port $PORT`

### Opción 3: Docker

1. **Crear Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY support/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 8050

CMD ["python", "start_arbitrage_system.py"]
```

2. **Crear docker-compose.yml:**
```yaml
version: '3.8'

services:
  arbitrage-system:
    build: .
    ports:
      - "8000:8000"
      - "8050:8050"
    environment:
      - ENVIRONMENT=production
    volumes:
      - ./output:/app/output
    restart: unless-stopped
```

3. **Ejecutar:**
```bash
docker-compose up -d
```

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# Entorno
ENVIRONMENT=production  # development, production, cloud

# Servidor
HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Seguridad
SECRET_KEY=tu-clave-secreta-aqui

# Base de datos (opcional)
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

### Personalización de Pares

Edita `api/config.py` para cambiar los pares monitoreados:

```python
BINANCE_ASSETS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT',
    'SOLUSDT', 'MATICUSDT', 'LINKUSDT', 'UNIUSDT', 'AVAXUSDT'
]
```

### Configuración de Arbitraje

```python
ARBITRAGE_MIN_PROFIT = 0.5  # 0.5% mínimo
ARBITRAGE_MAX_OPPORTUNITIES = 50  # Máximo oportunidades guardadas
```

## 📈 Monitoreo y Logs

### Logs de la API

Los logs se guardan en `output/api.log`:

```bash
tail -f output/api.log
```

### Métricas del Sistema

Accede a `/api/status` para ver:
- Estado del WebSocket
- Clientes conectados
- Símbolos monitoreados
- Oportunidades encontradas

### Monitoreo de Recursos

```bash
# Uso de CPU y memoria
htop

# Logs del sistema
journalctl -u arbitrage-api -f

# Estado de nginx
sudo systemctl status nginx
```

## 🔒 Seguridad

### Recomendaciones

1. **Firewall**: Solo abrir puertos necesarios (80, 443, 22)
2. **SSL/TLS**: Usar certificados válidos
3. **Rate Limiting**: Implementar límites de requests
4. **Autenticación**: Agregar autenticación si es necesario
5. **Logs**: Monitorear logs regularmente
6. **Backups**: Hacer backups de configuración y datos

### Configuración de Seguridad

```python
# En api/config.py
RATE_LIMIT_REQUESTS = 100  # requests por minuto
RATE_LIMIT_WINDOW = 60     # ventana en segundos

# CORS más restrictivo para producción
CORS_ORIGINS = [
    "https://tu-dominio.com",
    "https://www.tu-dominio.com"
]
```

## 🚨 Troubleshooting

### Problemas Comunes

1. **API no responde:**
   - Verificar que el puerto 8000 esté libre
   - Revisar logs en `output/api.log`
   - Verificar credenciales de Binance

2. **Dashboard no carga:**
   - Verificar que el puerto 8050 esté libre
   - Revisar conexión a la API
   - Verificar CORS settings

3. **WebSocket no conecta:**
   - Verificar configuración de nginx
   - Revisar headers de proxy
   - Verificar firewall

4. **No hay datos de precios:**
   - Verificar conexión a Binance
   - Revisar configuración de pares
   - Verificar logs del WebSocket

### Comandos de Diagnóstico

```bash
# Verificar puertos
netstat -tulpn | grep :8000
netstat -tulpn | grep :8050

# Verificar servicios
sudo systemctl status arbitrage-api
sudo systemctl status nginx

# Verificar logs
tail -f output/api.log
sudo journalctl -u arbitrage-api -f

# Test de conectividad
curl http://localhost:8000/api/status
curl http://localhost:8050/
```

## 📞 Soporte

Para problemas o preguntas:

1. Revisar logs en `output/api.log`
2. Verificar configuración en `api/config.py`
3. Probar endpoints individuales
4. Verificar conectividad a Binance

## 📝 Licencia

Este proyecto es para uso educativo y de desarrollo. Usa bajo tu propia responsabilidad.

---

**¡Disfruta monitoreando oportunidades de arbitraje triangular en tiempo real! 🚀** 