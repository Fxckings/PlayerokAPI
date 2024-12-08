from __future__ import annotations

from PlayerokAPI.common.enums import MessageTypes, PatternsEnum
import os
import ctypes
from loguru import logger
import aiofiles.os
from pathlib import Path

async def get_message_type(message: str) -> MessageTypes:
    """
    Возвращает тип сообщения.
    """
    for message_type, pattern in PatternsEnum.message_type_patterns.items():
        if pattern.search(message):
            return message_type

    return MessageTypes.NON_SYSTEM

async def set_console_title(title: str) -> None:
    """
    Изменяет название консоли для Windows.
    """
    try:
        if os.name == 'nt':
            ctypes.windll.kernel32.SetConsoleTitleW(title)
    except OSError as e:
        logger.warning(f"Произошла ошибка при изменении названия консоли: {e}")

async def delete_file(file_path: str) -> None:
    """
    Удаляет файл.
    """
    try:
        os.remove(file_path)
    except OSError as e:
        logger.warning(f"Произошла ошибка при удалении файла: {e}")

async def create_storage() -> None:
    """
    Создает директории.
    """
    await create_storage_telegram()
    await create_storage_images()

async def create_storage_telegram() -> None:
    """
    Создает директории для хранения данных (телеграм).
    """
    if not Path("storage/telegram").is_dir():
        await aiofiles.os.makedirs("storage/telegram", exist_ok=True)
        async with aiofiles.open("storage/telegram/users.json", "w") as f:
            await f.write("{}")
        async with aiofiles.open("storage/telegram/banned.json", "w") as f:
            await f.write("{}")

async def create_storage_images() -> None:
    """
    Создает директории для хранения изображений.
    """
    if not Path("images").is_dir():
        await aiofiles.os.makedirs("images", exist_ok=True)
