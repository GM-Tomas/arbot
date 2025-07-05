import unittest
import asyncio
from classes.arbitrage_bot import ArbitrageBot
import json
from unittest.mock import Mock, patch

class TestArbitrageBot(unittest.TestCase):
    def setUp(self):
        # Configuración de prueba
        self.test_config = {
            "binance": {
                "api_key": "test_key",
                "api_secret": "test_secret"
            },
            "settings": {
                "base_currency": "USDT",
                "top_n_pairs": 50,
                "update_interval": 5,
                "fixed_slippage": 0.1,
                "fixed_trading_fee": 0.1
            }
        }
        
        # Crear instancia del bot con configuración de prueba
        self.bot = ArbitrageBot()
        self.bot.config = self.test_config
        
        # Datos mock para testing
        self.mock_triangular_pairs = [
            ("BTCUSDT", "BTCEUR", "EURUSDT"),
            ("ETHUSDT", "ETHEUR", "EURUSDT"),
            ("BNBUSDT", "BNBEUR", "EURUSDT")
        ]
        
        # Precios mock que simulan una oportunidad de arbitraje
        self.mock_prices = {
            "BTCUSDT": 50000.0,  # 1 BTC = 50000 USDT
            "BTCEUR": 45000.0,   # 1 BTC = 45000 EUR
            "EURUSDT": 1.1,      # 1 EUR = 1.1 USDT
            "ETHUSDT": 3000.0,   # 1 ETH = 3000 USDT
            "ETHEUR": 2700.0,    # 1 ETH = 2700 EUR
            "BNBUSDT": 400.0,    # 1 BNB = 400 USDT
            "BNBEUR": 360.0      # 1 BNB = 360 EUR
        }

   
    def test_calculate_profit_for_btc_triangle(self):
        """Test específico para el cálculo de profit del triángulo BTC"""
        # Valores de prueba
        initial_amount = 1000.0  # 1000 USDT
        btc_usdt_price = 50000.0
        btc_eur_price = 46000.0
        eur_usdt_price = 1.1
        fee = 0.1  # 0.1%
        
        print("\n=== Simulación de arbitraje triangular ===")
        print(f"Cantidad inicial: {initial_amount} USDT")
        
        # Simular la ruta buy->sell->sell
        amount = initial_amount
        
        # Primer trade (buy BTC con USDT)
        amount = (amount * (1 - fee/100)) / btc_usdt_price
        print(f"Cantidad de BTC obtenida: {amount:.8f} BTC")
        
        # Segundo trade (BTC por EUR)
        amount = (amount * (1 - fee/100)) * btc_eur_price
        print(f"Cantidad de BTC obtenida: {amount:.8f} Eur")
        
        # Tercer trade (EUR por usdt)
        amount = (amount * (1 - fee/100)) * eur_usdt_price
        print(f"Cantidad de EUR obtenida: {amount:.8f} usdt")
        
        # Calcular rentabilidad
        profit_percentage = ((amount - initial_amount) / initial_amount) * 100
        print(f"Profit: {profit_percentage:.4f}%")

        # Verificar que la rentabilidad es la esperada
        expected_profit = 0.896  # Valor calculado previamente
        self.assertAlmostEqual(profit_percentage, expected_profit, places=2)

def run_tests():
    """Función para ejecutar los tests"""
    unittest.main()

if __name__ == '__main__':
    # Configurar el event loop para los tests asíncronos
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TestArbitrageBot().test_simulate_triangular_arbitrage_profitability())
    run_tests() 