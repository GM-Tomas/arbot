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

class BinanceKlineWebSocket:
    """
    Clase para manejar WebSocket de Binance para streams de kline (velas) en tiempo real.
    Opera en un hilo separado para no interrumpir el hilo principal.
    """
    
    def __init__(self, assets: List[str], interval: str = "1m"):
        """
        Inicializa el WebSocket de Binance para monitorear klines.
        
        Args:
            assets (List[str]): Lista de pares de trading (ej: ['BTCUSDT', 'ETHUSDT'])
            interval (str): Intervalo de las velas (ej: '1m', '5m', '1h', '1d')
        """
        self.assets = [asset.upper() for asset in assets]
        self.interval = interval
        self.ws = None
        self.ws_thread = None
        self.running = False
        self.callbacks = []
        self.lock = threading.Lock()
        
        # Construir el stream string
        self.stream_string = self._build_stream_string()
        
        # URL del WebSocket
        self.socket_url = f"wss://stream.binance.com:9443/stream?streams={self.stream_string}"
        
        logger.info(f"WebSocket inicializado para assets: {self.assets}")
        logger.info(f"URL del stream: {self.socket_url}")
    
    def _build_stream_string(self) -> str:
        """
        Construye el string de streams para la URL del WebSocket.
        
        Returns:
            str: String de streams formateado
        """
        streams = [f"{asset.lower()}@kline_{self.interval}" for asset in self.assets]
        return '/'.join(streams)
    
    def add_callback(self, callback: Callable[[pd.DataFrame], None]):
        """
        Agrega una función callback que será llamada cuando se reciba un mensaje.
        
        Args:
            callback (Callable[[pd.DataFrame], None]): Función que recibe un DataFrame con los datos
        """
        with self.lock:
            self.callbacks.append(callback)
    
    def _manipulate_data(self, source: dict) -> pd.DataFrame:
        """
        Manipula los datos recibidos del WebSocket y los convierte en DataFrame.
        
        Args:
            source (dict): Datos recibidos del WebSocket
            
        Returns:
            pd.DataFrame: DataFrame con los datos procesados
        """
        try:
            # Extraer datos del mensaje
            kline_data = source['data']['k']
            price = float(kline_data['c'])  # Precio de cierre
            pair = source['data']['s']  # Símbolo del par
            timestamp = pd.to_datetime(source['data']['E'], unit='ms')  # Timestamp
            
            # Crear DataFrame
            data = {
                'symbol': [pair],
                'price': [price],
                'timestamp': [timestamp],
                'open': [float(kline_data['o'])],
                'high': [float(kline_data['h'])],
                'low': [float(kline_data['l'])],
                'volume': [float(kline_data['v'])],
                'close': [float(kline_data['c'])]
            }
            
            df = pd.DataFrame(data)
            return df
            
        except Exception as e:
            logger.error(f"Error procesando datos: {e}")
            return pd.DataFrame()
    
    def _on_message(self, ws, message):
        """
        Callback para mensajes del WebSocket.
        
        Args:
            ws: WebSocket object
            message (str): Mensaje recibido
        """
        try:
            # Parsear el mensaje JSON
            data = json.loads(message)
            
            # Procesar los datos
            df = self._manipulate_data(data)
            
            if not df.empty:
                # Notificar a todos los callbacks registrados
                with self.lock:
                    for callback in self.callbacks:
                        try:
                            callback(df)
                        except Exception as e:
                            logger.error(f"Error en callback: {e}")
                            
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON: {e}")
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
    
    def _on_error(self, ws, error):
        """
        Callback para errores del WebSocket.
        
        Args:
            ws: WebSocket object
            error: Error ocurrido
        """
        logger.error(f"Error en WebSocket: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """
        Callback cuando el WebSocket se cierra.
        
        Args:
            ws: WebSocket object
            close_status_code: Código de cierre
            close_msg: Mensaje de cierre
        """
        logger.info(f"WebSocket cerrado - Status: {close_status_code}, Mensaje: {close_msg}")
    
    def _on_open(self, ws):
        """
        Callback cuando el WebSocket se abre.
        
        Args:
            ws: WebSocket object
        """
        logger.info("WebSocket conectado exitosamente")
    
    def _run_websocket(self):
        """
        Ejecuta el WebSocket en el hilo separado.
        """
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
            logger.error(f"Error ejecutando WebSocket: {e}")
    
    def start(self):
        """
        Inicia el WebSocket en un hilo separado.
        """
        if self.running:
            logger.warning("WebSocket ya está ejecutándose")
            return
        
        self.running = True
        self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self.ws_thread.start()
        
        logger.info("WebSocket iniciado en hilo separado")
    
    def stop(self):
        """
        Detiene el WebSocket.
        """
        if not self.running:
            logger.warning("WebSocket no está ejecutándose")
            return
        
        self.running = False
        
        if self.ws:
            self.ws.close()
        
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=5)
        
        logger.info("WebSocket detenido")
    
    def is_running(self) -> bool:
        """
        Verifica si el WebSocket está ejecutándose.
        
        Returns:
            bool: True si está ejecutándose, False en caso contrario
        """
        return self.running and self.ws_thread and self.ws_thread.is_alive()
    
    def get_assets(self) -> List[str]:
        """
        Obtiene la lista de assets monitoreados.
        
        Returns:
            List[str]: Lista de assets
        """
        return self.assets.copy() 