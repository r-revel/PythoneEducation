import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from config import Config


class DataService:
    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or Config.YAHOO_CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_stock_data(self, ticker: str) -> pd.DataFrame:
        """Загружает исторические данные по тикеру"""
        cache_file = os.path.join(self.cache_dir, f"{ticker.lower()}.csv")

        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            if not df.empty:
                return df

        # Загружаем с Yahoo Finance
        end_date = datetime.now()
        start_date = end_date - timedelta(days=Config.HISTORICAL_YEARS * 365)

        try:
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)

            if df.empty:
                raise ValueError(f"Нет данных для тикера {ticker}")

            df.to_csv(cache_file)
            return df

        except Exception as e:
            raise ValueError(f"Ошибка загрузки данных для {ticker}: {str(e)}")

    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Предобработка данных и создание признаков"""
        data = df[['Close']].copy()
        data.columns = ['price']
        data = data.dropna()

        # Создание лаговых признаков
        for lag in Config.LAG_FEATURES:
            data[f'lag_{lag}'] = data['price'].shift(lag)

        # Скользящие средние
        for window in Config.WINDOW_SIZES:
            data[f'sma_{window}'] = data['price'].rolling(window=window).mean()
            data[f'std_{window}'] = data['price'].rolling(window=window).std()

        # Целевая переменная (цена через 1 день)
        data['target'] = data['price'].shift(-1)
        data = data.dropna()

        return data

    def split_data(self, data: pd.DataFrame) -> tuple:
        """Разделение данных на train и test"""
        split_idx = int(len(data) * Config.TRAIN_TEST_SPLIT)
        train = data.iloc[:split_idx]
        test = data.iloc[split_idx:]

        # Подготовка признаков
        X_train = train.drop(['price', 'target'], axis=1)
        y_train = train['target']
        X_test = test.drop(['price', 'target'], axis=1)
        y_test = test['target']

        return X_train, y_train, X_test, y_test, train['price'], test['price']
