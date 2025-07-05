import csv
import logging
from datetime import datetime
from typing import Dict, List

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradeLogger:
    def __init__(self, config: Dict):
        """
        Inicializa el logger de trades.
        
        Args:
            config (Dict): Diccionario con la configuración del bot
        """
        self.config = config
        self.log_file = 'output/trades.csv'
        if self.config['settings']['monitoring']['save_trades']:
            self.initialize_trade_log()

    def initialize_trade_log(self):
        """Inicializa el archivo de registro de trades."""
        try:
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if f.tell() == 0:  # Si el archivo está vacío
                    writer.writerow(['timestamp', 'pair1', 'pair2', 'pair3', 'profit', 'amount', 'status'])
            logger.info(f"Archivo de trades inicializado: {self.log_file}")
        except Exception as e:
            logger.error(f"Error al inicializar archivo de trades: {e}")

    def log_trade(self, trade_info: Dict):
        """
        Registra un trade en el archivo CSV.
        
        Args:
            trade_info (Dict): Diccionario con la información del trade
                - pairs: Lista de pares involucrados
                - profit: Ganancia del trade
                - amount: Cantidad del trade
                - status: Estado del trade (PENDING, SUCCESS, FAILED)
        """
        if not self.config['settings']['monitoring']['save_trades']:
            return
            
        try:
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    trade_info['pairs'][0],
                    trade_info['pairs'][1],
                    trade_info['pairs'][2],
                    trade_info['profit'],
                    trade_info['amount'],
                    trade_info['status']
                ])
            logger.info(f"Trade registrado: {trade_info['pairs']} - {trade_info['status']}")
        except Exception as e:
            logger.error(f"Error al registrar trade: {e}")

    def get_trade_history(self, limit: int = None) -> List[Dict]:
        """
        Obtiene el historial de trades.
        
        Args:
            limit (int, optional): Número máximo de trades a retornar. Si es None, retorna todos.
            
        Returns:
            List[Dict]: Lista de trades con su información
        """
        try:
            trades = []
            with open(self.log_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trades.append({
                        'timestamp': row['timestamp'],
                        'pairs': [row['pair1'], row['pair2'], row['pair3']],
                        'profit': float(row['profit']),
                        'amount': float(row['amount']),
                        'status': row['status']
                    })
            
            if limit:
                trades = trades[-limit:]
            
            return trades
        except Exception as e:
            logger.error(f"Error al obtener historial de trades: {e}")
            return []

    def get_daily_stats(self) -> Dict:
        """
        Obtiene estadísticas diarias de trading.
        
        Returns:
            Dict: Diccionario con estadísticas diarias
                - total_trades: Número total de trades
                - successful_trades: Número de trades exitosos
                - failed_trades: Número de trades fallidos
                - total_profit: Ganancia total
                - average_profit: Ganancia promedio por trade
        """
        try:
            trades = self.get_trade_history()
            today = datetime.now().date()
            
            daily_trades = [
                trade for trade in trades 
                if datetime.fromisoformat(trade['timestamp']).date() == today
            ]
            
            successful_trades = [t for t in daily_trades if t['status'] == 'SUCCESS']
            failed_trades = [t for t in daily_trades if t['status'] == 'FAILED']
            
            total_profit = sum(t['profit'] for t in successful_trades)
            avg_profit = total_profit / len(successful_trades) if successful_trades else 0
            
            return {
                'total_trades': len(daily_trades),
                'successful_trades': len(successful_trades),
                'failed_trades': len(failed_trades),
                'total_profit': total_profit,
                'average_profit': avg_profit
            }
        except Exception as e:
            logger.error(f"Error al obtener estadísticas diarias: {e}")
            return {
                'total_trades': 0,
                'successful_trades': 0,
                'failed_trades': 0,
                'total_profit': 0,
                'average_profit': 0
            }