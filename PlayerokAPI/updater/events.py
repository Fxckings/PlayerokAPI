from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from PlayerokAPI.types.main import Message

class NewMessageEvent:
    """
    Класс, представляющий событие нового сообщения.
    """
    def __init__(self, chat_id: str, message: Message) -> None:
        self.chat_id = chat_id
        self.message = message

    def to_dict(self) -> dict:
        message_content = None
        if self.message.text:
            message_content = self.message.text
        elif self.message.file and self.message.file.url:
            message_content = self.message.file.url
        else:
            logger.warning(f"Сообщение не содержит текста или файла: {self.message}")

        return {
            "chat_id": self.chat_id,
            "message": message_content,
        }

class MessageEventsStack:
    """
    Класс, представляющий стек событий сообщений.
    """
    def __init__(self) -> None:
        self._stack: List[NewMessageEvent] = []

    def add_event(self, event: NewMessageEvent) -> None:
        """
        Добавляет новое событие в стек.

        Args:
            event (NewMessageEvent): Событие для добавления.
        """
        self._stack.append(event)

    def pop_event(self) -> Optional[NewMessageEvent]:
        """
        Извлекает и удаляет первое событие из стека.

        Returns:
            Optional[NewMessageEvent]: Извлеченное событие или None, если стек пуст.
        """
        return self._stack.pop(0) if self._stack else None

    def get_stack(self) -> List[dict]:
        """
        Возвращает текущее состояние стека в виде списка словарей.

        Returns:
            List[dict]: Список событий в виде словарей.
        """
        return [event.to_dict() for event in self._stack]