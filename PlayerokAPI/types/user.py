from __future__ import annotations

from PlayerokAPI.types.user import *
from dataclasses import dataclass
from typing import Optional, Dict, Any, Union

@dataclass
class MyUserProfile:
    """
    Класс, содержащий основную информацию о пользователе, через viewer-запрос.
    __typename == "User"
    """
    id: str
    is_blocked: bool
    has_frozen_balance: bool
    username: str
    email: str
    role: str
    balance: Optional["UserBalance"] = None
    avatar_url: str = ''
    is_online: bool = False
    rating: int = 0
    testimonial_counter: int = 0
    created_at: str = ''
    support_chat_id: str = ''
    system_chat_id: str = ''
    stats: Optional["UserStats"] = None
    has_enabled_notifications: bool = False
    profile: Optional["UserFragment"] = None

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'MyUserProfile':
        """
        Создает экземпляр MyUserProfile из словаря данных.

        Args:
            data (Dict[str, Any]): Словарь с данными пользователя.

        Returns:
            MyUserProfile: Новый экземпляр MyUserProfile.
        """
        user_data = data.get('data', {}).get('viewer') or data.get('data', {}).get('user', {})
        profile_data = user_data.get('profile', {}) if user_data else {}
        stats_data = user_data.get('stats', {}) or {}
        items_data = stats_data.get('items', {}) or {}
        deals_data = stats_data.get('deals', {}) or {}
        incoming_data = deals_data.get('incoming', {}) or {}
        outgoing_data = deals_data.get('outgoing', {}) or {}
        balance_data = user_data.get('balance', {}) or {}

        return cls(
            id=user_data.get('id', ''),
            is_blocked=user_data.get('isBlocked', False),
            has_frozen_balance=user_data.get('hasFrozenBalance', False),
            username=user_data.get('username', ''),
            email=user_data.get('email', ''),
            role=user_data.get('role', ''),
            balance=UserBalance(
                id=balance_data.get('id', ''),
                value=balance_data.get('value', 0),
                frozen=balance_data.get('frozen', 0),
                available=balance_data.get('available', 0),
                withdrawable=balance_data.get('withdrawable', 0),
                pendingIncome=balance_data.get('pendingIncome', 0)
            ),
            avatar_url=profile_data.get('avatarURL', ''),
            is_online=profile_data.get('isOnline', False),
            rating=profile_data.get('rating', 0),
            testimonial_counter=profile_data.get('testimonialCounter', 0),
            created_at=profile_data.get('createdAt', ''),
            support_chat_id=profile_data.get('supportChatId', ''),
            system_chat_id=profile_data.get('systemChatId', ''),
            stats=UserStats(
                items=UserStatsItems(
                    total=items_data.get('total', 0),
                    finished=items_data.get('finished', 0)
                ),
                deals=UserDeals(
                    incoming=UserDealsIncoming(
                        total=incoming_data.get('total', 0),
                        finished=incoming_data.get('finished', 0)
                    ),
                    outgoing=UserDealsOutgoing(
                        total=outgoing_data.get('total', 0),
                        finished=outgoing_data.get('finished', 0)
                    )
                )
            ),
            has_enabled_notifications=user_data.get('hasEnabledNotifications', False),
            profile=UserFragment(
                id=profile_data.get('id', ''),
                username=profile_data.get('username', ''),
                role=profile_data.get('role', ''),
                avatarURL=profile_data.get('avatarURL', ''),
                isOnline=profile_data.get('isOnline', False),
                isBlocked=profile_data.get('isBlocked', False),
                rating=profile_data.get('rating', 0),
                testimonialCounter=profile_data.get('testimonialCounter', 0),
                createdAt=profile_data.get('createdAt', ''),
                supportChatId=profile_data.get('supportChatId', ''),
                systemChatId=profile_data.get('systemChatId', '')
            )
        )
    
@dataclass
class UserStatsItems:
    """
    Класс, содержащий статистику лотов пользователя.
    
    Attributes:
        total (Optional[int]): Сколько лотов было продано.
        finished (Optional[int]): Сколько лотов было полностью выполнено.
    """
    total: Optional[int] = 0
    finished: Optional[int] = 0

@dataclass
class UserDealsIncoming:
    """
    Класс, содержащий статистику входящих сделок пользователя.
    
    Attributes:
        total (Optional[Union[int, float]]): Сколько заказов были начаты.
        finished (Optional[Union[int, float]]: Сколько заказов были полностью выполнены.
    """
    total: Optional[Union[int, float]] = 0
    finished: Optional[Union[int, float]] = 0

@dataclass
class UserDealsOutgoing:
    """
    Класс, содержащий статистику исходящих сделок пользователя.
    
    Attributes:
        total (Optional[int]): Сколько заказов были начаты.
        finished (Optional[int]): Сколько заказов были полностью выполнены.
    """
    total: Optional[int] = 0
    finished: Optional[int] = 0

@dataclass
class UserDeals:
    """
    Класс, содержащий статистику сделок пользователя.
    
    Attributes:
        incoming (Optional[UserDealsIncoming]): Статистика входящих сделок.
        outgoing (Optional[UserDealsIncoming]): Статистика исходящих сделок.
    """
    incoming: Optional[UserDealsIncoming] = None
    outgoing: Optional[UserDealsIncoming] = None

@dataclass
class UserStats:
    """
    Класс, содержащий общую статистику пользователя.
    
    Attributes:
        items (Optional[UserStatsItems]): Статистика лотов пользователя.
        deals (Optional[UserDeals]): Статистика сделок пользователя.
    """
    items: Optional[UserStatsItems] = None
    deals: Optional[UserDeals] = None

@dataclass
class UserFragment:
    """
    Класс, содержащий профиль пользователя.
    
    Attributes:
        id (str): Айди пользователя.
        username (str): Имя пользователя.
        role (str): Роль пользователя (по умолчанию: USER).
        avatarURL (str): Ссылка на аватарку пользователя.
        isOnline (bool): Статус онлайн пользователя.
        isBlocked (bool): Заблокирован ли пользователь.
        rating (int): Рейтинг пользователя.
        testimonialCounter (int): Количество отзывов пользователя.
        createdAt (str): Дата регистрации пользователя.
        supportChatId (str): Айди чата поддержки пользователя.
        systemChatId (str): Айди системного чата пользователя.
    """

    id: str = ''
    username: str = ''
    role: str = 'USER'
    avatarURL: str = ''
    isOnline: bool = False
    isBlocked: bool = False
    rating: int = 0
    testimonialCounter: int = 0
    createdAt: str = ''
    supportChatId: str = ''
    systemChatId: str = ''

    @classmethod
    async def from_dict(cls, data: dict) -> 'UserFragment':
        """
        Создает экземпляр UserFragment из словаря данных.

        Args:
            data (dict): Словарь с данными пользователя.

        Returns:
            UserFragment: Новый экземпляр UserFragment.
        """
        return cls(
            id=data.get('id', ''),
            username=data.get('username', ''),
            role=data.get('role', 'USER'),
            avatarURL=data.get('avatarURL', ''),
            isOnline=data.get('isOnline', False),
            isBlocked=data.get('isBlocked', False),
            rating=data.get('rating', 0),
            testimonialCounter=data.get('testimonialCounter', 0),
            createdAt=data.get('createdAt', ''),
            supportChatId=data.get('supportChatId', ''),
            systemChatId=data.get('systemChatId', '')
        )

@dataclass
class UserBalance:
    """
    Класс, содержащий информацию о балансе пользователя.
    
    Attributes:
        id (str): Идентификатор баланса.
        value (Optional[float]): Общая сумма.
        frozen (Optional[float]): Замороженная сумма.
        available (Optional[float]): Всего доступно.
        withdrawable (Optional[float]): Всего можно вывести/потратить.
        pendingIncome (Optional[float]): Всего входящих доходов.
    """

    id: str
    value: Optional[float] = None
    frozen: Optional[float] = None
    available: Optional[float] = None
    withdrawable: Optional[float] = None
    pendingIncome: Optional[float] = None