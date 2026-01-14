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
        predictions = []
        current_features = last_data.copy()

        for _ in range(steps):
            if not hasattr(self.model, 'feature_names_in_'):
                train_features = self.last_features.columns
            else:
                train_features = self.model.feature_names_in_

            current_features = current_features.reindex(columns=train_features)

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
