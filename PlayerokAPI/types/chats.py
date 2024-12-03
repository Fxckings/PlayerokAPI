from __future__ import annotations

from PlayerokAPI.types.user import *
from PlayerokAPI.types.other import *
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List, TypeVar, Type
from PlayerokAPI.common.enums import MessageTypes
from utils.tools import get_message_type
import asyncio
from functools import cached_property
import json

T = TypeVar('T', bound='Message')

@dataclass
class Chats:
    """
    Класс, представляющий список чатов.
    
    Attributes:
        edges (List[ChatEdge]): Все чаты, которые есть.
        page_info (ChatsPageInfo): Информация о пагинации.
        total_count (int): Общее количество чатов.
    """

    edges: List[ChatEdge]
    page_info: ChatsPageInfo
    total_count: int

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'Chats':
        """
        Создает экземпляр Chats из словаря данных.
        
        Args:
            data (Dict[str, Any]): Словарь с данными чатов.
        
        Returns:
            Chats: Новый экземпляр Chats.
        """
        edges_data = data.get('edges', [])
        edges = [await ChatEdge.from_dict(edge) for edge in edges_data]

        page_info_data = data.get('pageInfo', {})
        page_info = await ChatsPageInfo.from_dict(page_info_data)

        return cls(
            edges=edges,
            page_info=page_info,
            total_count=data.get('total_count', 0)
        )

    @property
    def get_last_chat_id(self) -> str:
        return self.edges[-1].get_last_chat_id if self.edges else ''

@dataclass
class ChatEdge:
    """
    Класс, представляющий чет (edge) чата.
    
    Attributes:
        cursor (str): Курсор для пагинации.
        node (Chat): Определенный чат.
    """

    cursor: str
    node: Chat

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'ChatEdge':
        """Создает экземпляр ChatEdge из словаря."""
        node_data = data.get('node', {})
        node = await Chat.from_dict(node_data)
        return cls(
            cursor=data.get('cursor', ''),
            node=node
        )

    @property
    def get_last_chat_id(self) -> str:
        return self.node.id if self.node else ''

@dataclass
class Chat:
    """
    Класс, представляющий определенный чат.
    
    Attributes:
        id (str): Идентификатор чата.
        type (str): Тип чата (например, NOTIFICATIONS).
        unreadMessagesCounter (int): Количество непрочитанных сообщений.
        bookmarked (Optional[bool]): Закладка чата.
        last_message (Optional[ChatMessage]): Последнее сообщение в чате.
        isTextingAllowed (Optional[bool]): Разрешено ли отправлять текстовые сообщения.
        owner (Optional[UserFragment]): Создатель чата.
        agent (Optional[UserFragment]): Агент чата.
        participants (List[UserFragment]): Список участников чата.
        deals (List[ItemDealProfile]): Список сделок в чате.
        status (Optional[str]): Статус чата.
        startedAt (Optional[str]): Время начала чата.
        finishedAt (Optional[str]): Время окончания чата.
    """

    id: str
    type: str
    unreadMessagesCounter: int
    bookmarked: Optional[bool]
    last_message: Optional['ChatMessage']
    isTextingAllowed: Optional[bool]
    owner: Optional['UserFragment']
    agent: Optional['UserFragment']
    participants: List['UserFragment'] = field(default_factory=list)
    deals: List['ItemDealProfile'] = field(default_factory=list)
    status: Optional[str] = None
    startedAt: Optional[str] = None
    finishedAt: Optional[str] = None

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'Chat':
        """
        Создает экземпляр Chat из словаря данных.
        
        Args:
            data (Dict[str, Any]): Словарь с данными чата.
        
        Returns:
            Chat: Новый экземпляр Chat.
        """
        participants_data = data.get('participants', [])
        participants = [await UserFragment.from_dict(participant) for participant in participants_data] if participants_data else []

        owner_data = data.get('owner', {})
        owner = await UserFragment.from_dict(owner_data) if owner_data else None

        last_message_data = data.get('lastMessage')
        last_message = await ChatMessage.from_dict(last_message_data) if last_message_data else None

        deals_data = data.get('deals')
        deals = [await ItemDealProfile.from_dict(deal) for deal in deals_data] if isinstance(deals_data, list) else [await ItemDealProfile.from_dict(deals_data)] if deals_data else []

        return cls(
            id=data.get('id', ''),
            type=data.get('type', ''),
            unreadMessagesCounter=data.get('unreadMessagesCounter', -1),
            bookmarked=data.get('bookmarked'),
            last_message=last_message,
            isTextingAllowed=data.get('isTextingAllowed'),
            owner=owner,
            agent=data.get('agent', None),
            participants=participants,
            deals=deals,
            status=data.get('status'),
            startedAt=data.get('startedAt'),
            finishedAt=data.get('finishedAt')
        )
    
    @cached_property
    async def last_deal(self) -> 'ItemDealProfile':
        """
        Возвращает последнюю сделку в чате.
        
        Returns:
            ItemDealProfile: Последняя сделка в чате.
        """
        return self.deals[-1] if self.deals else None

@dataclass
class ChatsPageInfo:
    """
    Класс, представляющий метаданные о пагинации списка чатов.
    
    Attributes:
        startCursor (str): Курсор начала страницы.
        endCursor (str): Курсор конца страницы.
        hasPreviousPage (bool): Есть ли предыдущая страница.
        hasNextPage (bool): Есть ли следующая страница.
    """

    startCursor: str
    endCursor: str
    hasPreviousPage: bool
    hasNextPage: bool

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'ChatsPageInfo':
        """
        Создает экземпляр ChatsPageInfo из словаря данных.
        
        Args:
            data (Dict[str, Any]): Словарь с данными пагинации.
        
        Returns:
            ChatsPageInfo: Новый экземпляр ChatsPageInfo.
        """
        return cls(
            startCursor=data.get('startCursor', ''),
            endCursor=data.get('endCursor', ''),
            hasPreviousPage=data.get('hasPreviousPage', False),
            hasNextPage=data.get('hasNextPage', False)
        )

@dataclass
class ChatMessage:
    """
    Класс, представляющий определенное сообщение в чате.
    
    Attributes:
        id (str): Идентификатор сообщения.
        text (str): Текст сообщения.
        createdAt (str): Дата и время создания сообщения.
        isRead (bool): Был ли сообщение прочитано.
        isBulkMessaging (bool): Является ли это сообщением массового рассылки.
        event (Optional[str]): Тип события (если применимо).
        file (Optional[Dict[str, Any]]): Данные файла (если применимо).
        user (Optional[UserFragment]): Пользователь, отправивший сообщение.
        eventByUser (Optional[UserFragment]): Пользователь, организовавший событие (если применимо).
        eventToUser (Optional[UserFragment]): Получатель события (если применимо).
        deal (Optional[Dict[str, Any]]): Данные сделки (если применимо).
    """

    id: str
    text: str
    createdAt: str
    isRead: bool
    isBulkMessaging: bool
    event: Optional[str] = None
    file: Optional[Dict[str, Any]] = None
    user: Optional['UserFragment'] = None
    eventByUser: Optional['UserFragment'] = None
    eventToUser: Optional['UserFragment'] = None
    deal: Optional[Dict[str, Any]] = None

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """
        Создает экземпляр ChatMessage из словаря данных.
        
        Args:
            data (Dict[str, Any]): Словарь с данными сообщения.
        
        Returns:
            ChatMessage: Новый экземпляр ChatMessage.
        """
        user_data = data.get('user')
        user = await UserFragment.from_dict(user_data) if user_data else None

        event_by_user_data = data.get('eventByUser')
        event_by_user = await UserFragment.from_dict(event_by_user_data) if event_by_user_data else None

        event_to_user_data = data.get('eventToUser')
        event_to_user = await UserFragment.from_dict(event_to_user_data) if event_to_user_data else None

        return cls(
            id=data.get('id', ''),
            text=data.get('text', ''),
            createdAt=data.get('createdAt', ''),
            isRead=data.get('isRead', False),
            isBulkMessaging=data.get('isBulkMessaging', False),
            event=data.get('event'),
            file=data.get('file'),
            user=user,
            eventByUser=event_by_user,
            eventToUser=event_to_user,
            deal=data.get('deal'),
        )
    
@dataclass
class Message:
    """
    Класс, представляющий определенное сообщение.
    
    Attributes:
        id (str): Идентификатор сообщения.
        text (str): Текст сообщения.
        createdAt (str): Время создания сообщения.
        deletedAt (Optional[str]): Время удаления сообщения.
        isRead (bool): Прочитано ли сообщение.
        isSuspicious (bool): Подозрительное сообщение.
        isBulkMessaging (bool): Массовое сообщение.
        game (Optional[Any]): Игра.
        file (Optional[Any]): Файл.
        user (Optional[UserFragment]): Пользователь.
        deal (Optional[Any]): Сделка.
        item (Optional[Any]): Предмет.
        transaction (Optional[Any]): Транзакция.
        moderator (Optional[Any]): Модератор.
        eventByUser (Optional[Any]): Событие от пользователя.
        eventToUser (Optional[Any]): Событие для пользователя.
        isAutoResponse (bool): Автоматическое событие?
        event (Optional[Any]): Событие.
        buttons (Optional[Any]): Кнопки.
        type (MessageTypes): Тип сообщения.
    """

    id: str
    text: str
    createdAt: str
    deletedAt: Optional[str] = None
    isRead: bool = False
    isSuspicious: bool = False
    isBulkMessaging: bool = False
    game: Optional[Any] = None
    file: Optional[Any] = None
    user: Optional[UserFragment] = None
    deal: Optional[Any] = None
    item: Optional[Any] = None
    transaction: Optional[Any] = None
    moderator: Optional[Any] = None
    eventByUser: Optional[Any] = None
    eventToUser: Optional[Any] = None
    isAutoResponse: bool = False
    event: Optional[Any] = None
    buttons: Optional[Any] = None
    type: Optional[MessageTypes] = MessageTypes.NON_SYSTEM

    @classmethod
    async def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Создает экземпляр Message из словаря данных.
        
        Args:
            data (Dict[str, Any]): Словарь с данными сообщения.
        
        Returns:
            Message: Новый экземпляр Message.
        """
        user_data = data.get('user', {})
        user = await UserFragment.from_dict(user_data) if user_data else None

        message_type = await get_message_type(data.get('text', ''))
        return cls(
            id=data.get('id', ''),
            text=data.get('text', ''),
            createdAt=data.get('createdAt', ''),
            deletedAt=data.get('deletedAt'),
            isRead=data.get('isRead', False),
            isSuspicious=data.get('isSuspicious', False),
            isBulkMessaging=data.get('isBulkMessaging', False),
            game=data.get('game'),
            file=data.get('file'),
            user=user,
            deal=data.get('deal'),
            item=data.get('item'),
            transaction=data.get('transaction'),
            moderator=data.get('moderator'),
            eventByUser=data.get('eventByUser'),
            eventToUser=data.get('eventToUser'),
            isAutoResponse=data.get('isAutoResponse', False),
            event=data.get('event'),
            buttons=data.get('buttons'),
            type=MessageTypes(message_type),
        )

    @classmethod
    async def from_list(cls: Type[T], data: List[Dict[str, Any]]) -> List[T]:
        """
        Создает список сообщений из списка словарей данных.
        
        Args:
            data (List[Dict[str, Any]]): Список словарей с данными сообщений.
        
        Returns:
            List[Message]: Список новых экземпляров Message.
        """
        return await asyncio.gather(*[cls.from_dict(item['node']) for item in data])