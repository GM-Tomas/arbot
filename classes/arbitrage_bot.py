import logging
from typing import Dict, List, Optional
import asyncio
import pandas as pd
from datetime import datetime
import threading
import requests

from .binance_kline_websocket import BinanceKlineWebSocket

logger = logging.getLogger(__name__)

class ArbitrageBot:
    def __init__(self):
        # Configuración hardcodeada
        self.base_currency = 'USDT'
        self.trading_fee = 0.1  # 0.1%
        self.slippage = 0.05    # 0.05%
        self.update_interval = 5  # segundos
        self.min_profit_threshold = 0.5  # 0.5%
        self.websocket_interval = '1m'
        self.top_pairs_count = 20  # Número de pares con más volumen a monitorear
        
        # Estado del bot
        self.triangular_pairs = []
        self.prices = {}  # Almacenamiento directo de precios
        self.volumes = {}  # Almacenamiento directo de volúmenes
        self.timestamps = {}  # Almacenamiento directo de timestamps
        self.websocket = None
        self.running = False
        self.opportunities_history = []
        self.lock = threading.Lock()

    def get_top_volume_pairs(self) -> List[str]:
        """Obtiene los pares USDT con mayor volumen de Binance"""
        try:
            # Obtener datos de 24h de Binance
            url = "https://api.binance.com/api/v3/ticker/24hr"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Filtrar solo pares USDT y ordenar por volumen
            usdt_pairs = []
            for ticker in data:
                symbol = ticker['symbol']
                if symbol.endswith('USDT'):
                    volume = float(ticker['volume'])
                    quote_volume = float(ticker['quoteVolume'])
                    usdt_pairs.append({
                        'symbol': symbol,
                        'volume': volume,
                        'quote_volume': quote_volume
                    })
            
            # Ordenar por volumen en USDT (quoteVolume) y tomar los top
            usdt_pairs.sort(key=lambda x: x['quote_volume'], reverse=True)
            top_pairs = [pair['symbol'] for pair in usdt_pairs[:self.top_pairs_count]]
            
            logger.info(f"Obtenidos {len(top_pairs)} pares con mayor volumen: {top_pairs}")
            return top_pairs
            
        except Exception as e:
            logger.error(f"Error obteniendo pares con mayor volumen: {e}")
            # Fallback a pares principales
            fallback_pairs = [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 
                'DOTUSDT', 'AVAXUSDT', 'MATICUSDT', 'LINKUSDT', 'UNIUSDT',
                'LTCUSDT', 'BCHUSDT', 'XRPUSDT', 'DOGEUSDT', 'SHIBUSDT',
                'TRXUSDT', 'EOSUSDT', 'ATOMUSDT', 'NEARUSDT', 'FTMUSDT'
            ]
            logger.info(f"Usando pares de fallback: {fallback_pairs}")
            return fallback_pairs

    def on_price_update(self, df: pd.DataFrame):
        """Callback para actualizaciones de precio"""
        try:
            if not df.empty:
                symbol = df['symbol'].iloc[0]
                price = df['price'].iloc[0]
                volume = df['volume'].iloc[0]
                timestamp = df['timestamp'].iloc[0]
                
                with self.lock:
                    self.prices[symbol] = price
                    self.volumes[symbol] = volume
                    self.timestamps[symbol] = timestamp
                
        except Exception as e:
            logger.error(f"Error en callback: {e}")

    async def initialize(self):
        """Inicializa el bot"""
        try:
            # Obtener pares con mayor volumen
            top_pairs = self.get_top_volume_pairs()
            self.setup_triangular_pairs(top_pairs)
            await self.setup_websocket()
            logger.info(f"Bot inicializado con {len(self.triangular_pairs)} pares triangulares")
        except Exception as e:
            logger.error(f"Error en inicialización: {e}")
            raise

    def setup_triangular_pairs(self, top_pairs: List[str]):
        """Configura pares triangulares basados en los pares con mayor volumen"""
        # Extraer símbolos base (sin USDT)
        base_symbols = [pair.replace('USDT', '') for pair in top_pairs]
        
        self.triangular_pairs = []
        for i, coin1 in enumerate(base_symbols):
            for j, coin2 in enumerate(base_symbols):
                if i != j:  # Evitar pares iguales
                    pair1 = f"{coin1}{self.base_currency}"
                    pair2 = f"{coin1}{coin2}"
                    pair3 = f"{coin2}{self.base_currency}"
                    self.triangular_pairs.append((pair1, pair2, pair3))

    async def setup_websocket(self):
        """Configura WebSocket"""
        try:
            all_pairs = set()
            for base_pair, inter_pair, final_pair in self.triangular_pairs:
                all_pairs.update([base_pair, inter_pair, final_pair])
            
            pairs_list = list(all_pairs)
            
            if pairs_list:
                self.websocket = BinanceKlineWebSocket(
                    assets=pairs_list,
                    interval=self.websocket_interval
                )
                self.websocket.add_callback(self.on_price_update)
                self.websocket.start()
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Error configurando WebSocket: {e}")

    def get_price(self, symbol: str) -> Optional[float]:
        """Obtiene el precio de un símbolo"""
        with self.lock:
            if symbol in self.prices and symbol in self.timestamps:
                # Verificar que el precio no sea muy antiguo (máximo 60 segundos)
                age = (datetime.now() - self.timestamps[symbol]).total_seconds()
                if age <= 60:
                    return self.prices[symbol]
            return None

    def has_recent_prices(self) -> bool:
        """Verifica si hay precios recientes disponibles"""
        with self.lock:
            current_time = datetime.now()
            for symbol in self.prices:
                if symbol in self.timestamps:
                    age = (current_time - self.timestamps[symbol]).total_seconds()
                    if age <= 60:
                        return True
            return False

    def get_all_prices(self) -> Dict[str, float]:
        """Obtiene todos los precios válidos"""
        with self.lock:
            current_time = datetime.now()
            valid_prices = {}
            
            for symbol, price in self.prices.items():
                if symbol in self.timestamps:
                    age = (current_time - self.timestamps[symbol]).total_seconds()
                    if age <= 60:
                        valid_prices[symbol] = price
            
            return valid_prices

    async def scan_opportunities(self, initial_amount: float = 100.0) -> List[Dict]:
        """Escanea oportunidades de arbitraje"""
        opportunities = []
        
        if not self.has_recent_prices():
            return opportunities
        
        print(f"\n🔍 Escaneando {len(self.triangular_pairs)} pares triangulares...")
        
        for base_pair, inter_pair, final_pair in self.triangular_pairs:
            try:
                base_price = self.get_price(base_pair)
                inter_price = self.get_price(inter_pair)
                final_price = self.get_price(final_pair)
                
                if not all(price is not None for price in [base_price, inter_price, final_price]):
                    continue
                
                # Calcular arbitraje con slippage
                amount = initial_amount
                
                # Primer trade (buy) - aplicar slippage
                buy_price = base_price * (1 + self.slippage/100)
                amount = (amount * (1 - self.trading_fee/100)) / buy_price
                
                # Segundo trade (sell) - aplicar slippage
                sell_price = inter_price * (1 - self.slippage/100)
                amount = (amount * (1 - self.trading_fee/100)) * sell_price
                
                # Tercer trade (sell) - aplicar slippage
                final_sell_price = final_price * (1 - self.slippage/100)
                amount = (amount * (1 - self.trading_fee/100)) * final_sell_price
                
                profit_percentage = ((amount - initial_amount) / initial_amount) * 100
                
                if profit_percentage > self.min_profit_threshold:
                    opportunity = {
                        'route': f"{base_pair} -> {inter_pair} -> {final_pair}",
                        'profit_percentage': profit_percentage,
                        'prices': {base_pair: base_price, inter_pair: inter_price, final_pair: final_price},
                        'amounts': {'initial': initial_amount, 'final': amount},
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    opportunities.append(opportunity)
                    
                    # Print detallado de la oportunidad
                    print(f"\n💰 OPORTUNIDAD ENCONTRADA!")
                    print(f"   Ruta: {opportunity['route']}")
                    print(f"   Beneficio: {profit_percentage:.4f}%")
                    print(f"   Inicial: ${initial_amount:.2f} → Final: ${amount:.2f}")
                    print(f"   Precios: {base_pair}=${base_price:.4f}, {inter_pair}=${inter_price:.4f}, {final_pair}=${final_price:.4f}")
                    print(f"   Fees: {self.trading_fee}%, Slippage: {self.slippage}%")
            
            except Exception as e:
                logger.warning(f"Error escaneando {base_pair}->{inter_pair}->{final_pair}: {e}")
                continue
        
        # Guardar en historial
        with self.lock:
            self.opportunities_history.extend(opportunities)
            if len(self.opportunities_history) > 100:
                self.opportunities_history = self.opportunities_history[-100:]
        
        return sorted(opportunities, key=lambda x: x['profit_percentage'], reverse=True)

    def get_dashboard_data(self) -> Dict:
        """Obtiene datos para dashboard"""
        try:
            with self.lock:
                recent_opportunities = self.opportunities_history[-10:] if self.opportunities_history else []
                total_opportunities = len(self.opportunities_history)
                
                avg_profit = 0
                max_profit = 0
                if self.opportunities_history:
                    profits = [opp['profit_percentage'] for opp in self.opportunities_history]
                    avg_profit = sum(profits) / len(profits)
                    max_profit = max(profits)
                
                current_prices = self.get_all_prices()
                
                return {
                    'status': {
                        'bot_running': self.running,
                        'websocket_status': "Conectado" if (self.websocket and self.websocket.is_running()) else "Desconectado",
                        'total_triangular_pairs': len(self.triangular_pairs),
                        'monitored_pairs': len(current_prices)
                    },
                    'opportunities': {
                        'recent': recent_opportunities,
                        'total_found': total_opportunities,
                        'average_profit': round(avg_profit, 4),
                        'max_profit': round(max_profit, 4)
                    },
                    'prices': {
                        'total_pairs': len(current_prices),
                        'sample_prices': dict(list(current_prices.items())[:10])
                    },
                    'last_update': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo datos: {e}")
            return {'status': {'error': str(e)}}

    async def start_scanning(self):
        """Inicializa el bot y comienza a escanear oportunidades sin el bucle principal"""
        try:
            await self.initialize()
            self.running = True
            logger.info("Bot iniciado en modo escaneo")
        except Exception as e:
            logger.error(f"Error iniciando bot: {e}")
            raise

    async def run(self):
        """Ejecuta el bot con bucle principal"""
        logger.info("Iniciando bot de arbitraje...")
        await self.initialize()
        self.running = True
        
        print(f"\n🚀 Bot iniciado con configuración:")
        print(f"   Moneda base: {self.base_currency}")
        print(f"   Trading fee: {self.trading_fee}%")
        print(f"   Slippage: {self.slippage}%")
        print(f"   Umbral mínimo: {self.min_profit_threshold}%")
        print(f"   Intervalo de escaneo: {self.update_interval}s")
        print(f"   Pares triangulares: {len(self.triangular_pairs)}")
        print("=" * 60)
        
        try:
            while self.running:
                opportunities = await self.scan_opportunities()
                if opportunities:
                    print(f"\n✅ Encontradas {len(opportunities)} oportunidades en este escaneo")
                    best_opp = opportunities[0]
                    print(f"🏆 Mejor oportunidad: {best_opp['route']} - {best_opp['profit_percentage']:.4f}%")
                else:
                    print("❌ No se encontraron oportunidades en este escaneo")
                
                await asyncio.sleep(self.update_interval)
        except KeyboardInterrupt:
            logger.info("Deteniendo bot...")
        except Exception as e:
            logger.error(f"Error en ejecución: {e}")
        finally:
            self.running = False
            if self.websocket:
                self.websocket.stop()

    def stop(self):
        """Detiene el bot"""
        self.running = False
        if self.websocket:
            self.websocket.stop()
