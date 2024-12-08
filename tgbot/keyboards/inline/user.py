from __future__ import annotations
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

class InlineKeyboardFactory:
    @staticmethod
    async def registration_keyboard() -> InlineKeyboardMarkup:
        """
        Создает клавиатуру для регистрации с кнопкой ввода пароля.

        Returns:
            InlineKeyboardMarkup: Инлайн-клавиатура для регистрации.
        """
        builder = InlineKeyboardBuilder()
        builder.button(text="📫 Ввести пароль", callback_data="continue_with_password")
        builder.adjust(1)  # Один ряд кнопок
        return builder.as_markup()

    @staticmethod
    async def new_message_keyboard(chat_id: str, username: str) -> InlineKeyboardMarkup:
        """
        Создает клавиатуру для ответа в чате.

        Args:
            chat_id (str): Идентификатор чата.

        Returns:
            InlineKeyboardMarkup: Инлайн-клавиатура для отправки сообщения.
        """
        builder = InlineKeyboardBuilder()
        builder.button(text="📤 Ответ", callback_data=f"send_message_{chat_id}")
        builder.button(text=f"🌐 {username}", url=f"https://playerok.com/chats/{chat_id}")
        builder.adjust(2)  # Один ряд кнопок
        return builder.as_markup()