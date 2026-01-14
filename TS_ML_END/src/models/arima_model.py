import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from models.ml_model import BaseModel

class ARIMAModel(BaseModel):
    def __init__(self, order=(5,1,0)):
        self.order = order
        self.model = None
    
    def fit(self, X_train, y_train):
        # Для ARIMA используем только временной ряд
        self.model = ARIMA(y_train, order=self.order)
        self.model = self.model.fit()
        return self
    
    def predict(self, X):
        # Для ARIMA X не используется
        steps = len(X) if hasattr(X, '__len__') else 1
        return self.model.forecast(steps=steps)
    
    def forecast(self, last_data, steps: int) -> np.ndarray:
        return self.model.forecast(steps=steps)
    
    def evaluate(self, y_true, y_pred):
        # ARIMA может вернуть меньше предсказаний
        min_len = min(len(y_true), len(y_pred))
        y_true = y_true[:min_len]
        y_pred = y_pred[:min_len]
        return super().evaluate(y_true, y_pred)