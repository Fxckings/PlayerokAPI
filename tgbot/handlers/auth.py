from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from tgbot.FSMC.auth import AuthState
from tgbot.handlers.auth_handler import AuthHandler
from tgbot.core.config import TelegramBotSettings

auth_router = Router(name="auth")
auth_handler = AuthHandler()

@auth_router.message(AuthState.password)
async def handle_password(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод пароля пользователя в состоянии AuthState.password.

    Передает обработку пароля в соответствующий AuthHandler.

    Args:
        message (Message): Входящее сообщение с паролем.
        state (FSMContext): Контекст состояния FSM.
    """
    await auth_handler.handle_password(message, state)

@auth_router.callback_query(F.data == "continue_with_password")
async def request_password(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Обрабатывает запрос на регистрацию с использованием пароля.

    Если пользователь уже зарегистрирован, отправляет уведомление.
    В противном случае запрашивает ввод пароля и переводит FSM в состояние AuthState.password.

    Args:
        callback_query (CallbackQuery): Входящий callback-запрос.
        state (FSMContext): Контекст состояния FSM.
    """
    is_registered = await TelegramBotSettings().is_user_registered(callback_query.from_user.id)
    
    if is_registered:
        await callback_query.message.answer("Вы уже зарегистрированы.")
        return

    await callback_query.message.answer("Введите пароль для регистрации:")
    await state.set_state(AuthState.password)
