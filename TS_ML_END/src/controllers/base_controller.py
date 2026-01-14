from telegram import Update
from controllers.app_context import AppContext
from view.base import MViewItem, MViewOption


class BaseController:

    def __init__(self, context: AppContext):
        self.ctx = context
        self.chat_id = None
        self.user_id = None
        self.ctx.driver.set_state_handler(self._state_handler)

    async def show_message(self, title: str, text: str, options=None, **kwargs):
        if options is None:
            options = [MViewOption(title="В меню", link="/")]

        await self.ctx.driver.render_message(
            content=MViewItem(title=title, text=text, option=options),
            **kwargs
        )

    async def show_error(self, error_message: str, **kwargs):
        return await self.show_message(
            title="Ошибка",
            text=error_message,
            options=[MViewOption(title="Назад", link="/")],
            **kwargs
        )

    def _state_handler(self, update: Update):
        if update.effective_user:
            self.user_id = update.effective_user.id
            self.chat_id = update._effective_message.chat_id