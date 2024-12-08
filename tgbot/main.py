from __future__ import annotations

from tgbot.core.loader import  bot, dp
from tgbot.handlers import get_handlers_router
from tgbot.middlewares import register_middlewares

async def on_startup() -> None:
    await register_middlewares(dp)
    dp.include_router(get_handlers_router())
    await bot.delete_webhook(drop_pending_updates=True)

async def on_shutdown() -> None:
    await dp.storage.close()
    await dp.fsm.storage.close()
    await bot.delete_webhook()
    await bot.session.close()

async def startup() -> None:
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), polling_timeout=10)