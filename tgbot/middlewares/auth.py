from __future__ import annotations

from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import Message
from loguru import logger
from tgbot.core.config import TelegramBotSettings
from tgbot.handlers.auth_handler import AuthHandler
from tgbot.FSMC.auth import AuthState

class IsBannedMiddleware(BaseMiddleware):
    """
    Middleware для проверки, забанен ли пользователь.
    """
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        
        if await TelegramBotSettings().is_banned(str(event.from_user.id)):
            logger.info(f"Пользователь {event.from_user.id} заблокирован, но пытается что-то сделать.")
            return
        else:
            return await handler(event, data)

class IsRegisteredMiddleware(BaseMiddleware):
    """
    Middleware для проверки регистрации пользователя.
    Если пользователь не зарегистрирован, перенаправляем на регистрацию.
    """
    def __init__(self):
        self.auth_handler = AuthHandler()

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user_id = str(event.from_user.id)
        state = data['state']

        current_state = await state.get_state()
        if current_state == AuthState.password:
            return await handler(event, data)

        if not await TelegramBotSettings().is_user_registered(user_id):
            logger.info(f"Пользователь {user_id} не зарегистрирован, но зашел в бота.")
            await self.auth_handler.request_password(event)
        else:
            return await handler(event, data)