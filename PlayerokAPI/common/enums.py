from __future__ import annotations

from enum import Enum
import re

class MessageTypes(Enum): #TODO
    """
    Класс, представляющий типы сообщений в чате.
    """

    SYSTEM = 0
    """Системное сообщение."""
    
    NON_SYSTEM = 1
    """Обычное сообщение."""

    DEAL_HAS_PROBLEM = 2
    """
    Покупатель сообщил о проблеме
    Решите проблему с покупателем
    """

    DEAL_PROBLEM_RESOLVED = 3
    """
    🔰 Поддержка решила проблему
    """

    DEAL_CONFIRMED = 4
    """
    Покупатель подтвердил получение
    Оплата зачислена на ваш баланс и доступна к выплате
    """

    ITEM_SENT = 5
    """
    Вы выполнили заказ
    Ожидайте подтверждение получения от покупателя
    """

    DEAL_ROLLED_BACK = 6
    """
    🔰 Поддержка сделала возврат средств
    Средства возвращены покупателю на баланс
    """

    DEAL_CONFIRMED_AUTOMATICALLY = 7
    """
    Получение подтверждено автоматически
    Оплата зачислена на ваш баланс и доступна к выплате
    """

    ITEM_PAID = 8
    """
    {{ITEM_PAID}}
    Покупатель оплатил покупку
    Вы получите оплату после того, как передадите товар
    """

class PatternsEnum:
    """
    Класс, представляющий шаблоны сообщений.
    """
    message_type_patterns = {
        MessageTypes.DEAL_HAS_PROBLEM: re.compile(r'{{DEAL_HAS_PROBLEM}}', re.DOTALL),
        MessageTypes.DEAL_PROBLEM_RESOLVED: re.compile(r'{{DEAL_PROBLEM_RESOLVED}}', re.DOTALL),
        MessageTypes.DEAL_CONFIRMED: re.compile(r'{{DEAL_CONFIRMED}}', re.DOTALL),
        MessageTypes.ITEM_SENT: re.compile(r'{{ITEM_SENT}}', re.DOTALL),
        MessageTypes.DEAL_ROLLED_BACK: re.compile(r'{{DEAL_ROLLED_BACK}}', re.DOTALL),
        MessageTypes.DEAL_CONFIRMED_AUTOMATICALLY: re.compile(r'{{DEAL_CONFIRMED_AUTOMATICALLY}}', re.DOTALL),
        MessageTypes.ITEM_PAID: re.compile(r'{{ITEM_PAID}}', re.DOTALL),
    }
