import pytest
import numpy as np
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_service import DataService
from services.analytics_service import AnalyticsService
from services.plot_service import PlotService
from services.log_service import LogService

class TestServicesReal:
    """Реальные тесты сервисов"""
    
    def test_data_service_synthetic(self):
        """Тест DataService на синтетических данных"""
        print("\n=== Тестируем DataService ===")
        
        service = DataService()
        
        # Создаем синтетические данные
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
        
        df = pd.DataFrame({
            'Open': prices * 0.99,
            'High': prices * 1.02,
            'Low': prices * 0.98,
            'Close': prices,
            'Volume': np.random.randint(1000000, 5000000, 100)
        }, index=dates)
        
        # Тестируем предобработку
        processed = service.preprocess_data(df)
        
        assert isinstance(processed, pd.DataFrame)
        assert 'price' in processed.columns
        assert 'target' in processed.columns
        assert not processed.isna().any().any()
        
        # Тестируем разделение
        X_train, y_train, X_test, y_test, train_prices, test_prices = \
            service.split_data(processed)
        
        assert len(X_train) > 0
        assert len(X_test) > 0
        assert len(y_train) == len(X_train)
        assert len(y_test) == len(X_test)
        
        print(f"Обработано записей: {len(processed)}")
        print(f"Train: {len(X_train)}, Test: {len(X_test)}")
        print("✅ DataService работает корректно")
    
    def test_analytics_service(self):
        """Тест AnalyticsService"""
        print("\n=== Тестируем AnalyticsService ===")
        
        # Создаем тестовые цены с явными минимумами и максимумами
        prices = np.array([
            100, 98, 102,  # минимум на 1, максимум на 2
            101, 99, 104,  # минимум на 4, максимум на 5
            103, 101, 106  # минимум на 7, максимум на 8
        ])
        
        service = AnalyticsService(investment_amount=1000)
        
        points = service.find_trading_points(prices)
        
        assert len(points) >= 2
        print(f"Найдено торговых точек: {len(points)}")
        
        for point in points:
            print(f"  День {point.date_index}: {point.action.upper()} по ${point.price:.2f}")
        
        # Симуляция торговли
        simulation = service.simulate_trading(prices, points)
        
        assert 'profit' in simulation
        assert 'trades' in simulation
        print(f"Прибыль: ${simulation['profit']:.2f}")
        
        # Генерация сводки
        summary = service.generate_summary(simulation, current_price=105)
        
        assert isinstance(summary, str)
        assert "ИНВЕСТИЦИОННАЯ СВОДКА" in summary
        print("Сводка сгенерирована успешно")
        
        print("✅ AnalyticsService работает корректно")
    
    def test_plot_service(self, tmp_path):
        """Тест PlotService"""
        print("\n=== Тестируем PlotService ===")
        
        service = PlotService(output_dir=str(tmp_path))
        
        # Тестовые данные
        historical = np.random.randn(100) * 10 + 150
        forecast = np.random.randn(30) * 5 + 155
        
        # Тестовые торговые точки
        from services.analytics_service import TradingPoint
        points = [
            TradingPoint(date_index=5, price=152, action='buy', reason='Тест'),
            TradingPoint(date_index=15, price=158, action='sell', reason='Тест')
        ]
        
        # Создаем график
        plot_path = service.create_forecast_plot(
            historical_prices=historical,
            forecast_prices=forecast,
            trading_points=points,
            ticker="TEST"
        )
        
        assert os.path.exists(plot_path)
        assert plot_path.endswith('.png')
        print(f"График сохранен: {plot_path}")
        
        print("✅ PlotService работает корректно")
    
    def test_log_service(self, tmp_path):
        """Тест LogService"""
        print("\n=== Тестируем LogService ===")
        
        log_file = tmp_path / "test_log.csv"
        service = LogService(log_file=str(log_file))
        
        # Логируем тестовый запрос
        service.log_request(
            user_id=123456,
            ticker="AAPL",
            investment_amount=1000,
            best_model="RandomForest",
            metrics={'rmse': 2.5, 'mape': 1.5},
            profit=150,
            profit_percentage=15.0,
            processing_time=3.5
        )
        
        # Проверяем, что файл создан
        assert os.path.exists(log_file)
        
        # Читаем и проверяем логи
        logs = pd.read_csv(log_file)
        assert len(logs) == 1
        assert logs.iloc[0]['ticker'] == 'AAPL'
        assert logs.iloc[0]['profit'] == 150
        
        print(f"Запись в лог: {logs.iloc[0].to_dict()}")
        print("✅ LogService работает корректно")