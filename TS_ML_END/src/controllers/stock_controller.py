from controllers.base_controller import BaseController
from view.base import MViewItem, MViewOption, FormField
from functools import partial
import time
from datetime import datetime

from services.data_service import DataService
from services.model_selector import ModelSelector
from services.analytics_service import AnalyticsService
from services.plot_service import PlotService
from services.log_service import LogService
from config import Config
import numpy as np


class StockController(BaseController):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.data_service = DataService()
        self.plot_service = PlotService()
        self.log_service = LogService()
        self.user_sessions = {}  # Простое хранилище сессий

    async def menu(self, update):
        """Главное меню бота"""

        options = [
            MViewOption(title='📈 Получить прогноз акций', link='/forecast'),
            MViewOption(title='📊 Моя статистика', link='/stats'),
            MViewOption(title='ℹ️ Помощь', link='/help'),
        ]

        return partial(
            self.ctx.driver.render_message,
            content=MViewItem(
                title="📊 Stock Forecast Bot",
                text="Добро пожаловать! Я помогу вам проанализировать акции и построить прогноз.",
                option=options
            )
        )

    async def start_forecast(self, update):
        """Начало процесса прогнозирования"""
        user_id = update.effective_user.id

        # Создаем сессию для пользователя
        self.user_sessions[user_id] = {
            'step': 'ticker',
            'data': {}
        }

        form_fields = [
            FormField(
                name='ticker',
                field_type='text',
                title='Введите тикер компании',
                placeholder='(например: AAPL, MSFT, GOOGL)'
            ),
            FormField(
                name='amount',
                field_type='text',
                title='Введите сумму для условной инвестиции ($)',
                placeholder='1000'
            )
        ]
        form_item = MViewItem(
            title="Ввод тикера",
            text="Пожалуйста, введите тикер компании, которую хотите проанализировать.",
            form_fields=form_fields,
            form_complete='/forecast/process'
        )

        self.ctx.driver.getRouter().set_current_item(form_item)
        return partial(
            self.ctx.driver.render_message,
            content=form_item
        )

    async def process_forecast(self, update, request):
        """Обработка запроса и построение прогноза"""
        user_id = update.effective_user.id

        try:
            # Получаем введенный тикер
            ticker = request.get("ticker", "")

            # Пробуем загрузить данные для проверки
            self.data_service.fetch_stock_data(ticker)

            # Сохраняем тикер в сессии
            self.user_sessions[user_id]['data']['ticker'] = ticker
            self.user_sessions[user_id]['step'] = 'amount'

        except Exception as e:
            return await self.show_error(update, f"Ошибка: {str(e)}\nПожалуйста, введите корректный тикер.")

        try:
            start_time = time.time()
            session = self.user_sessions[user_id]

            # Получаем данные из сессии
            ticker = session['data']['ticker']
            amount = int(request.get("amount", ""))

            # Отправляем сообщение о начале обработки

            await self.ctx.driver.render_message(
                content=MViewItem(
                    title="⏳ Обработка",
                    text="Загружаю данные и строю прогноз. Это может занять несколько минут..."
                ),
                update=update
            )

            # 1. Загрузка и подготовка данных
            df = self.data_service.fetch_stock_data(ticker)
            processed_data = self.data_service.preprocess_data(df)
            X_train, y_train, X_test, y_test, train_prices, test_prices = \
                self.data_service.split_data(processed_data)

            # 2. Обучение и выбор модели
            model_selector = ModelSelector()
            results = model_selector.train_and_evaluate(X_train, y_train, X_test, y_test)
            best_model, best_metrics = model_selector.select_best_model(results)

            # 3. Построение прогноза
            last_data = processed_data.iloc[-1:]
            forecast = model_selector.make_forecast(last_data, Config.FORECAST_DAYS)

            # 4. Генерация рекомендаций
            analytics = AnalyticsService(amount)
            trading_points = analytics.find_trading_points(forecast)
            simulation = analytics.simulate_trading(forecast, trading_points)
            summary = analytics.generate_summary(simulation, df['Close'].iloc[-1])

            # 5. Создание графика
            all_prices = np.concatenate([train_prices.values, test_prices.values])
            plot_path = self.plot_service.create_forecast_plot(
                all_prices[-100:],  # Последние 100 точек
                forecast,
                trading_points,
                ticker
            )

            # 6. Логирование
            processing_time = time.time() - start_time
            self.log_service.log_request(
                user_id=user_id,
                ticker=ticker,
                investment_amount=amount,
                best_model=best_model.get_name(),
                metrics=best_metrics,
                profit=simulation['profit'],
                profit_percentage=simulation['profit_percentage'],
                processing_time=processing_time
            )

            # 7. Формирование ответа
            options = [
                MViewOption(title='🔄 Новый прогноз', link='/forecast'),
                MViewOption(title='📊 Главное меню', link='/'),
            ]

            with open(plot_path, 'rb') as photo:
                photo_data = photo.read()
                return partial(
                    self.ctx.driver.render_message,
                    content=MViewItem(
                        title=f"📈 Прогноз для {ticker}\nЛучшая модель: {best_model.get_name()}",
                        text=summary,
                        option=options
                    ),
                    image_url=photo_data
                )

        except ValueError as e:
            return partial(self.show_error, f"Ошибка ввода: {str(e)}")
        except Exception as e:
            return partial(self.show_error, f"Произошла ошибка: {str(e)}")
        finally:
            # Очищаем сессию
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]

    async def show_stats(self, update):
        """Показать статистику пользователя"""
        # Здесь можно реализовать чтение логов и показ статистики
        return await self.show_message(
            update=update,
            title="📊 Статистика",
            text="Статистика будет доступна в будущих версиях.",
            options=[MViewOption(title="Назад", link="/")]
        )

    async def show_help(self, update):
        """Показать справку"""
        help_text = """
        🤖 **Stock Forecast Bot - Помощь**

        **Как пользоваться:**
        1. Выберите "Получить прогноз акций"
        2. Введите тикер компании (например: AAPL, MSFT, TSLA)
        3. Введите сумму для условной инвестиции
        4. Дождитесь результатов анализа

        **Что анализирует бот:**
        • Загружает исторические данные за 2 года
        • Обучает 3 различные модели прогнозирования
        • Выбирает лучшую модель по метрикам качества
        • Строит прогноз на 30 дней
        • Дает рекомендации по покупке/продаже
        • Рассчитывает потенциальную прибыль

        **Примеры тикеров:**
        • AAPL - Apple
        • MSFT - Microsoft
        • GOOGL - Alphabet (Google)
        • TSLA - Tesla
        • AMZN - Amazon
        """
        return partial(
            self.show_message,
            title="ℹ️ Помощь",
            text=help_text,
            options=[MViewOption(title="Начать анализ", link="/forecast")]
        )