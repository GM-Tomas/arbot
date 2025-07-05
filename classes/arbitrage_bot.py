import os
import time
import logging
import json
from typing import Dict, List, Tuple, Set
from binance.client import Client
from binance.exceptions import BinanceAPIException
import asyncio
import aiohttp
from .trade_logger import TradeLogger
from .price_websocket_manager import PriceWebSocketManager

logger = logging.getLogger(__name__)

class ArbitrageBot:
    def __init__(self):
        # Cargar configuración desde JSON
        try:
            with open('input/config.json', 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            logger.error(f"Error al cargar configuración: {e}")
            raise

        # Configurar cliente de Binance
        try:
            self.client = Client(
                self.config['binance']['api_key'],
                self.config['binance']['api_secret']
            )
        except Exception as e:
            logger.error(f"Error al inicializar cliente Binance: {e}")
            raise

        # Configurar parámetros del bot
        self.base_currency = self.config['settings']['base_currency']
        self.trading_pairs = set()
        self.triangular_pairs = []
        self.session = None
        
        # Inicializar logger de trades
        self.trade_logger = TradeLogger(self.config)

        # Inicializar gestor de precios
        self.price_manager = PriceWebSocketManager()
        self.price_manager.add_price_callback(self.on_price_update)

    def on_price_update(self, symbol: str, price: float):
        """Callback cuando se actualiza un precio"""
        # Aquí puedes agregar lógica adicional cuando se actualiza un precio
        print(f"Precio actualizado para {symbol}: {price}")
        pass

    async def initialize(self):
        """Inicializa el bot y obtiene los pares de trading disponibles."""
        try:
            self.session = aiohttp.ClientSession()
            self.trading_pairs = set(self.get_all_tickers())
            self.build_triangular_pairs()
            self.filter_triangular_pairs_by_volume()
            
            # Actualizar símbolos en el gestor de precios
            symbols = set()
            for base_pair, inter_pair, final_pair in self.triangular_pairs:
                symbols.update([base_pair, inter_pair, final_pair])

            time.sleep(10)
            self.price_manager.update_symbols(symbols)
            print(self.price_manager.get_all_prices())

            exit()
            
            logger.info(f"Bot inicializado con {len(self.triangular_pairs)} pares triangulares")
        except Exception as e:
            logger.error(f"Error en inicialización: {e}")
            raise

    def get_all_tickers(self) -> List[str]:
        """Obtiene todos los pares de trading disponibles."""
        try:
            exchange_info = self.client.get_exchange_info()
            return [symbol['symbol'] for symbol in exchange_info['symbols'] 
                   if symbol['status'] == 'TRADING' and symbol['isSpotTradingAllowed']]
        except BinanceAPIException as e:
            logger.error(f"Error al obtener tickers: {e}")
            return []

    def get_top_volume_pairs(self) -> List[str]:
        """
        Obtiene los top N pares con mayor volumen en las últimas 24 horas,
        donde N viene de la configuración.
        
        Returns:
            List[str]: Lista de los pares con mayor volumen
        """
        try:
            # Obtener tickers de 24h
            tickers = self.client.get_ticker()
            
            # Filtrar solo pares que terminan en la moneda base y tienen volumen
            valid_pairs = [
                ticker for ticker in tickers 
                if ticker['symbol'].endswith(self.base_currency) and 
                float(ticker['volume']) > 0
            ]
            
            # Ordenar por volumen (de mayor a menor)
            sorted_pairs = sorted(
                valid_pairs,
                key=lambda x: float(x['volume']),
                reverse=True
            )
            
            # Obtener los top N pares de la configuración
            top_pairs = [pair['symbol'] for pair in sorted_pairs[:self.config['settings']['top_n_pairs']]]
            
            return top_pairs
            
        except BinanceAPIException as e:
            logger.error(f"Error al obtener volumen de pares: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al obtener top volumen: {e}")
            return []

    def build_triangular_pairs(self):
        """Construye combinaciones triangulares simples."""
        try:
            # Obtener pares base (los que terminan en la moneda base)
            base_pairs = {pair for pair in self.trading_pairs if pair.endswith(self.base_currency)}
            logger.info(f"Pares base encontrados: {len(base_pairs)}")
            
            # Obtener todas las monedas intermedias posibles
            intermediate_currencies = set()
            for pair in base_pairs:
                base_currency = pair[:-len(self.base_currency)]
                intermediate_currencies.add(base_currency)
            
            logger.info(f"Monedas intermedias encontradas: {len(intermediate_currencies)}")
            
            # Construir pares triangulares
            self.triangular_pairs = []
            for base_pair in base_pairs:
                base_currency = base_pair[:-len(self.base_currency)]
                
                for inter_currency in intermediate_currencies:
                    if inter_currency != base_currency:
                        inter_pair = f"{base_currency}{inter_currency}"
                        final_pair = f"{inter_currency}{self.base_currency}"
                        
                        if inter_pair in self.trading_pairs and final_pair in self.trading_pairs:
                            self.triangular_pairs.append((base_pair, inter_pair, final_pair))
                            logger.debug(f"Par triangular encontrado: {base_pair} -> {inter_pair} -> {final_pair}")
            
            logger.info(f"Total de pares triangulares encontrados: {len(self.triangular_pairs)}")
            if len(self.triangular_pairs) > 0:
                logger.info(f"Ejemplo de par triangular: {self.triangular_pairs[0]}")
            
        except Exception as e:
            logger.error(f"Error al construir pares triangulares: {e}")
            raise

    def filter_triangular_pairs_by_volume(self):
        """
        Filters triangular pairs to only include those with high trading volume.
        Uses the top N pairs from get_top_volume_pairs() to ensure we only trade
        in liquid markets.
        """
        try:
            # Get top volume pairs
            top_volume_pairs = self.get_top_volume_pairs()

            logger.info(f"Obtenidos {len(top_volume_pairs)} pares con mayor volumen")
            
            # Filter triangular pairs to only include those with high volume
            filtered_pairs = []
            for base_pair, inter_pair, final_pair in self.triangular_pairs:
                # Check if all pairs in the triangle have sufficient volume
                if (base_pair in top_volume_pairs and 
                    inter_pair in self.trading_pairs and 
                    final_pair in self.trading_pairs):
                    filtered_pairs.append((base_pair, inter_pair, final_pair))
                    logger.debug(f"Par triangular con volumen aceptado: {base_pair} -> {inter_pair} -> {final_pair}")
            
            # Update triangular pairs with filtered list
            self.triangular_pairs = filtered_pairs
            logger.info(f"Filtrados {len(self.triangular_pairs)} pares triangulares con volumen suficiente")
            
            if len(self.triangular_pairs) > 0:
                logger.info(f"Ejemplo de par triangular filtrado: {self.triangular_pairs[0]}")
            
        except Exception as e:
            logger.error(f"Error al filtrar pares triangulares por volumen: {e}")
            raise

    async def simulate_triangular_arbitrage_profitability(self, initial_amount: float = 100.0) -> List[Dict]:
        """
        Versión optimizada que usa el gestor de precios para obtener precios actualizados.
        """
        try:
            opportunities = []
            
            # Valores fijos de la configuración
            slippage_percentage = self.config['settings'].get('fixed_slippage', 0.1)
            trading_fee = self.config['settings'].get('fixed_trading_fee', 0.1)
            
            # Esperar a que tengamos precios actualizados
            self.price_manager.price_update_event.wait(timeout=5)

            print(self.price_manager.get_all_prices())
            print("Símbolos monitoreados:", self.price_manager.get_all_prices().keys())
            
            # Usar solo los triángulos ya filtrados
            for base_pair, inter_pair, final_pair in self.triangular_pairs:
                try:
                    # Obtener precios actuales del gestor de precios
                    base_price = self.price_manager.get_price(base_pair)
                    inter_price = self.price_manager.get_price(inter_pair)
                    final_price = self.price_manager.get_price(final_pair)
                    
                    print(base_price, inter_price, final_price)
                    return
                    
                    if not all(price is not None for price in [base_price, inter_price, final_price]):
                        continue
                    
                    # Simular la ruta buy->sell->sell
                    amount = initial_amount
                    
                    # Primer trade (buy)
                    amount = (amount * (1 - trading_fee/100)) / base_price
                    
                    # Segundo trade (sell)
                    amount = (amount * (1 - trading_fee/100)) * inter_price
                    
                    # Tercer trade (sell)
                    amount = (amount * (1 - trading_fee/100)) * final_price
                    
                    # Calcular rentabilidad final
                    profit_percentage = ((amount - initial_amount) / initial_amount) * 100
                    
                    # Solo considerar oportunidades con beneficio positivo
                    if 0 < profit_percentage:
                        opportunities.append({
                            'route': f"{base_pair} -> {inter_pair} -> {final_pair}",
                            'profit_percentage': profit_percentage,
                            'direction': 'buy->sell->sell',
                            'fees': trading_fee,
                            'prices': {
                                base_pair: base_price,
                                inter_pair: inter_price,
                                final_pair: final_price
                            },
                            'amounts': {
                                'initial': initial_amount,
                                'final': amount
                            }
                        })
                
                except Exception as e:
                    logger.warning(f"Error al simular arbitraje para {base_pair}->{inter_pair}->{final_pair}: {e}")
                    continue
            
            # Ordenar oportunidades por rentabilidad
            opportunities.sort(key=lambda x: x['profit_percentage'], reverse=True)
            
            # Logging de resultados
            if opportunities:
                best_opp = opportunities[0]
                logger.info(f"Mejor oportunidad: {best_opp['route']} : {best_opp['profit_percentage']:.4f}%")
                logger.info(f"Precios: {best_opp['prices']}")
                logger.info(f"Cantidades: {best_opp['amounts']}")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error en simulación de arbitraje: {e}")
            return []

    async def run(self):
        """Función principal que ejecuta el bot de forma asíncrona."""
        logger.info("Iniciando bot de arbitraje triangular...")
        await self.initialize()
        
        try:
            while True:
                opportunities = await self.simulate_triangular_arbitrage_profitability()
                await asyncio.sleep(self.config['settings']['update_interval'])
                print("INTERVALO!!!")
        except KeyboardInterrupt:
            logger.info("Deteniendo bot...")
        finally:
            self.price_manager.stop()
            if self.session:
                await self.session.close()
