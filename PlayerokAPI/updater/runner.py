from __future__ import annotations

from PlayerokAPI.common.account import Account
from PlayerokAPI.updater.events import *
from typing import Optional, List, AsyncGenerator
from loguru import logger
import asyncio

class Runner:
    """
    Класс получения новых чатов, в которых есть новое сообщение.
    """
    def __init__(self) -> None:
        self.account = Account()

    async def listen(
        self,
        requests_delay: float = 4.0,
        ignore_errors: bool = False
    ) -> AsyncGenerator[BaseEvent, None, None]:
        """
        Асинхронно отправляет запросы для получения новых событий.

        :param requests_delay: задержка между запросами (в секундах).
        :type requests_delay: :obj:`float`, опционально

        :param ignore_errors: игнорировать ошибки?
        :type ignore_errors: :obj:`bool`, опционально

        :yield: генератор событий.
        :rtype: :obj:`Generator` of :class:`BaseEvent`
        """
        while True:
            try:
                unread_chats = await self.account.get_unreaded_chats()
                if not unread_chats:
                    continue
                
                logger.info(f"Получены новые чаты: {unread_chats}")
                
                events_stack = MessageEventsStack()
                
                for chat_id in unread_chats:
                    chat = await self.account.get_chat(chat_id)
                    unread_messages = chat.unreadMessagesCounter

                    if not unread_messages:
                        continue

                    messages = await self.account.get_chat_messages(chat_id, count=unread_messages)

                    for message in messages:
                        event = NewMessageEvent(chat_id, message)
                        events_stack.add_event(event)

                        yield event
                
                await self.account.mark_chat_as_read(unread_chats)
            
            except Exception as e:
                if not ignore_errors:
                    raise e
                else:
                    logger.error(f"Произошла ошибка при получении новых чатов: {e}")
                    logger.debug("TRACEBACK", exc_info=True)
            
            await asyncio.sleep(requests_delay)