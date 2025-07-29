#!/usr/bin/env python3
"""
Configuración para la API de streaming de arbitraje triangular

Este archivo contiene configuraciones para diferentes entornos:
- Desarrollo local
- Producción (VPS/Dedicated)
- Cloud hosting (Heroku, Railway, etc.)
"""

import os
from typing import Dict, Any

class APIConfig:
    """Configuración base de la API"""
    
    # Configuración general
    APP_NAME = "Arbitraje Triangular API"
    VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Configuración del servidor
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # Configuración de CORS
    CORS_ORIGINS = [
        "http://localhost:8050",  # Dashboard local
        "http://127.0.0.1:8050",
        "https://your-domain.com",  # Cambiar por tu dominio
        "*"  # Solo para desarrollo
    ]
    
    # Configuración de WebSocket
    WEBSOCKET_PING_INTERVAL = 20
    WEBSOCKET_PING_TIMEOUT = 10
    
    # Configuración de Binance
    BINANCE_ASSETS = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT',
        'SOLUSDT', 'MATICUSDT', 'LINKUSDT', 'UNIUSDT', 'AVAXUSDT'
    ]
    BINANCE_INTERVAL = '1m'
    
    # Configuración de arbitraje
    ARBITRAGE_MIN_PROFIT = 0.5  # 0.5%
    ARBITRAGE_MAX_OPPORTUNITIES = 50
    
    # Configuración de logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = "output/api.log"
    
    # Configuración de rate limiting
    RATE_LIMIT_REQUESTS = 100  # requests per minute
    RATE_LIMIT_WINDOW = 60  # seconds

class DevelopmentConfig(APIConfig):
    """Configuración para desarrollo local"""
    DEBUG = True
    HOST = "127.0.0.1"
    PORT = 8000
    
    # Logging detallado para desarrollo
    LOG_LEVEL = "DEBUG"
    
    # CORS permisivo para desarrollo
    CORS_ORIGINS = ["*"]

class ProductionConfig(APIConfig):
    """Configuración para producción (VPS/Dedicated)"""
    DEBUG = False
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 8000))
    
    # CORS más restrictivo
    CORS_ORIGINS = [
        "https://your-domain.com",
        "https://www.your-domain.com"
    ]
    
    # Logging de producción
    LOG_LEVEL = "WARNING"
    
    # Configuración de seguridad
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # Configuración de base de datos (si se usa)
    DATABASE_URL = os.getenv("DATABASE_URL")

class CloudConfig(APIConfig):
    """Configuración para cloud hosting (Heroku, Railway, etc.)"""
    DEBUG = False
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 8000))
    
    # CORS para cloud
    CORS_ORIGINS = [
        "https://your-app.herokuapp.com",
        "https://your-app.railway.app"
    ]
    
    # Configuración específica de cloud
    WORKERS = int(os.getenv("WEB_CONCURRENCY", 1))
    
    # Logging para cloud
    LOG_LEVEL = "INFO"

# Configuración según el entorno
def get_config() -> APIConfig:
    """Obtiene la configuración según el entorno"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "cloud":
        return CloudConfig()
    else:
        return DevelopmentConfig()

# Configuración de hosting recomendada
HOSTING_RECOMMENDATIONS = {
    "local_development": {
        "description": "Desarrollo local",
        "command": "python api/streaming_api.py",
        "requirements": "support/requirements.txt",
        "ports": {"api": 8000, "dashboard": 8050}
    },
    "vps_dedicated": {
        "description": "VPS o servidor dedicado",
        "recommended": ["DigitalOcean", "Linode", "Vultr", "AWS EC2"],
        "setup": [
            "Instalar Python 3.8+",
            "Configurar firewall (puertos 8000, 8050)",
            "Usar systemd para servicios",
            "Configurar nginx como proxy reverso",
            "Usar SSL/TLS con Let's Encrypt"
        ],
        "systemd_service": """
[Unit]
Description=Arbitraje Triangular API
After=network.target

[Service]
Type=simple
User=arbitrage
WorkingDirectory=/path/to/arbitbot
Environment=ENVIRONMENT=production
ExecStart=/usr/bin/python3 api/streaming_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
        """
    },
    "cloud_platforms": {
        "heroku": {
            "description": "Heroku",
            "files": {
                "Procfile": "web: uvicorn api.streaming_api:main --host 0.0.0.0 --port $PORT",
                "runtime.txt": "python-3.9.18"
            },
            "env_vars": ["ENVIRONMENT=cloud", "PORT=$PORT"]
        },
        "railway": {
            "description": "Railway",
            "command": "uvicorn api.streaming_api:main --host 0.0.0.0 --port $PORT",
            "env_vars": ["ENVIRONMENT=cloud"]
        },
        "render": {
            "description": "Render",
            "build_command": "pip install -r support/requirements.txt",
            "start_command": "uvicorn api.streaming_api:main --host 0.0.0.0 --port $PORT"
        }
    }
}

# Configuración de nginx (para VPS/Dedicated)
NGINX_CONFIG = """
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirigir a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # API
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
    
    # WebSocket
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
    
    # Dashboard
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
"""

# Configuración de Docker (opcional)
DOCKERFILE = """
FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias
COPY support/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Exponer puertos
EXPOSE 8000 8050

# Comando por defecto
CMD ["python", "start_arbitrage_system.py"]
"""

DOCKER_COMPOSE = """
version: '3.8'

services:
  arbitrage-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    volumes:
      - ./output:/app/output
    restart: unless-stopped

  arbitrage-dashboard:
    build: .
    ports:
      - "8050:8050"
    environment:
      - ENVIRONMENT=production
    depends_on:
      - arbitrage-api
    restart: unless-stopped
""" 