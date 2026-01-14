import numpy as np
import pandas as pd
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
        self.trained_features = None

    def fit(self, X_train, y_train):
        self.model.fit(X_train, y_train)
        self.last_features = X_train.iloc[-1:].copy()
        self.trained_features = X_train.columns.tolist()
        return self

    def predict(self, X):
        return self.model.predict(X)

    def forecast(self, last_data, steps: int) -> np.ndarray:
        predictions = []

        if hasattr(self.model, 'feature_names_in_'):
            train_features = self.model.feature_names_in_
        else:
            train_features = self.trained_features

        current_features = last_data.copy()
        current_features = current_features.reindex(columns=train_features)

        if 'day_of_week' in train_features:
            last_day = current_features['day_of_week'].iloc[0]
        if 'month' in train_features:
            last_month = current_features['month'].iloc[0]

        for step in range(steps):
            if 'day_of_week' in train_features:
                current_day = (last_day + step) % 7
                current_features['day_of_week'] = current_day

            if 'month' in train_features:
                total_days = last_day + step
                current_month = (last_month - 1 + total_days // 30) % 12 + 1
                current_features['month'] = current_month

            pred = self.model.predict(current_features)[0]
            predictions.append(pred)

            lag_cols = [col for col in current_features.columns
                        if col.startswith('lag_')]

            for lag in sorted([int(col.split('_')[1]) for col in lag_cols],
                              reverse=True):
                if lag == 1:
                    current_features[f'lag_{lag}'] = pred
                else:
                    prev_lag = f'lag_{lag-1}'
                    if prev_lag in current_features.columns:
                        current_features[f'lag_{lag}'] = current_features[prev_lag]

        return np.array(predictions)
