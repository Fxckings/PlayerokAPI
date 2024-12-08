from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import Message

start_router = Router(name="start")

@start_router.message(Command(commands=["start"]))
async def not_registered(message: Message) -> None:
    await message.answer("ЕЙйоуу!.")