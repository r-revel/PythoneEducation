import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class TradingPoint:
    date_index: int
    price: float
    action: str  # 'buy' или 'sell'
    reason: str


class AnalyticsService:
    def __init__(self, investment_amount: float):
        self.investment_amount = investment_amount
        self.current_cash = investment_amount
        self.current_shares = 0

    def find_trading_points(self, prices: np.ndarray) -> List[TradingPoint]:
        """Поиск точек покупки и продажи в прогнозе"""
        trading_points = []

        # Простой алгоритм поиска локальных экстремумов
        for i in range(1, len(prices) - 1):
            if prices[i] < prices[i-1] and prices[i] < prices[i+1]:
                # Локальный минимум - покупаем
                trading_points.append(
                    TradingPoint(
                        date_index=i,
                        price=prices[i],
                        action='buy',
                        reason='Локальный минимум'
                    )
                )
            elif prices[i] > prices[i-1] and prices[i] > prices[i+1]:
                # Локальный максимум - продаем
                trading_points.append(
                    TradingPoint(
                        date_index=i,
                        price=prices[i],
                        action='sell',
                        reason='Локальный максимум'
                    )
                )

        return trading_points

    def simulate_trading(self, prices: np.ndarray, trading_points: List[TradingPoint]) -> Dict:
        """Симуляция торговли по рекомендациям"""
        history = []
        cash = self.investment_amount
        shares = 0
        trades = []

        # Сортируем точки по времени
        trading_points.sort(key=lambda x: x.date_index)

        for point in trading_points:
            if point.action == 'buy' and cash > 0:
                # Покупаем на все доступные средства
                shares_to_buy = cash / point.price
                shares += shares_to_buy
                cash = 0
                trades.append({
                    'day': point.date_index,
                    'action': 'buy',
                    'price': point.price,
                    'shares': shares_to_buy,
                    'cash_after': cash,
                    'shares_after': shares
                })

            elif point.action == 'sell' and shares > 0:
                # Продаем все акции
                cash = shares * point.price
                trades.append({
                    'day': point.date_index,
                    'action': 'sell',
                    'price': point.price,
                    'shares': shares,
                    'cash_after': cash,
                    'shares_after': 0
                })
                shares = 0

        # Финализируем позицию в конце периода
        if shares > 0:
            final_price = prices[-1]
            cash = shares * final_price
            trades.append({
                'day': len(prices) - 1,
                'action': 'final_sell',
                'price': final_price,
                'shares': shares,
                'cash_after': cash,
                'shares_after': 0
            })

        # Расчет итогов
        profit = cash - self.investment_amount
        profit_percentage = (profit / self.investment_amount) * 100 if self.investment_amount > 0 else 0

        return {
            'initial_investment': self.investment_amount,
            'final_cash': cash,
            'profit': profit,
            'profit_percentage': profit_percentage,
            'trades': trades,
            'trading_points': trading_points
        }

    def generate_summary(self, simulation_result: Dict, current_price: float) -> str:
        """Генерация текстовой сводки"""
        summary = []

        # Общая информация
        price_change = ((simulation_result['final_cash'] / self.investment_amount - 1) * 100
                        if self.investment_amount > 0 else 0)

        summary.append("📊 **ИНВЕСТИЦИОННАЯ СВОДКА**")
        summary.append("")
        summary.append(f"💰 Начальная сумма: ${self.investment_amount:,.2f}")
        summary.append(f"🏁 Итоговая сумма: ${simulation_result['final_cash']:,.2f}")
        summary.append(
            f"📈 Прибыль: ${simulation_result['profit']:,.2f} ({simulation_result['profit_percentage']:.2f}%)")
        summary.append("")

        # Точки торговли
        if simulation_result['trading_points']:
            summary.append("🔄 **ТОРГОВЫЕ РЕКОМЕНДАЦИИ:**")
            for point in simulation_result['trading_points'][:10]:  # Показываем первые 10
                action_icon = "🟢 ПОКУПКА" if point.action == 'buy' else "🔴 ПРОДАЖА"
                summary.append(f"День {point.date_index}: {action_icon} по ${point.price:.2f} ({point.reason})")

        # Сделки
        if simulation_result['trades']:
            summary.append("")
            summary.append("💼 **ВЫПОЛНЕННЫЕ СДЕЛКИ:**")
            for trade in simulation_result['trades']:
                action = "Купил" if trade['action'] == 'buy' else "Продал"
                summary.append(f"День {trade['day']}: {action} {trade['shares']:.2f} акций по ${trade['price']:.2f}")

        summary.append("")
        summary.append("⚠️ **ВАЖНО:** Этот анализ носит учебный характер и не является финансовой рекомендацией.")

        return "\n".join(summary)
