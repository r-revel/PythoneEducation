import numpy as np
from sklearn.ensemble import RandomForestRegressor
from models.ml_model import BaseModel


class RandomForestModel(BaseModel):
    def __init__(self, n_estimators=100, random_state=42):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1
        )
        self.last_features = None

    def fit(self, X_train, y_train):
        self.model.fit(X_train, y_train)
        self.last_features = X_train.iloc[-1:].copy()
        return self

    def predict(self, X):
        return self.model.predict(X)

    def forecast(self, last_data, steps: int) -> np.ndarray:
        """Рекурсивный прогноз для Random Forest"""
        predictions = []
        current_features = last_data.copy()

        for _ in range(steps):
            pred = self.model.predict(current_features)[0]
            predictions.append(pred)

            # Обновляем признаки для следующего шага
            # Сдвигаем лаги
            for lag in sorted([1, 2, 3, 5, 7, 14], reverse=True):
                if f'lag_{lag}' in current_features.columns:
                    if lag == 1:
                        current_features[f'lag_{lag}'] = pred
                    else:
                        current_features[f'lag_{lag}'] = current_features[f'lag_{lag-1}']

            # Пересчитываем скользящие средние (упрощенно)
            # В реальном проекте нужна более сложная логика

        return np.array(predictions)
