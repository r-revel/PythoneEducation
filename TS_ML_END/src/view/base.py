from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class MViewOption:
    title: str
    link: str
    action: Optional[str] = None # 'web_app' | 'open_url'
@dataclass
class FormField:
    name: str
    field_type: str  # 'choice' | 'text'
    title: str
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None
    current_value: Optional[Any] = None
    message_id: Optional[int] = None


@dataclass
class MViewItem:
    title: str
    text: str
    image_url: Optional[str] = None  # URL изображения
    image_caption: Optional[str] = None  # Подпись к изображению=
    option: Optional[List[MViewOption]] = None
    message_id: Optional[int] = None
    current_form_step: Optional[int] = None  # Текущий шаг заполнения формы


@dataclass
class MViewListItem:
    items: List[str]


class AView(ABC):
    @abstractmethod
    async def init(self, callback=None):
        """Настройка"""
        pass

    @abstractmethod
    async def render_message(self, list: MViewListItem):
        """Возвращает список всех элементов. Должен быть реализован в дочерних классах."""
        pass