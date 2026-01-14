import matplotlib.pyplot as plt
import numpy as np
from typing import List
import os
from datetime import datetime, timedelta
from services.analytics_service import TradingPoint


class PlotService:
    def __init__(self, output_dir='./plots'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_forecast_plot(self,
                             historical_prices: np.ndarray,
                             forecast_prices: np.ndarray,
                             trading_points: List[TradingPoint],
                             ticker: str) -> str:
        """Создание графика с прогнозом и торговыми точками"""
        plt.figure(figsize=(12, 6))

        # Подготовка данных
        total_days = len(historical_prices) + len(forecast_prices)
        dates = [datetime.now() - timedelta(days=total_days - i)
                 for i in range(total_days)]

        # Исторические данные
        hist_dates = dates[:len(historical_prices)]
        plt.plot(hist_dates, historical_prices, 'b-', label='Исторические данные', linewidth=2)

        # Прогноз
        forecast_dates = dates[len(historical_prices):]
        plt.plot(forecast_dates, forecast_prices, 'r--', label='Прогноз', linewidth=2)

        # Вертикальная линия разделения
        separation_date = hist_dates[-1]
        plt.axvline(x=separation_date, color='gray', linestyle=':', alpha=0.5)

        # Торговые точки
        buy_points = [tp for tp in trading_points if tp.action == 'buy']
        sell_points = [tp for tp in trading_points if tp.action == 'sell']

        if buy_points:
            buy_dates = [forecast_dates[tp.date_index] for tp in buy_points]
            buy_prices = [tp.price for tp in buy_points]
            plt.scatter(buy_dates, buy_prices, color='green', s=100,
                        marker='^', label='Покупка', zorder=5)

        if sell_points:
            sell_dates = [forecast_dates[tp.date_index] for tp in sell_points]
            sell_prices = [tp.price for tp in sell_points]
            plt.scatter(sell_dates, sell_prices, color='red', s=100,
                        marker='v', label='Продажа', zorder=5)

        # Настройки графика
        plt.title(f'Прогноз цен акций {ticker}', fontsize=14, fontweight='bold')
        plt.xlabel('Дата')
        plt.ylabel('Цена ($)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Сохранение
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ticker}_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150)
        plt.close()

        return filepath
