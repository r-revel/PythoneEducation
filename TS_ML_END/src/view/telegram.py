from typing import Callable, Dict, Optional, List, Any, Union
from dataclasses import dataclass
from telegram import InputMediaPhoto, KeyboardButton, LabeledPrice, Update, Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters
)
import inspect

from view.base import AView, MViewItem
from router.router import Router
from telegram.error import BadRequest

class TelegramClient:
    def __init__(self, token: str):
        self.token = token
        self.application: Optional[Application] = None
        self._is_running = False
        self.router: Optional[Router] = None
        # Добавляем обработчик состояния (по умолчанию None)
        self.state_handler: Optional[Callable] = None

    def set_state_handler(self, handler: Callable):
        """Устанавливает функцию-обработчик состояния, которая будет вызываться перед отправкой сообщений."""
        self.state_handler = handler

    async def init(self, callback=None, router: Optional['Router'] = None):
        """Инициализация бота"""
        self.router = router
        self.application = Application.builder().token(self.token).build()

        handlers = [
            CommandHandler("start", self._handle_start),
            MessageHandler(filters.TEXT & ~filters.COMMAND,
                           self._handle_message),
            CallbackQueryHandler(self._handle_callback),
            PreCheckoutQueryHandler(self._handle_pre_checkout),
            MessageHandler(filters.SUCCESSFUL_PAYMENT, self._handle_successful_payment),
        ]

        for handler in handlers:
            self.application.add_handler(handler)

        await self.application.initialize()
        await self.application.start()

        if self.application.updater:
            await self.application.updater.start_polling()

        self._is_running = True

        if callback:
            await callback() if inspect.iscoroutinefunction(callback) else callback()

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.state_handler is not None:
            self.state_handler(update=update)
        try:
            await self.getRouter().handle("/", update=update, newMessage=True)
        except ValueError as e:
            await self.render_message(
                content="Меню недоступно. Попробуйте позже.",
                newMessage=True
            )
            print(f"Route error: {e}")

    async def render_message(
        self,
        content: Union[str, MViewItem],
        newMessage: Optional[bool] = None,
        update: Optional[str] = None,
        removerCurrent: Optional[bool] = None,
        redirectUrl: Optional[str] = None,
        **kwargs
    ) -> int:
        """
        Универсальный метод для отправки/обновления сообщения
        Возвращает ID сообщения
        """

        if (removerCurrent):
            message_id = getattr(
                getattr(update, "effective_message", None), "message_id", None)
            if (message_id is not None):
                await self.delete_message(message_id=message_id)
            message_id = None

        if (not newMessage):
            message_id = getattr(
                getattr(update, "effective_message", None), "message_id", None)
        else:
            message_id = None

        print('message_id', message_id)

        chat_id = getattr(
            getattr(update, "effective_message", None), "chat_id", None)

        if chat_id is None:
            raise ValueError("Chat ID not provided")

        if isinstance(content, str):
            render = await self._render_text(
                text=content,
                message_id=message_id,
                chat_id=chat_id,
                **kwargs
            )
            if (redirectUrl is not None):
                await self.getRouter().handle(redirectUrl, update=update, newMessage=True)
            return render

        elif isinstance(content, MViewItem):
            render = await self._render_item(
                item=content,
                message_id=message_id,
                chat_id=chat_id,
                **kwargs
            )
            if (redirectUrl is not None):
                await self.getRouter().handle(redirectUrl, update=update, newMessage=True)
            return render
        else:
            raise ValueError("Unsupported content type")


    def getRouter(self) -> Router:
        if self.router:
            return self.router
        else:
            raise Exception('Ошибка: не удалось найти router')

    async def _render_text(
        self,
        text: str,
        chat_id: int,
        message_id: Optional[int] = None,
        **kwargs
    ) -> int:
        """Обработка текстового сообщения"""
        if message_id:

            try:
                msg = await self.application.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    **kwargs
                )
            except BadRequest as e:
                msg = await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    **kwargs
                )

            return msg.message_id
        else:
            # Отправляем новое сообщение
            msg = await self.application.bot.send_message(
                chat_id=chat_id,
                text=text,
                **kwargs
            )
            return msg.message_id

    async def _render_photo(
        self,
        photo: str,
        caption: Optional[str] = None,
        message_id: Optional[int] = None,
        **kwargs
    ) -> int:
        """Обработка сообщения с фото"""
        if message_id:
            try:
                # Пытаемся обновить существующее сообщение с фото
                msg = await self.application.bot.edit_message_media(
                    chat_id=self.chat_id,
                    message_id=message_id,
                    media=InputMediaPhoto(photo, caption=caption),
                    **kwargs
                )
                return msg.message_id
            except Exception as e:
                print(f"Can't update photo message, sending new: {e}")
                await self.delete_message(message_id, **kwargs)

        # Отправляем новое фото
        msg = await self.application.bot.send_photo(
            chat_id=self.chat_id,
            photo=photo,
            caption=caption,
            **kwargs
        )
        return msg.message_id

    def _create_item_keyboard(self, item: MViewItem) -> Optional[InlineKeyboardMarkup]:
        """Создание клавиатуры для элемента"""
        if hasattr(item, 'option') and item.option:
            buttons = []
            for opt in item.option:
                if hasattr(opt, 'action') and opt.action == "web_app":
                    button = InlineKeyboardButton(text=opt.title, web_app=WebAppInfo(url=opt.link))
                elif hasattr(opt, 'action') and opt.action == "open_url":
                    button = InlineKeyboardButton(opt.title, url=opt.link)
                else:
                    button = InlineKeyboardButton(opt.title, callback_data=opt.link)
                buttons.append([button])
            return InlineKeyboardMarkup(buttons)
        return None

    async def delete_message(self, message_id: int | None, **kwargs) -> bool:

        update = kwargs.get('update')
        chat_id = getattr(
            getattr(update, "effective_message", None), "chat_id", None)

        """Удаление сообщения"""
        try:
            await self.application.bot.delete_message(chat_id, message_id)
            return True
        except Exception as e:
            print(f"Error deleting message: {e}")
            return False

    async def stop(self):
        """Остановка бота"""
        if self.application:
            if self.application.updater:
                await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        self._is_running = False

    async def _render_item(
        self,
        item: MViewItem,
        chat_id: int,
        message_id: Optional[int] = None,
        **kwargs
    ) -> int:
        """Обработка элемента с возможным изображением или формой"""

        # Старая логика для обычных элементов
        text = f"<b>{item.title}</b>\n{item.text}"
        reply_markup = self._create_item_keyboard(item)

        if hasattr(item, 'image_url') and item.image_url:
            return await self._render_photo(
                photo=item.image_url,
                caption=text,
                message_id=message_id,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            return await self._render_text(
                text=text,
                message_id=message_id,
                chat_id=chat_id,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.state_handler is not None:
            self.state_handler(update=update)

        if not self.router:
            return

        await self.router.handle(update.message.text, update=update)


    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.state_handler is not None:
            self.state_handler(update=update)

        if not self.router or not update.callback_query:
            return

        callback_query = update.callback_query
        callback_data = callback_query.data or ""

        await self.router.handle(callback_data, update=update)


    async def _handle_pre_checkout(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка предварительного запроса на оплату"""
        query = update.pre_checkout_query
        # Здесь можно добавить логику проверки заказа
        await query.answer(ok=True)

    async def _handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка успешного платежа"""
        successful_payment = update.message.successful_payment

        # Если у вас есть router, можно перенаправить на нужный маршрут
        if self.getRouter():
            await self.getRouter().handle("/payment_success", update=update, payment_data=successful_payment)
