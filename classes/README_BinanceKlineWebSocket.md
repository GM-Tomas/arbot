# BinanceKlineWebSocket

Esta clase permite monitorear en tiempo real los datos de velas (kline) de Binance a través de WebSocket, operando en un hilo separado para no interrumpir el hilo principal de ejecución.

## Características

- ✅ **Threading**: Opera en un hilo separado
- ✅ **Callbacks**: Sistema de callbacks para procesar datos
- ✅ **Múltiples assets**: Monitorea varios pares simultáneamente
- ✅ **Diferentes intervalos**: Soporta 1m, 5m, 15m, 1h, 4h, 1d
- ✅ **Manejo de errores**: Reconexión automática y logging
- ✅ **DataFrame**: Devuelve datos en formato pandas DataFrame

## Instalación

```bash
pip install -r support/requirements.txt
```

## Uso Básico

```python
from classes.binance_kline_websocket import BinanceKlineWebSocket
import pandas as pd

# 1. Crear instancia
websocket = BinanceKlineWebSocket(
    assets=['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
    interval='1m'
)

# 2. Definir callback para procesar datos
def my_callback(df: pd.DataFrame):
    print(f"Nuevo dato: {df['symbol'].iloc[0]} - ${df['close'].iloc[0]}")

# 3. Agregar callback
websocket.add_callback(my_callback)

# 4. Iniciar WebSocket
websocket.start()

# 5. El hilo principal puede hacer otras cosas
import time
time.sleep(60)  # Esperar 1 minuto

# 6. Detener WebSocket
websocket.stop()
```

## Estructura de Datos

Cada callback recibe un DataFrame con la siguiente estructura:

| Columna | Descripción |
|---------|-------------|
| `symbol` | Símbolo del par (ej: 'BTCUSDT') |
| `price` | Precio de cierre |
| `timestamp` | Timestamp de la vela |
| `open` | Precio de apertura |
| `high` | Precio más alto |
| `low` | Precio más bajo |
| `volume` | Volumen |
| `close` | Precio de cierre |

## Métodos Principales

### Constructor
```python
BinanceKlineWebSocket(assets: List[str], interval: str = "1m")
```

**Parámetros:**
- `assets`: Lista de pares de trading (ej: ['BTCUSDT', 'ETHUSDT'])
- `interval`: Intervalo de las velas ('1m', '5m', '15m', '1h', '4h', '1d')

### Métodos Públicos

#### `add_callback(callback: Callable[[pd.DataFrame], None])`
Agrega una función callback que será llamada cuando se reciba un mensaje.

#### `start()`
Inicia el WebSocket en un hilo separado.

#### `stop()`
Detiene el WebSocket y el hilo asociado.

#### `is_running() -> bool`
Verifica si el WebSocket está ejecutándose.

#### `get_assets() -> List[str]`
Obtiene la lista de assets monitoreados.

## Ejemplo Completo

```python
import sys
import os
import time
import pandas as pd

# Agregar el directorio classes al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'classes'))

from binance_kline_websocket import BinanceKlineWebSocket

def process_data(df: pd.DataFrame):
    """Procesa los datos recibidos del WebSocket"""
    symbol = df['symbol'].iloc[0]
    price = df['close'].iloc[0]
    timestamp = df['timestamp'].iloc[0]
    
    print(f"[{timestamp}] {symbol}: ${price}")

def main():
    # Crear WebSocket
    websocket = BinanceKlineWebSocket(
        assets=['BTCUSDT', 'ETHUSDT'],
        interval='1m'
    )
    
    # Agregar callback
    websocket.add_callback(process_data)
    
    # Iniciar
    websocket.start()
    
    try:
        # Mantener ejecutándose
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Deteniendo...")
        websocket.stop()

if __name__ == "__main__":
    main()
```

## Ejecutar el Ejemplo

```bash
cd testing
python example_binance_kline_websocket.py
```

## Ventajas del Diseño

1. **No bloqueante**: El WebSocket opera en un hilo separado
2. **Flexible**: Sistema de callbacks permite múltiples procesadores
3. **Robusto**: Manejo de errores y reconexión automática
4. **Eficiente**: Usa el stream combinado de Binance
5. **Fácil de usar**: API simple y clara

## Notas Importantes

- Los datos se reciben en tiempo real cuando se completa cada vela
- El intervalo '1m' significa que recibirás datos cada minuto
- Los callbacks se ejecutan en el hilo del WebSocket
- Usa `daemon=True` para que el hilo se detenga automáticamente con el programa principal 