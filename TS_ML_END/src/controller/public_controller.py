from controller.base_controller import BaseController
from view.base import MViewItem, MViewOption
from functools import partial
import locale

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')


class PublicController(BaseController):
    START_WORKING_HOUR = 9
    END_WORKING_HOUR = 21
    SLOT_DURATION = 1

    async def menu(self, update):
        """Главное меню"""

        options = [
            MViewOption(title='Управление расписанием', link='/price'),
            MViewOption(title='Добавить расписание', link='/price'),
            MViewOption(title='Список моих записей', link='/price'),
            MViewOption(title='Профиль', link='/price'),
        ]

        return partial(
            self.ctx.driver.render_message,
            content=MViewItem(
                title="Навигация",
                text="Выберите действие",
                option=options
            )
        )

    async def public(self):
        """Публичное меню"""
        return partial(
            self.ctx.driver.render_message,
            content=MViewItem(
                title="Навигация",
                text="Выберите действие",
                option=[
                    MViewOption(title='Записаться на прием', link='/filter'),
                    MViewOption(title='Управление моими записями', link='/appointments'),
                    MViewOption(title='Информация о подписке', link='/payment'),
                    MViewOption(
                        title='Оферта',
                        link='https://real-website.com/offer',
                        action="open_url"
                    ),
                ]
            )
        )

    async def price(self):
        """Подтвержденное удаление слота - только представление"""

        return partial(
            self.show_message,
            title="Успешно!",
            text="Слот удален",
            options=[MViewOption(
                title='Назад', link='/')]
        )
        # except Exception as e:
        #     return await self.show_error(str(e))

    async def show_error(self, error_message: str):
        """Показать сообщение об ошибке"""
        return partial(
            self.show_message,
            title="Ошибка",
            text=error_message,
            options=[MViewOption(title="Назад", link="/")]
        )
