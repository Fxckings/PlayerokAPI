from __future__ import annotations
from typing import Dict
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger
from tgbot.core.config import TelegramBotSettings
from config import SETTINGS
from tgbot.keyboards.inline.user import InlineKeyboardFactory

class AuthHandler:
    """
    Класс для обработки логики регистрации пользователя и управления попытками ввода пароля.
    """
    def __init__(self) -> None:
        self.failed_attempts: Dict[str, int] = {}

    async def request_password(self, message: Message) -> None:
        """
        Отправляет запрос на ввод пароля пользователю.

        Args:
            message (Message): Сообщение от пользователя.
        """
        logger.info(f"Запрос пароля у пользователя {message.from_user.id}")
        keyboard = await InlineKeyboardFactory.registration_keyboard()
        await message.answer(
            "Вы не зарегистрированы. Введите пароль для регистрации:",
            reply_markup=keyboard,
        )

    async def handle_password(self, message: Message, state: FSMContext) -> None:
        """
        Обрабатывает ввод пароля пользователем.

        Если пароль верный, пользователь регистрируется.
        Если пароль неверный, отслеживаются попытки. После 3 неверных попыток пользователь блокируется.

        Args:
            message (Message): Сообщение с паролем от пользователя.
            state (FSMContext): Контекст состояния FSM.
        """
        user_id = str(message.from_user.id)
        username = message.from_user.username
        password = message.text.strip()
        settings = TelegramBotSettings()

        self.failed_attempts[user_id] = self.failed_attempts.get(user_id, 0) + 1

        logger.info(f"Пользователь {user_id} вводит пароль: {password}")
        if password == SETTINGS.telegram_password:
            await settings.add_registered_user(user_id, username)
            await message.answer("Вы успешно зарегистрированы!")
            await state.clear()
            self.failed_attempts.pop(user_id, None)
            logger.info(f"Пользователь {user_id} зарегистрировался.")
        else:
            remaining_attempts = 3 - self.failed_attempts[user_id]
            if remaining_attempts <= 0:
                await settings.add_banned_user(user_id)
                await message.answer("Вы ввели неверный пароль 3 раза. Вы заблокированы.")
                logger.info(f"Пользователь {user_id} заблокирован после 3 неверных попыток.")
                await state.clear()
            else:
                await message.answer(
                    f"Неверный пароль. У вас осталось {remaining_attempts} попытки(-а)."
                )
                logger.info(f"Пользователь {user_id} ввел неверный пароль. Осталось {remaining_attempts} попытки(-а).")