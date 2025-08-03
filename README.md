# Crypto Arbitrage Bot

Este bot de arbitraje de criptomonedas utiliza la API de Binance para encontrar oportunidades de arbitraje entre diferentes pares de trading. El bot implementa el algoritmo de Dijkstra para encontrar el camino más corto en el grafo de nodos de pares de criptomonedas.

## Características

- Conexión con la API de Binance
- Análisis de datos con pandas
- Implementación del algoritmo de Dijkstra para encontrar oportunidades de arbitraje
- Monitoreo en tiempo real de precios
- Cálculo de ganancias potenciales

## Requisitos

- Python 3.8+
- Cuenta en Binance con API key y secret key
- Conexión a internet

## Instalación

1. Clonar el repositorio
2. Instalar las dependencias:
```bash
pip install -r support/requirements.txt
```
3. Configurar el archivo de configuración:
   - Edita `input/config.json` con tus credenciales de Binance
   - Ajusta los parámetros de trading según tus necesidades

## Uso

### Bot de Arbitraje
1. Configura tus credenciales en el archivo `input/config.json`
2. Ejecuta el bot:
```bash
python Main.py
```

### Dashboard Web
Para ejecutar el dashboard web con navegación entre páginas:
```bash
python run_dashboard.py
```

El dashboard estará disponible en: http://localhost:8050

**Páginas disponibles:**
- **Dashboard de Precios**: Muestra precios y volumen en tiempo real
- **Oportunidades de Arbitraje**: Información sobre análisis de arbitraje

## Estructura del Proyecto

```
Arbitbot/
├── classes/                 # Clases principales del bot
│   ├── arbitrage_bot.py    # Clase principal del bot
│   ├── binance_kline_websocket.py  # WebSocket para datos de Binance
│   └── README_BinanceKlineWebSocket.md
├── input/                  # Archivos de entrada
│   └── config.json        # Configuración del bot
├── output/                 # Archivos de salida
│   ├── arbitrage_bot.log  # Log del bot
│   ├── price_manager.log  # Log del gestor de precios
│   └── trades.csv         # Registro de trades
├── web/                    # Dashboard web
│   ├── app.py             # Aplicación principal
│   ├── layout.py          # Layout con navegación
│   ├── views/             # Vistas de las páginas
│   │   ├── dashboard_view.py    # Dashboard de precios
│   │   └── arbitrage_view.py    # Página de arbitraje
│   └── README.md          # Documentación del dashboard
├── run_dashboard.py       # Script para ejecutar el dashboard
├── requirements.txt        # Dependencias de Python
└── Main.py               # Punto de entrada principal del bot
```

## Configuración

El archivo `input/config.json` contiene toda la configuración del bot:

- **binance**: Credenciales de la API de Binance
- **settings**: Parámetros de trading y configuración general
- **risk_management**: Configuración de gestión de riesgos
- **monitoring**: Configuración de monitoreo y logging

## Advertencia

El trading de criptomonedas implica riesgos. Este bot es solo para fines educativos. Úsalo bajo tu propia responsabilidad.
