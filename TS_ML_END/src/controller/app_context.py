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
    time_slots: List[TimeSlot] = field(default_factory=list)

    def _init_time_slots(self) -> List[TimeSlot]:
        return [
            TimeSlot(text=f"{hour:02d}:00", id=f"{hour:02d}-00")
            for hour in range(9, 21)
        ]

    def get_time_slot_by_id(self, slot_id: str) -> TimeSlot:
        for slot in self.time_slots:
            if slot.id == slot_id:
                return slot
        raise ValueError(f"Time slot with id {slot_id} not found")
