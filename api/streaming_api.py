#!/usr/bin/env python3
"""
API de streaming en tiempo real para el bot de arbitraje triangular

Esta API proporciona:
1. Stream de precios en tiempo real
2. Stream de oportunidades de arbitraje
3. Endpoints REST para datos históricos
4. WebSocket para actualizaciones en tiempo real
"""

import sys
import os
import asyncio
import json
import time
from typing import Dict, List, Optional
from datetime import datetime
import logging

# Agregar el directorio raíz del proyecto al path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

from classes.binance_kline_websocket import BinanceKlineWebSocket
from classes.arbitrage_bot import ArbitrageBot

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamingAPI:
    def __init__(self):
        self.app = FastAPI(
            title="Arbitraje Triangular API",
            description="API de streaming en tiempo real para arbitraje triangular",
            version="1.0.0"
        )
        
        # Configurar CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Estado de la aplicación
        self.websocket_manager = None
        self.arbitrage_bot = None
        self.connected_clients = []
        self.price_history = {}
        self.arbitrage_opportunities = []
        
        # Configurar rutas
        self.setup_routes()
        
        # Inicializar componentes
        self.initialize_components()
    
    def initialize_components(self):
        """Inicializa el WebSocket y el bot de arbitraje"""
        try:
            # Inicializar WebSocket con pares principales
            assets = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT']
            self.websocket_manager = BinanceKlineWebSocket(
                assets=assets,
                interval='1m'
            )
            
            # Agregar callback para procesar datos
            self.websocket_manager.add_callback(self.on_price_update)
            
            # Inicializar bot de arbitraje
            self.arbitrage_bot = ArbitrageBot()
            
            logger.info("Componentes inicializados correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando componentes: {e}")
    
    def on_price_update(self, df):
        """Callback cuando se actualiza un precio"""
        try:
            symbol = df['symbol'].iloc[0]
            price = df['close'].iloc[0]
            timestamp = df['timestamp'].iloc[0]
            
            # Actualizar historial de precios
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            price_data = {
                'symbol': symbol,
                'price': price,
                'timestamp': timestamp,
                'datetime': datetime.fromtimestamp(timestamp/1000).isoformat()
            }
            
            self.price_history[symbol].append(price_data)
            
            # Mantener solo los últimos 100 registros
            if len(self.price_history[symbol]) > 100:
                self.price_history[symbol] = self.price_history[symbol][-100:]
            
            # Buscar oportunidades de arbitraje
            self.check_arbitrage_opportunities()
            
            # Enviar actualización a clientes conectados
            self.broadcast_price_update(price_data)
            
        except Exception as e:
            logger.error(f"Error procesando actualización de precio: {e}")
    
    def check_arbitrage_opportunities(self):
        """Verifica oportunidades de arbitraje"""
        try:
            # Aquí implementarías la lógica de arbitraje triangular
            # Por ahora, simulamos algunas oportunidades
            if len(self.price_history) >= 3:
                # Simular oportunidad de arbitraje
                opportunity = {
                    'id': len(self.arbitrage_opportunities) + 1,
                    'route': 'BTCUSDT -> ETHUSDT -> BNBUSDT',
                    'profit_percentage': 0.5 + (time.time() % 2),  # Simulado
                    'timestamp': datetime.now().isoformat(),
                    'prices': {
                        'BTCUSDT': self.price_history.get('BTCUSDT', [{}])[-1].get('price', 0),
                        'ETHUSDT': self.price_history.get('ETHUSDT', [{}])[-1].get('price', 0),
                        'BNBUSDT': self.price_history.get('BNBUSDT', [{}])[-1].get('price', 0)
                    }
                }
                
                self.arbitrage_opportunities.append(opportunity)
                
                # Mantener solo las últimas 50 oportunidades
                if len(self.arbitrage_opportunities) > 50:
                    self.arbitrage_opportunities = self.arbitrage_opportunities[-50:]
                
                # Enviar a clientes conectados
                self.broadcast_arbitrage_opportunity(opportunity)
                
        except Exception as e:
            logger.error(f"Error verificando arbitraje: {e}")
    
    def broadcast_price_update(self, price_data):
        """Envía actualización de precio a todos los clientes conectados"""
        message = {
            'type': 'price_update',
            'data': price_data
        }
        self.broadcast_message(message)
    
    def broadcast_arbitrage_opportunity(self, opportunity):
        """Envía oportunidad de arbitraje a todos los clientes conectados"""
        message = {
            'type': 'arbitrage_opportunity',
            'data': opportunity
        }
        self.broadcast_message(message)
    
    def broadcast_message(self, message):
        """Envía mensaje a todos los clientes WebSocket conectados"""
        disconnected_clients = []
        
        for client in self.connected_clients:
            try:
                asyncio.create_task(client.send_text(json.dumps(message)))
            except Exception as e:
                logger.error(f"Error enviando mensaje a cliente: {e}")
                disconnected_clients.append(client)
        
        # Remover clientes desconectados
        for client in disconnected_clients:
            self.connected_clients.remove(client)
    
    def setup_routes(self):
        """Configura las rutas de la API"""
        
        @self.app.get("/")
        async def root():
            return {
                "message": "Arbitraje Triangular API",
                "version": "1.0.0",
                "endpoints": {
                    "websocket": "/ws",
                    "prices": "/api/prices",
                    "opportunities": "/api/opportunities",
                    "status": "/api/status"
                }
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.connected_clients.append(websocket)
            
            try:
                # Enviar datos iniciales
                initial_data = {
                    'type': 'connection_established',
                    'message': 'Conectado al stream de arbitraje triangular',
                    'timestamp': datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(initial_data))
                
                # Mantener conexión activa
                while True:
                    try:
                        # Esperar mensaje del cliente (ping/pong)
                        data = await websocket.receive_text()
                        message = json.loads(data)
                        
                        if message.get('type') == 'ping':
                            await websocket.send_text(json.dumps({
                                'type': 'pong',
                                'timestamp': datetime.now().isoformat()
                            }))
                            
                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        logger.error(f"Error en WebSocket: {e}")
                        break
                        
            except Exception as e:
                logger.error(f"Error en conexión WebSocket: {e}")
            finally:
                if websocket in self.connected_clients:
                    self.connected_clients.remove(websocket)
        
        @self.app.get("/api/prices")
        async def get_prices():
            """Obtiene todos los precios actuales"""
            current_prices = {}
            for symbol, history in self.price_history.items():
                if history:
                    current_prices[symbol] = history[-1]
            
            return {
                'prices': current_prices,
                'total_symbols': len(current_prices),
                'timestamp': datetime.now().isoformat()
            }
        
        @self.app.get("/api/prices/{symbol}")
        async def get_price_history(symbol: str, limit: int = 100):
            """Obtiene historial de precios para un símbolo específico"""
            if symbol not in self.price_history:
                raise HTTPException(status_code=404, detail="Símbolo no encontrado")
            
            history = self.price_history[symbol][-limit:]
            return {
                'symbol': symbol,
                'history': history,
                'count': len(history),
                'timestamp': datetime.now().isoformat()
            }
        
        @self.app.get("/api/opportunities")
        async def get_opportunities():
            """Obtiene oportunidades de arbitraje"""
            return {
                'opportunities': self.arbitrage_opportunities,
                'count': len(self.arbitrage_opportunities),
                'timestamp': datetime.now().isoformat()
            }
        
        @self.app.get("/api/status")
        async def get_status():
            """Obtiene el estado del sistema"""
            return {
                'websocket_running': self.websocket_manager.is_running() if self.websocket_manager else False,
                'connected_clients': len(self.connected_clients),
                'monitored_symbols': len(self.price_history),
                'opportunities_found': len(self.arbitrage_opportunities),
                'timestamp': datetime.now().isoformat()
            }
        
        @self.app.get("/api/stream/prices")
        async def stream_prices():
            """Stream de precios en tiempo real (Server-Sent Events)"""
            async def generate():
                while True:
                    try:
                        current_prices = {}
                        for symbol, history in self.price_history.items():
                            if history:
                                current_prices[symbol] = history[-1]
                        
                        data = {
                            'prices': current_prices,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        yield f"data: {json.dumps(data)}\n\n"
                        await asyncio.sleep(1)  # Actualizar cada segundo
                        
                    except Exception as e:
                        logger.error(f"Error en stream de precios: {e}")
                        break
            
            return StreamingResponse(
                generate(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*"
                }
            )

def main():
    """Función principal para ejecutar la API"""
    api = StreamingAPI()
    
    # Iniciar WebSocket si no está corriendo
    if api.websocket_manager and not api.websocket_manager.is_running():
        api.websocket_manager.start()
        logger.info("WebSocket iniciado")
    
    # Configurar uvicorn
    uvicorn.run(
        api.app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main() 