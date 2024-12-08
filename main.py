"""
Тут находится главная логика работы бота.
НИЧЕГО НЕ ТРОГАТЬ!!1!
"""

from __future__ import annotations

import asyncio
from loguru import logger
from PlayerokAPI.updater.runner import Runner
from tgbot.main import startup
from tgbot.core.loader import bot
from tgbot.core.config import TelegramBotSettings
from tgbot.keyboards.inline.user import InlineKeyboardFactory
from utils.logger import configure_logger
from utils.tools import create_storage

VERSION = "-pre-0.0.1"

async def runner_listener() -> None: #TODO: как-нить сделать круче
    """
    Простенький слушатель событий у раннера, обрабатывает новые сообщения и уведомляет зарегистрированных пользователей в тг.
    """
    async for event in Runner().listen():
        logger.info(f"Новое сообщение: {event.message.text}")

        try:
            keyboard = await InlineKeyboardFactory.new_message_keyboard(
                chat_id=event.chat_id, username=event.message.user.username
            )

            registered_users = await TelegramBotSettings().get_registered_users()
            if not registered_users:
                return

            for user in registered_users:
                if event.message.text:
                    await bot.send_message(
                        chat_id=user,
                        text=f"👤 <b>{event.message.user.username}</b>: <code>{event.message.text}</code>",
                        reply_markup=keyboard
                    )
                elif event.message.file:
                    await bot.send_photo(
                        chat_id=user,
                        photo=event.message.file.url,
                        caption=f"👤 <b>{event.message.user.username}</b>\n🔗 <a href='{event.message.file.url}'>Ссылка на изображение</a>",
                        reply_markup=keyboard
                    )
        except Exception as error:
            logger.error(f"Ошибка при отправке сообщения пользователю: {error}")

async def main() -> None:
    """
    Основной асинхронный цикл запуска бота и слушателя Runner.
    """
    await configure_logger()
    await create_storage()

    logger.info(f"PlayerokAPI v{VERSION}")

    telegram_bot_task = asyncio.create_task(startup())
    runner_task = asyncio.create_task(runner_listener())

    try:
        await asyncio.wait(
            {telegram_bot_task, runner_task},
            return_when=asyncio.FIRST_COMPLETED
        )

    except asyncio.CancelledError:
        logger.warning("Задачи были отменены.")
    except Exception as error:
        logger.error(f"Ошибка в основном цикле: {error}")
    finally:
        if not telegram_bot_task.done():
            telegram_bot_task.cancel()
        if not runner_task.done():
            runner_task.cancel()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Остановка приложения...")
    except Exception as error:
        logger.error(f"Критическая ошибка: {error}")
    finally:
        logger.info("PlayerokAPI остановлен.")