from dataclasses import dataclass, field
from typing import List
from view.telegram import TelegramClient


@dataclass
class TimeSlot:
    text: str
    id: str


@dataclass
class AppContext:
    driver: TelegramClient
