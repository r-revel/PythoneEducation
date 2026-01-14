import numpy as np
from typing import List, Dict, Tuple
from models.ml_model import BaseModel
from models.rf_model import RandomForestModel
from models.arima_model import ARIMAModel
from models.lstm_model import PyTorchLSTMModel


class ModelSelector:
    def __init__(self):
        self.models: List[BaseModel] = [
            RandomForestModel(n_estimators=100),
            ARIMAModel(order=(5, 1, 0)),
            PyTorchLSTMModel(sequence_length=30, epochs=30)
        ]
        self.best_model = None
        self.best_metrics = None

    def train_and_evaluate(self, X_train, y_train, X_test, y_test) -> Dict:
        """Обучение и оценка всех моделей"""
        results = {}

        for model in self.models:
            try:
                # Обучение
                model.fit(X_train, y_train)

                # Прогноз на тестовой выборке
                y_pred = model.predict(X_test)

                # Оценка
                metrics = model.evaluate(y_test.values, y_pred)
                results[model.get_name()] = {
                    'model': model,
                    'metrics': metrics,
                    'predictions': y_pred
                }

                print(f"{model.get_name()}: {metrics}")

            except Exception as e:
                print(f"Ошибка в модели {model.get_name()}: {str(e)}")
                continue

        return results

    def select_best_model(self, results: Dict) -> Tuple[BaseModel, Dict]:
        """Выбор лучшей модели по RMSE"""
        if not results:
            raise ValueError("Нет результатов для выбора модели")

        best_model_name = None
        best_rmse = float('inf')

        for model_name, result in results.items():
            rmse = result['metrics'].get('rmse', float('inf'))
            if rmse < best_rmse:
                best_rmse = rmse
                best_model_name = model_name

        self.best_model = results[best_model_name]['model']
        self.best_metrics = results[best_model_name]['metrics']

        return self.best_model, self.best_metrics

    def make_forecast(self, last_data, steps: int) -> np.ndarray:
        """Прогноз на будущее с использованием лучшей модели"""
        if self.best_model is None:
            raise ValueError("Модель не обучена")

        return self.best_model.forecast(last_data, steps)
