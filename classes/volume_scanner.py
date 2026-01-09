import json
import os
import time
import logging
import threading
from typing import List, Dict

from .binance_ticker_websocket import BinanceTickerWebSocket

logger = logging.getLogger(__name__)

class VolumeScanner:
    """
    Clase para escanear pares de Binance y ordenarlos por volumen.
    """
    
    def __init__(self, output_file: str = "config/top_pairs.json"):
        self.output_file = output_file
        self.ws = BinanceTickerWebSocket()
        self._scan_complete = threading.Event()
        self._result_pairs = []
        
    def _save_pairs(self, pairs: List[str]):
        """Guarda la lista de pares en el archivo JSON."""
        try:
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
            
            with open(self.output_file, 'w') as f:
                json.dump(pairs, f, indent=4)
            logger.info(f"Guardados {len(pairs)} pares en {self.output_file}")
            
        except Exception as e:
            logger.error(f"Error guardando pares: {e}")

    def _process_tickers(self, tickers: List[Dict]):
        """
        Procesa la lista de tickers recibida del WebSocket.
        Filtra por USDT y ordena por volumen.
        """
        try:
            usdt_pairs = []
            
            for t in tickers:
                symbol = t['s']
                # Filtrar solo pares USDT
                if symbol.endswith('USDT'):
                    try:
                        quote_volume = float(t['q']) # q = Quote Volume
                        usdt_pairs.append({
                            'symbol': symbol,
                            'volume': quote_volume
                        })
                    except ValueError:
                        continue
            
            # Si no encontramos suficientes pares, seguimos esperando
            if len(usdt_pairs) < 10:
                return

            # Ordenar por volumen descendente
            usdt_pairs.sort(key=lambda x: x['volume'], reverse=True)
            
            # Extraer solo los símbolos
            sorted_symbols = [p['symbol'] for p in usdt_pairs]
            
            # Guardar resultado
            self._result_pairs = sorted_symbols
            self._save_pairs(sorted_symbols)
            
            # Marcar como completado
            self._scan_complete.set()
            
        except Exception as e:
            logger.error(f"Error procesando tickers: {e}")

    def scan_and_save(self, timeout: int = 30) -> List[str]:
        """
        Inicia el escaneo, espera a recibir datos, guarda y retorna.
        """
        logger.info("Iniciando escaneo de volumen...")
        
        self.ws.add_callback(self._process_tickers)
        self.ws.start()
        
        # Esperar a que se complete el escaneo
        completed = self._scan_complete.wait(timeout=timeout)
        
        self.ws.stop()
        
        if completed:
            logger.info("Escaneo completado exitosamente.")
            return self._result_pairs
        else:
            logger.warning("Escaneo agotó el tiempo de espera.")
            return []
