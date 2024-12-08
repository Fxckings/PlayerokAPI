from __future__ import annotations

from aiogram import Dispatcher
from aiogram.utils.callback_answer import CallbackAnswerMiddleware

async def register_middlewares(dp: Dispatcher) -> None:
    from .auth import IsBannedMiddleware, IsRegisteredMiddleware

    dp.message.middleware(IsBannedMiddleware())
    dp.message.middleware(IsRegisteredMiddleware())
    dp.callback_query.middleware(IsBannedMiddleware())
    dp.callback_query.middleware(CallbackAnswerMiddleware())