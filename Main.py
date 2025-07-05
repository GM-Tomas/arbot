import os
import time
import logging
import json
from typing import Dict, List, Tuple, Set
from binance.client import Client
from binance.exceptions import BinanceAPIException
import asyncio
import aiohttp
from classes.trade_logger import TradeLogger
from classes.price_websocket_manager import PriceWebSocketManager
from classes.arbitrage_bot import ArbitrageBot
import websocket

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output/arbitrage_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    bot = ArbitrageBot()
    asyncio.run(bot.run()) 