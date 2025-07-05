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

1. Configura tus credenciales en el archivo `input/config.json`
2. Ejecuta el bot:
```bash
python Main.py
```

## Estructura del Proyecto

```
Arbitbot/
├── classes/                 # Clases principales del bot
│   ├── arbitrage_bot.py    # Clase principal del bot
│   ├── price_websocket_manager.py  # Gestor de WebSocket para precios
│   └── trade_logger.py     # Logger de trades
├── input/                  # Archivos de entrada
│   └── config.json        # Configuración del bot
├── output/                 # Archivos de salida
│   ├── arbitrage_bot.log  # Log del bot
│   ├── price_manager.log  # Log del gestor de precios
│   └── trades.csv         # Registro de trades
├── support/               # Archivos de soporte
│   └── requirements.txt   # Dependencias de Python
├── testing/               # Tests del bot
│   └── test_arbitrage_bot.py
└── Main.py               # Punto de entrada principal
```

## Configuración

El archivo `input/config.json` contiene toda la configuración del bot:

- **binance**: Credenciales de la API de Binance
- **settings**: Parámetros de trading y configuración general
- **risk_management**: Configuración de gestión de riesgos
- **monitoring**: Configuración de monitoreo y logging

## Advertencia

El trading de criptomonedas implica riesgos. Este bot es solo para fines educativos. Úsalo bajo tu propia responsabilidad.
