import logging
import json
import time
import threading
import websocket
from typing import Dict, Set, Callable, Optional
from queue import Queue, Empty

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output/price_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PriceWebSocketManager:
    def __init__(self):
        """
        Inicializa el gestor de WebSocket para precios en tiempo real.
        
 
        """
        self.prices = {}
        self.price_update_event = threading.Event()
        self.ws = None
        self.ws_thread = None
        self.reconnect_delay = 5
        self.max_reconnect_attempts = 5
        self.reconnect_attempts = 0
        self.subscription_groups = []
        self.current_group_index = 0
        self.last_subscription_time = 0
        self.subscription_interval = 2.0  # Aumentado a 2 segundos
        self.refresh_interval = 300
        self.last_refresh_time = 0
        self.running = True
        self.callbacks = []
        self.symbols_queue = Queue()
        self.worker_thread = None
        self.lock = threading.Lock()  # Lock para operaciones críticas
        self.is_subscribing = False  # Flag para evitar suscripciones simultáneas
        
        # Iniciar el worker thread para procesar actualizaciones de símbolos
        self.worker_thread = threading.Thread(target=self._process_symbol_updates)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        # Iniciar WebSocket inmediatamente
        self.start_websocket()

    def _process_symbol_updates(self):
        """Procesa las actualizaciones de símbolos en segundo plano"""
        while self.running:
            try:
                # Obtener nuevos símbolos de la cola
                symbols = self.symbols_queue.get(timeout=1)
                if symbols:
                    self._update_subscriptions(symbols)
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error procesando actualizaciones de símbolos: {e}")

    def _update_subscriptions(self, symbols: Set[str]):
        """Actualiza las suscripciones con un nuevo conjunto de símbolos"""
        with self.lock:
            if self.is_subscribing:
                return
            
            try:
                self.is_subscribing = True
                # Preparar nuevos grupos de suscripción
                streams = [f"{symbol.lower()}@ticker" for symbol in symbols]
                logger.info(f"Preparando suscripciones para streams: {streams}")
                self.subscription_groups = [streams[i:i + 3] for i in range(0, len(streams), 3)]
                self.current_group_index = 0
                
                # Enviar nuevas suscripciones si el WebSocket está conectado
                if self.ws and self.ws.sock and self.ws.sock.connected:
                    self.send_subscription_group(self.ws)
                else:
                    logger.warning("WebSocket no está conectado, no se pueden enviar suscripciones")
            except Exception as e:
                logger.error(f"Error actualizando suscripciones: {e}")
            finally:
                self.is_subscribing = False

    def update_symbols(self, symbols: Set[str]):
        """
        Actualiza el conjunto de símbolos a monitorear.
        Esta función es thread-safe y puede ser llamada desde cualquier hilo.
        
        Args:
            symbols (Set[str]): Conjunto de símbolos a monitorear
        """
        self.symbols_queue.put(symbols)

    def add_price_callback(self, callback: Callable[[str, float], None]):
        """
        Agrega una función callback que será llamada cuando se actualice un precio.
        
        Args:
            callback (Callable[[str, float], None]): Función que recibe (símbolo, precio)
        """
        self.callbacks.append(callback)

    def on_message(self, ws, message):
        """Callback para mensajes del WebSocket"""
        try:
            data = json.loads(message)
            logger.debug(f"Mensaje recibido: {data}")  # Debug del mensaje completo
            
            # Manejar mensajes de ping/pong
            if isinstance(data, dict) and 'e' in data and data['e'] == 'pong':
                return
                
            # Manejar mensajes de suscripción
            if isinstance(data, dict) and 'result' in data:
                logger.info(f"Respuesta de suscripción: {data}")
                return
                
            # Manejar mensajes de ticker
            if 'stream' in data and 'data' in data:
                stream_data = data['data']
                symbol = stream_data['s']
                price = float(stream_data['c'])
                
                logger.debug(f"Precio actualizado para {symbol}: {price}")
                self.prices[symbol] = price
                self.price_update_event.set()
                
                # Notificar a todos los callbacks registrados
                for callback in self.callbacks:
                    try:
                        callback(symbol, price)
                    except Exception as e:
                        logger.error(f"Error en callback de precio: {e}")
            else:
                logger.warning(f"Mensaje no reconocido: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando mensaje JSON: {e}, Mensaje: {message}")
        except Exception as e:
            logger.error(f"Error procesando mensaje WebSocket: {e}")

    def on_error(self, ws, error):
        logger.error(f"Error en WebSocket: {error}")
        self.handle_reconnection()

    def on_close(self, ws, close_status_code, close_msg):
        logger.info(f"WebSocket cerrado - Status: {close_status_code}, Mensaje: {close_msg}")
        if close_status_code != 1000:
            self.handle_reconnection()

    def handle_reconnection(self):
        """Maneja la reconexión con backoff exponencial"""
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            delay = min(5 * (2 ** (self.reconnect_attempts - 1)), 80)
            logger.info(f"Intentando reconectar en {delay} segundos... Intento {self.reconnect_attempts} de {self.max_reconnect_attempts}")
            time.sleep(delay)
            self.start_websocket()
        else:
            logger.error("Se alcanzó el máximo número de intentos de reconexión")

    def send_subscription_group(self, ws):
        """Envía un grupo de suscripciones con rate limiting"""
        with self.lock:
            if self.is_subscribing:
                return

            try:
                self.is_subscribing = True
                current_time = time.time()
                
                # Solo refrescar si ha pasado el intervalo y no estamos en medio de una suscripción
                if current_time - self.last_refresh_time > self.refresh_interval:
                    logger.info("Refrescando suscripciones...")
                    self._update_subscriptions(set(self.prices.keys()))
                    self.last_refresh_time = current_time
                    return
                
                if current_time - self.last_subscription_time < self.subscription_interval:
                    time.sleep(self.subscription_interval)
                
                if self.current_group_index < len(self.subscription_groups):
                    group = self.subscription_groups[self.current_group_index]
                    subscribe_message = {
                        "method": "SUBSCRIBE",
                        "params": group,
                        "id": 1
                    }
                    logger.info(f"Enviando suscripción: {subscribe_message}")
                    ws.send(json.dumps(subscribe_message))
                    self.last_subscription_time = time.time()
                    self.current_group_index += 1
                    logger.info(f"Enviado grupo de suscripción {self.current_group_index}/{len(self.subscription_groups)}")
                else:
                    self.current_group_index = 0
            finally:
                self.is_subscribing = False

    def on_open(self, ws):
        """Callback cuando el WebSocket se abre"""
        logger.info("WebSocket conectado")
        self.reconnect_attempts = 0
        self.send_subscription_group(ws)

    def start_websocket(self):
        """Inicia la conexión WebSocket en un hilo separado"""
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            "wss://stream.binance.com:9443/ws",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        logger.info("WebSocket iniciado y thread creado")

    def get_price(self, symbol: str) -> Optional[float]:
        """
        Obtiene el precio actual de un símbolo.
        
        Args:
            symbol (str): Símbolo del par de trading
            
        Returns:
            Optional[float]: Precio actual o None si no está disponible
        """
        return self.prices.get(symbol)

    def get_all_prices(self) -> Dict[str, float]:
        """
        Obtiene todos los precios actuales.
        
        Returns:
            Dict[str, float]: Diccionario con todos los precios actuales
        """
        return self.prices.copy()

    def stop(self):
        """Detiene el WebSocket y el worker thread"""
        self.running = False
        if self.ws:
            self.ws.close()
        if self.worker_thread:
            self.worker_thread.join(timeout=1) 