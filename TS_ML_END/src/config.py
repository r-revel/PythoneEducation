import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    YAHOO_CACHE_DIR = os.getenv('YAHOO_CACHE_DIR', './cache')
    LOG_FILE = os.getenv('LOG_FILE', './logs.csv')
    HISTORICAL_YEARS = int(os.getenv('HISTORICAL_YEARS', 2))
    FORECAST_DAYS = int(os.getenv('FORECAST_DAYS', 30))

    # Модельные константы
    TRAIN_TEST_SPLIT = 0.8
    LAG_FEATURES = [1, 2, 3, 5, 7, 14]
    WINDOW_SIZES = [7, 14, 30]

    # Метрики для выбора модели
    METRICS = ['rmse', 'mape', 'mae']
