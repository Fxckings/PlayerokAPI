from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from tgbot.FSMC.chat import SendMessageFSM
from PlayerokAPI.common.account import Account
from tgbot.core.loader import bot
from loguru import logger
from typing import Dict, Any
from utils.tools import delete_file

chat_router = Router(name="chat")

@chat_router.callback_query(F.data.startswith("send_message_"))
async def process_send_message(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик callback-запроса для отправки сообщения.

    Запрашивает текст сообщения у пользователя и сохраняет данные состояния.
    
    Args:
        callback_query (CallbackQuery): Входящий callback-запрос.
        state (FSMContext): Контекст состояния FSM.
    """
    response_message = await callback_query.message.answer("Введите текст сообщения:")

    await state.update_data(
        playerok_chat_id=callback_query.data.split("_")[2],
        message_id=response_message.message_id,
        chat_id=callback_query.from_user.id,
    )

    await state.set_state(SendMessageFSM.message)

@chat_router.message(SendMessageFSM.message)
async def send_message(message: Message, state: FSMContext) -> None:
    """
    Обработчик текстового сообщения/фото для отправки.

    Удаляет исходное сообщение, отправляет текст через и очищает состояние.
    
    Args:
        message (Message): Входящее сообщение.
        state (FSMContext): Контекст состояния FSM.
    Returns:
        None: Нет возвращаемого значения.
    """
    content_type = message.content_type
    data: Dict[str, Any] = await state.get_data()

    if content_type not in ["text", "photo"]:
        await message.answer("❌ Только текстовое сообщение или фото.")
        return

    await bot.delete_message(data["chat_id"], data["message_id"])

    try:
        if content_type == "photo":
            await message.bot.download(file=message.photo[-1].file_id, destination="images/image.jpg")
            await Account().send_image(data["playerok_chat_id"], file_name="image.jpg", local_path="images/")
            await message.bot.send_photo(chat_id=data["chat_id"], photo=message.photo[-1].file_id, caption=f"<i><b>🤖 Ты:</b></i> <i>*Изображение*</i>")
            await delete_file("images/image.jpg")
        else:
            message_text: str = message.text
            await Account().send_message(data["playerok_chat_id"], message_text)
            await message.answer(f"<i><b>🤖 Ты:</b></i> <code>{message_text}</code>")
        
        logger.info(f"Отправлено сообщение: {message.text if content_type == 'text' else '*изображение*'} в чат {data['playerok_chat_id']}")

    except Exception as error:
        error_message = "<b>❌ Ошибка при отправке сообщения:</b>" if content_type == "text" else "<b>❌ Ошибка при отправке изображения:</b>"
        await message.answer(f"{error_message}\n<code>{message.text if content_type == 'text' else ''}</code>")
        logger.error(f"Ошибка при отправке сообщения / изображения: {error}")
    finally:
        await state.clear()
