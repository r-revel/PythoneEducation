import csv
import os
from datetime import datetime
from typing import Dict
from config import Config

class LogService:
    def __init__(self, log_file=None):
        self.log_file = log_file or Config.LOG_FILE
        self._ensure_header()
    
    def _ensure_header(self):
        """Создание файла с заголовками, если не существует"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'user_id',
                    'ticker',
                    'investment_amount',
                    'best_model',
                    'rmse',
                    'mape',
                    'profit',
                    'profit_percentage',
                    'processing_time'
                ])
    
    def log_request(self, user_id: int, ticker: str, investment_amount: float,
                   best_model: str, metrics: Dict, profit: float, 
                   profit_percentage: float, processing_time: float):
        """Логирование запроса пользователя"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'ticker': ticker.upper(),
            'investment_amount': investment_amount,
            'best_model': best_model,
            'rmse': metrics.get('rmse', 0),
            'mape': metrics.get('mape', 0),
            'profit': profit,
            'profit_percentage': profit_percentage,
            'processing_time': processing_time
        }
        
        with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=log_entry.keys())
            writer.writerow(log_entry)