import json
import websocket
import pandas as pd
import threading
import time
from typing import List, Callable
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinanceTickerWebSocket:
    """
    Clase para manejar WebSocket de Binance para el stream de todos los tickers (!ticker@arr).
    """
    
    def __init__(self):
        self.ws = None
        self.ws_thread = None
        self.running = False
        self.callbacks = []
        self.lock = threading.Lock()
        
        # URL del WebSocket para todos los tickers
        # Usamos fstream (Futuros) o stream (Spot) dependiendo de la necesidad.
        # El usuario mencionó "pares operados en Binance", asumiremos Spot por defecto.
        self.socket_url = "wss://stream.binance.com:9443/ws/!ticker@arr"
        
        logger.info(f"WebSocket Ticker inicializado: {self.socket_url}")
    
    def add_callback(self, callback: Callable[[List[dict]], None]):
        """Agrega una función callback que recibirá la lista de tickers."""
        with self.lock:
            self.callbacks.append(callback)
    
    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            # data es una lista de objetos ticker
            if isinstance(data, list) and len(data) > 0:
                with self.lock:
                    for callback in self.callbacks:
                        try:
                            callback(data)
                        except Exception as e:
                            logger.error(f"Error en callback de ticker: {e}")
                            
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON: {e}")
        except Exception as e:
            logger.error(f"Error procesando mensaje ticker: {e}")
    
    def _on_error(self, ws, error):
        logger.error(f"Error en WebSocket Ticker: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        logger.info(f"WebSocket Ticker cerrado")
    
    def _on_open(self, ws):
        logger.info("WebSocket Ticker conectado exitosamente")
    
    def _run_websocket(self):
        try:
            self.ws = websocket.WebSocketApp(
                self.socket_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            self.ws.run_forever()
        except Exception as e:
            logger.error(f"Error ejecutando WebSocket Ticker: {e}")
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self.ws_thread.start()
        logger.info("WebSocket Ticker iniciado")
    
    def stop(self):
        if not self.running:
            return
        
        self.running = False
        if self.ws:
            self.ws.close()
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=5)
        logger.info("WebSocket Ticker detenido")
