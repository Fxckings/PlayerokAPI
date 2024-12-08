from __future__ import annotations
import asyncio
from typing import AsyncGenerator, Optional, List, Set, Dict
from uuid import UUID
from loguru import logger
from PlayerokAPI.common.account import Account
from PlayerokAPI.updater.events import NewMessageEvent, MessageEventsStack
from PlayerokAPI.common.exceptions import RunnerError

class Runner:
    """
    Класс для получения новых чатов с непрочитанными сообщениями.
    """
    def __init__(self) -> None:
        self.account = Account()
        self.read_chats: bool = self.account.settings.read_chats
        self.processed_message_ids: Dict[str, Set[UUID]] = {}
        self.readed_chats: List[str] = []

    async def listen(
        self,
        requests_delay: Optional[float | int] = 4,
        ignore_errors: bool = True
    ) -> AsyncGenerator[NewMessageEvent, None]:
        """
        Асинхронно отправляет запросы для получения новых событий в чатах.

        Args:
            requests_delay (Optional[float | int]): Задержка между запросами (в секундах).
            ignore_errors (bool): Игнорировать ошибки или выбрасывать их.

        Yields:
            AsyncGenerator[NewMessageEvent, None]: События новых сообщений.
        """
        while True:
            try:
                unread_chats = await self.account.get_unreaded_chats()

                if not unread_chats:
                    await asyncio.sleep(requests_delay)
                    continue

                logger.info(f"Получены новые чаты: {unread_chats}")

                events_stack = MessageEventsStack()

                for chat_id in unread_chats:
                    chat = await self.account.get_chat(chat_id)
                    unread_messages_count = chat.unreadMessagesCounter

                    if not unread_messages_count:
                        continue

                    messages = await self.account.get_chat_messages(chat_id, count=unread_messages_count)

                    for message in messages:
                        event = NewMessageEvent(chat_id, message)
                        events_stack.add_event(event)

                        yield event

                await self.account.mark_chat_as_read(unread_chats)

            except Exception as error:
                if not ignore_errors:
                    raise RunnerError(error) from error
                logger.error(f"Произошла ошибка при получении новых чатов: {error}")

            logger.info(f"Задержка {requests_delay} секунд перед следующим запросом.")
            await asyncio.sleep(requests_delay)