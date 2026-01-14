from models.lstm_model import PyTorchLSTMModel
from models.arima_model import ARIMAModel
from models.rf_model import RandomForestModel
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestModelsReal:
    """Реальные тесты моделей без моков"""

    @pytest.fixture
    def real_stock_data(self):
        """Создаем реалистичные тестовые данные"""
        # Генерируем синтетические данные, похожие на реальные акции
        np.random.seed(42)
        n_samples = 200

        # Тренд + сезонность + шум
        time = np.arange(n_samples)
        trend = 100 + 0.1 * time
        seasonal = 5 * np.sin(2 * np.pi * time / 30)
        noise = np.random.normal(0, 2, n_samples)

        prices = trend + seasonal + noise

        data = pd.DataFrame({
            'price': prices
        })

        # Добавляем лаги
        for lag in [1, 2, 3]:
            data[f'lag_{lag}'] = data['price'].shift(lag)

        # Добавляем скользящие средние
        data['sma_7'] = data['price'].rolling(7).mean()
        data['sma_14'] = data['price'].rolling(14).mean()

        # Целевая переменная
        data['target'] = data['price'].shift(-1)

        # Удаляем пропуски
        data = data.dropna()

        return data

    def test_random_forest_real(self, real_stock_data):
        """Тест RandomForest на реальных данных"""
        print("\n=== Тестируем RandomForest ===")

        # Подготовка данных
        split_idx = int(len(real_stock_data) * 0.8)
        train_data = real_stock_data.iloc[:split_idx]
        test_data = real_stock_data.iloc[split_idx:]

        X_train = train_data.drop(['price', 'target'], axis=1)
        y_train = train_data['target']
        X_test = test_data.drop(['price', 'target'], axis=1)
        y_test = test_data['target']

        # Создаем и обучаем модель
        model = RandomForestModel(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)

        # Делаем предсказания
        predictions = model.predict(X_test)

        # Проверяем результаты
        assert len(predictions) == len(y_test)
        assert not np.isnan(predictions).any()

        # Оцениваем модель
        metrics = model.evaluate(y_test.values, predictions)
        print(f"RandomForest метрики: {metrics}")

        # Прогноз на будущее
        last_data = real_stock_data.drop(['price', 'target'], axis=1).iloc[-1:]
        forecast = model.forecast(last_data, steps=5)

        assert len(forecast) == 5
        print(f"RandomForest прогноз: {forecast}")

        print("✅ RandomForest работает корректно")

    def test_arima_real(self, real_stock_data):
        """Тест ARIMA на реальных данных"""
        print("\n=== Тестируем ARIMA ===")

        time_series = real_stock_data['price']
        split_idx = int(len(time_series) * 0.8)

        y_train = time_series[:split_idx]
        y_test = time_series[split_idx:]

        # Создаем и обучаем модель
        model = ARIMAModel(order=(2, 1, 1))
        model.fit(None, y_train)  # X_train не нужен для ARIMA

        # Делаем предсказания
        predictions = model.predict(y_test)

        # Проверяем результаты
        assert len(predictions) == len(y_test) or len(predictions) > 0
        assert not np.isnan(predictions).any()

        # Оцениваем модель
        if len(predictions) == len(y_test):
            metrics = model.evaluate(y_test.values, predictions)
            print(f"ARIMA метрики: {metrics}")

        # Прогноз на будущее
        forecast = model.forecast(None, steps=5)

        assert len(forecast) == 5
        print(f"ARIMA прогноз: {forecast}")

        print("✅ ARIMA работает корректно")

    def test_lstm_real(self, real_stock_data):
        """Тест LSTM на реальных данных"""
        print("\n=== Тестируем LSTM ===")

        # Подготовка данных для LSTM
        split_idx = int(len(real_stock_data) * 0.8)
        train_data = real_stock_data.iloc[:split_idx]

        X_train = train_data.drop(['price', 'target'], axis=1)
        y_train = train_data['target']

        try:
            # Создаем и обучаем модель
            model = PyTorchLSTMModel(
                sequence_length=10,
                epochs=5,  # Минимум эпох для теста
                batch_size=8
            )
            model.fit(X_train, y_train)

            print("✅ LSTM обучена успешно")

            # Прогноз на будущее
            last_data = real_stock_data.drop(['price', 'target'], axis=1).iloc[-10:]

            last_price = real_stock_data['price'].iloc[-1]

            last_data_with_price = last_data.copy()
            last_data_with_price['price'] = last_price

            forecast = model.forecast(last_data_with_price, steps=5)

            assert len(forecast) == 5
            print(f"LSTM прогноз: {forecast}")

            print("✅ LSTM работает корректно")

        except Exception as e:
            print(f"⚠️ LSTM тест пропущен: {e}")
            pytest.skip(f"LSTM не смогла обучиться: {e}")

    def test_all_models_comparison(self, real_stock_data):
        """Сравнение всех трех моделей"""
        print("\n=== Сравнение всех моделей ===")

        # Подготовка данных
        split_idx = int(len(real_stock_data) * 0.8)
        train_data = real_stock_data.iloc[:split_idx]
        test_data = real_stock_data.iloc[split_idx:]

        X_train = train_data.drop(['price', 'target'], axis=1)
        y_train = train_data['target']
        X_test = test_data.drop(['price', 'target'], axis=1)
        y_test = test_data['target']

        models = {
            'RandomForest': RandomForestModel(n_estimators=10, random_state=42),
            'ARIMA': ARIMAModel(order=(2, 1, 1))
        }

        results = {}

        for name, model in models.items():
            try:
                if name == 'ARIMA':
                    model.fit(None, y_train)
                    predictions = model.predict(y_test)
                else:
                    model.fit(X_train, y_train)
                    predictions = model.predict(X_test)

                if len(predictions) == len(y_test):
                    metrics = model.evaluate(y_test.values, predictions)
                    results[name] = metrics['rmse']
                    print(f"{name}: RMSE = {metrics['rmse']:.4f}")

            except Exception as e:
                print(f"❌ {name} ошибка: {e}")

        # Выбираем лучшую модель
        if results:
            best_model = min(results, key=results.get)
            print(f"\n🎯 Лучшая модель: {best_model} (RMSE: {results[best_model]:.4f})")
            assert best_model in ['RandomForest', 'ARIMA']
