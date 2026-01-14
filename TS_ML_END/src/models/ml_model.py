from abc import ABC, abstractmethod
import numpy as np
from typing import Tuple


class BaseModel(ABC):
    @abstractmethod
    def fit(self, X_train, y_train):
        """Обучение модели"""
        pass

    @abstractmethod
    def predict(self, X) -> np.ndarray:
        """Прогнозирование"""
        pass

    @abstractmethod
    def forecast(self, last_data, steps: int) -> np.ndarray:
        """Прогноз на несколько шагов вперед"""
        pass

    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> dict:
        """Вычисление метрик качества"""
        metrics = {}

        # RMSE
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        metrics['rmse'] = rmse

        # MAPE
        mask = y_true != 0
        if mask.any():
            mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
            metrics['mape'] = mape

        # MAE
        mae = np.mean(np.abs(y_true - y_pred))
        metrics['mae'] = mae

        return metrics

    def get_name(self) -> str:
        return self.__class__.__name__
