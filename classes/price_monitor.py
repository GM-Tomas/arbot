import logging
import threading
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime

from .binance_kline_websocket import BinanceKlineWebSocket

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceMonitor:
    """
    Clase Singleton para monitorear precios de criptomonedas.
    Actúa como la única fuente de verdad para los datos de precios en la aplicación.
    """
    
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PriceMonitor, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Evitar reinicialización si ya existe
        if getattr(self, '_initialized', False):
            return
            
        self._prices: Dict[str, Dict] = {}
        self._pairs: List[str] = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT']
        self._websocket: Optional[BinanceKlineWebSocket] = None
        self._data_lock = threading.Lock()
        
        self._start_websocket()
        self._initialized = True
        logger.info("PriceMonitor Singleton inicializado")

    @classmethod
    def get_instance(cls):
        """Método estático para obtener la instancia única."""
        return cls()

    def _start_websocket(self):
        """Inicia (o reinicia) la conexión WebSocket."""
        if self._websocket:
            self._websocket.stop()
            
        logger.info(f"Iniciando monitor para pares: {self._pairs}")
        self._websocket = BinanceKlineWebSocket(assets=self._pairs, interval="1m")
        self._websocket.add_callback(self._on_price_update)
        self._websocket.start()

    def update_pairs(self, new_pairs: List[str]):
        """
        Actualiza la lista de pares monitoreados y reinicia el WebSocket.
        
        Args:
            new_pairs: Lista de strings con los símbolos (ej: ['BTCUSDT', 'ETHUSDT'])
        """
        # Limpiar espacios y convertir a mayúsculas
        clean_pairs = [p.strip().upper() for p in new_pairs if p.strip()]
        
        # Validar que no esté vacía
        if not clean_pairs:
            logger.warning("Intento de actualizar con lista vacía")
            return

        with self._data_lock:
            self._pairs = clean_pairs
            # Reiniciar diccionario de precios para limpiar datos viejos si se desea
            # O mantenerlos. Aquí optamos por mantenerlos pero marcar que se actualizaron los pares.
            # self._prices.clear() 
        
        self._start_websocket()

    def _on_price_update(self, df: pd.DataFrame):
        """Callback privado para procesar actualizaciones del WebSocket."""
        try:
            if not df.empty:
                symbol = df['symbol'].iloc[0]
                price = df['price'].iloc[0]
                volume = df['volume'].iloc[0]
                timestamp = df['timestamp'].iloc[0]
                
                with self._data_lock:
                    self._prices[symbol] = {
                        'price': price,
                        'volume': volume,
                        'timestamp': timestamp,
                        'last_update_str': timestamp.strftime('%H:%M:%S')
                    }
        except Exception as e:
            logger.error(f"Error procesando precio en Monitor: {e}")

    def get_prices(self) -> Dict[str, Dict]:
        """Devuelve una copia segura de los precios actuales."""
        with self._data_lock:
            return self._prices.copy()

    def get_monitored_pairs(self) -> List[str]:
        """Devuelve la lista actual de pares monitoreados."""
        return self._pairs.copy()
