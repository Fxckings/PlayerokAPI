from __future__ import annotations

from PlayerokAPI.common.enums import MessageTypes, PatternsEnum

async def get_message_type(message: str) -> MessageTypes:
    """
    Возвращает тип сообщения.
    """
    for message_type, pattern in PatternsEnum.message_type_patterns.items():
        if pattern.search(message):
            return message_type

    return MessageTypes.NON_SYSTEM