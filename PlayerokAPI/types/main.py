from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, TypeVar, Union, Type
import json
from functools import cached_property
from utils.tools import get_message_type
from PlayerokAPI.common.enums import MessageTypes
import asyncio
from loguru import logger

T = TypeVar('T', bound='Message')
    
@dataclass
class GameCategory:
    """
    Класс, представляющий определенную категорию игр.
    
    Attributes:
        id (str): Идентификатор категории.
        slug (str): Слаг категории.
        name (str): Название категории.
        categoryId (str): ID родительской категории.
        gameId (str): ID связанной игры.
        obtaining (Optional[str]): Способ получения.
        options (List[str]): Варианты.
        props (Optional[str]): Свойства.
        noCommentFromBuyer (bool): Запрещено оставлять комментарии от покупателя.
        instructionForBuyer (Optional[str]): Инструкция для покупателя.
        instructionForSeller (Optional[str]): Инструкция для продавца.
        useCustomObtaining (bool): Использовать пользовательский способ получения.
        autoConfirmPeriod (str): Период автоматического подтверждения.
        autoModerationMode (bool): Режим автоматической модерации.
    """
    id: str
    slug: str
    name: str
    categoryId: str
    gameId: str
    obtaining: Optional[str] = None
    options: List[str] = field(default_factory=list)
    props: Optional[str] = None
    noCommentFromBuyer: bool = False
    instructionForBuyer: Optional[str] = None
    instructionForSeller: Optional[str] = None
    useCustomObtaining: bool = False
    autoConfirmPeriod: str = ''
    autoModerationMode: bool = False

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'GameCategory':
        return cls(
            id=data.get('id', ''),
            slug=data.get('slug', ''),
            name=data.get('name', ''),
            categoryId=data.get('categoryId', ''),
            gameId=data.get('gameId', ''),
            obtaining=data.get('obtaining'),
            options=data.get('options', []),
            props=data.get('props'),
            noCommentFromBuyer=data.get('noCommentFromBuyer', False),
            instructionForBuyer=data.get('instructionForBuyer'),
            instructionForSeller=data.get('instructionForSeller'),
            useCustomObtaining=data.get('useCustomObtaining', False),
            autoConfirmPeriod=data.get('autoConfirmPeriod', ''),
            autoModerationMode=data.get('autoModerationMode', False),
        )

@dataclass
class TransactionPropsFragment:
    paymentURL: Optional[str] = None

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'TransactionPropsFragment':
        return cls(
            paymentURL=data.get('paymentURL'),
        )

@dataclass
class Transaction:
    """
    Класс, представляющий определенную транзакцию.
    
    Attributes:
        id (str): Идентификатор транзакции.
        operation (str): Операция.
        direction (str): Направление.
        providerId (str): ID провайдера.
        status (str): Статус.
        statusDescription (Optional[str]): Описание статуса.
        statusExpirationDate (Optional[str]): Дата истечения статуса.
        value (int): Значение.
        props (Optional[TransactionPropsFragment]): Свойства транзакции.
    """

    id: str
    operation: str
    direction: str
    providerId: str
    status: str
    statusDescription: Optional[str] = None
    statusExpirationDate: Optional[str] = None
    value: int = 0
    props: Optional[TransactionPropsFragment] = None

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        props_data = data.get('props', {})
        props = TransactionPropsFragment.from_dict(props_data) if props_data else None

        return cls(
            id=data.get('id', ''),
            operation=data.get('operation', ''),
            direction=data.get('direction', ''),
            providerId=data.get('providerId', ''),
            status=data.get('status', ''),
            statusDescription=data.get('statusDescription'),
            statusExpirationDate=data.get('statusExpirationDate'),
            value=data.get('value', 0),
            props=props,
        )
    
@dataclass
class ItemProfileList:
    """
    Класс, представляющий список профилей лотов на аккаунте.
    
    Attributes:
        items (List[LotDetails]): Список лотов.
        pageInfo (Dict[str, Any]): Информация о странице.
        totalCount (int): Всего лотов на аккаунте.
    """

    items: List[LotDetails] = field(default_factory=list)
    """Список лотов."""
    pageInfo: Dict[str, Any] = field(default_factory=dict)
    """Информация о странице."""
    totalCount: int = 0
    """Всего лотов на аккаунте."""

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'ItemProfileList':
        items_data = data.get('items', {}).get('edges', [])
        items = [await LotDetails.from_dict(item['node']) for item in items_data] if items_data else []

        pageInfo_data = data.get('pageInfo', {})
        pageInfo = {
            'startCursor': pageInfo_data.get('startCursor'),
            'endCursor': pageInfo_data.get('endCursor'),
            'hasPreviousPage': pageInfo_data.get('hasPreviousPage', False),
            'hasNextPage': pageInfo_data.get('hasNextPage', False),
            '__typename': pageInfo_data.get('__typename', 'ItemProfilePageInfo')
        }

        totalCount = data.get('totalCount', 0)

        return cls(
            items=items,
            pageInfo=pageInfo,
            totalCount=totalCount
        )

@dataclass
class LinkStatsSummary:
    """
    Класс, представляющий сводную статистику ссылки.
    
    Attributes:
        clickCounter (int): Счетчик кликов.
        clientCounter (int): Счетчик клиентов.
        registrationCounter (int): Счетчик регистраций.
        paymentCounter (int): Счетчик платежей.
        paymentSum (float): Сумма платежей.
        firstPaymentCounter (int): Счетчик первых платежей.
        firstPaymentSum (float): Сумма первых платежей.
        sellerCounter (int): Счетчик продавцов.
        id (Dict[str, str]): Идентификатор в формате словаря.
        __typename (str): Тип объекта.
    """

    clickCounter: int = 0
    clientCounter: int = 0
    registrationCounter: int = 0
    paymentCounter: int = 0
    paymentSum: float = 0.0
    firstPaymentCounter: int = 0
    firstPaymentSum: float = 0.0
    sellerCounter: int = 0
    id: Dict[str, str] = field(default_factory=dict)

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'LinkStatsSummary':
        id_data = json.loads(data.get('id', '{}'))
        
        return cls(
            clickCounter=data.get('clickCounter', 0),
            clientCounter=data.get('clientCounter', 0),
            registrationCounter=data.get('registrationCounter', 0),
            paymentCounter=data.get('paymentCounter', 0),
            paymentSum=float(data.get('paymentSum', 0)),
            firstPaymentCounter=data.get('firstPaymentCounter', 0),
            firstPaymentSum=float(data.get('firstPaymentSum', 0)),
            sellerCounter=data.get('sellerCounter', 0),
            id=id_data,
        )

@dataclass
class UserDeals:
    incoming: Optional[UserStatsItems] = None
    outgoing: Optional[UserStatsItems] = None

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
                    incoming=UserStatsItems(
                        total=incoming_data.get('total', 0),
                        finished=incoming_data.get('finished', 0)
                    ),
                    outgoing=UserStatsItems(
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
    total: Optional[int] = 0
    finished: Optional[int] = 0

@dataclass
class UserStats:
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

@dataclass
class File:
    id: Optional[str] = None
    url: Optional[str] = None

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'File':
        return cls(
            id=data.get('id'),
            url=data.get('url'),
        )

@dataclass
class LotDetails:
    """
    Класс, представляющий детали лота.
    
    Attributes:
        id (str): Идентификатор лота.
        slug (str): Айдишник лота.
        name (str): Название лота.
        description (str): Описание лота.
        rawPrice (int): Необработанная цена.
        price (int): Цена лота.
        attributes (Dict[str, Any]): Атрибуты лота.
        status (str): Статус лота.
        priorityPosition (int): Позиция приоритета.
        sellerType (str): Тип продавца.
        user (Optional[UserFragment]): Пользователь.
        buyer (Optional[UserFragment]): Покупатель.
        attachments (List[File]): Прикрепленные файлы.
        category (GameCategory): Категория.
        game (dict): Профиль игры.
        comment (Optional[str]): Секретные данные.
        dataFields (Optional[Dict[str, Any]]): Дополнительные поля данных.
        obtainingType (Optional[str]): Тип получения.
        priority (str): Приоритет.
        sequence (int): Последовательность.
        priorityPrice (int): Цена приоритета.
        statusExpirationDate (str): Дата истечения статуса.
        viewsCounter (int): Счетчик просмотров.
        statusDescription (Optional[str]): Описание статуса.
        editable (bool): Изменяемый ли?
        statusPayment (Transaction): Транзакция оплаты.
        moderator (Optional[UserFragment]): Модератор.
        approvalDate (str): Дата одобрения.
        deletedAt (Optional[str]): Дата удаления.
        createdAt (str): Дата создания.
        updatedAt (str): Дата обновления.
        mayBePublished (bool): Может ли быть опубликован?
    """
    id: str = ''
    slug: str = ''
    name: str = ''
    description: str = ''
    rawPrice: int = 0
    price: int = 0
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: str = ''
    priorityPosition: int = 0
    sellerType: str = ''
    user: Optional[UserFragment] = None
    buyer: Optional[UserFragment] = None
    attachments: List[File] = field(default_factory=list)
    category: Optional[GameCategory] = None
    game: Optional[Dict] = None
    comment: Optional[str] = None
    dataFields: Dict[str, Any] = field(default_factory=dict)
    obtainingType: Optional[str] = None
    priority: str = ''
    sequence: int = 0
    priorityPrice: int = 0
    statusExpirationDate: str = ''
    viewsCounter: int = 0
    statusDescription: Optional[str] = None
    editable: bool = False
    statusPayment: Optional[Transaction] = None
    moderator: Optional[UserFragment] = None
    approvalDate: str = ''
    deletedAt: Optional[str] = None
    createdAt: str = ''
    updatedAt: str = ''
    mayBePublished: bool = False

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'LotDetails':
        user = await UserFragment.from_dict(data.get('user', {})) if data.get('user') else None
        buyer = await UserFragment.from_dict(data.get('buyer', {})) if data.get('buyer') else None
        attachments = [await File.from_dict(attachment) for attachment in data.get('attachments', [])]
        category = await GameCategory.from_dict(data.get('category', {})) if data.get('category') else None
        status_payment = await Transaction.from_dict(data.get('statusPayment', {})) if data.get('statusPayment') else None
        moderator = await UserFragment.from_dict(data.get('moderator', {})) if data.get('moderator') else None

        return cls(
            id=data.get('id', ''),
            slug=data.get('slug', ''),
            name=data.get('name', ''),
            description=data.get('description', ''),
            rawPrice=data.get('rawPrice', 0),
            price=data.get('price', 0),
            attributes=data.get('attributes', {}),
            status=data.get('status', ''),
            priorityPosition=data.get('priorityPosition', 0),
            sellerType=data.get('sellerType', ''),
            user=user,
            buyer=buyer,
            attachments=attachments,
            category=category,
            game = data.get('game'),
            comment=data.get('comment'),
            dataFields=data.get('dataFields', {}),
            obtainingType=data.get('obtainingType'),
            priority=data.get('priority', ''),
            sequence=data.get('sequence', 0),
            priorityPrice=data.get('priorityPrice', 0),
            statusExpirationDate=data.get('statusExpirationDate', ''),
            viewsCounter=data.get('viewsCounter', 0),
            statusDescription=data.get('statusDescription'),
            editable=data.get('editable', False),
            statusPayment=status_payment,
            moderator=moderator,
            approvalDate=data.get('approvalDate', ''),
            deletedAt=data.get('deletedAt'),
            createdAt=data.get('createdAt', ''),
            updatedAt=data.get('updatedAt', ''),
            mayBePublished=data.get('mayBePublished', False)
        )

@dataclass
class ItemDealProfile:
    """
    Класс, представляющий сделку в определенном чате.
    
    Attributes:
        id (str): Идентификатор сделки.
        direction (str): Направление сделки.
        status (str): Статус сделки.
        hasProblem (bool): Есть проблема.
        statusDescription (Optional[str]): Описание статуса.
        testimonial (Optional[str]): ТестимонIAL.
        item (Optional[LotDetails]): Лот.
        user (Optional[UserFragment]): Пользователь.
    """
    id: str
    direction: str
    status: str
    hasProblem: bool
    statusDescription: Optional[str] = None
    testimonial: Optional[str] = None
    item: Optional[LotDetails] = None
    user: Optional[UserFragment] = None

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'ItemDealProfile':
        return cls(
            id=data.get('id', ''),
            direction=data.get('direction', ''),
            status=data.get('status', ''),
            hasProblem=data.get('hasProblem', False),
            statusDescription=data.get('statusDescription'),
            testimonial=data.get('testimonial'),
            item=await LotDetails.from_dict(data.get('item', {})) if data.get('item') else None,
            user=await UserFragment.from_dict(data.get('user', {})) if data.get('user') else None
        )

@dataclass
class CreateDeal:
    """
    Класс, представляющий созданную сделку.
    
    Attributes:
        id (str): Идентификатор сделки.
        operation (str): Операция.
        direction (str): Направление.
        providerId (str): ID провайдера.
        provider (TransactionProvider): Провайдер.
        user (UserFragment): Пользователь.
        creator (Optional[Any]): Создатель (может быть null).
        status (str): Статус.
        statusDescription (Optional[str]): Описание статуса.
        statusExpirationDate (Optional[str]): Дата истечения статуса.
        value (int): Значение.
        fee (int): Комиссия.
        createdAt (str): Время создания.
        props (TransactionPropsFragment): Свойства сделки.
        verifiedAt (Optional[str]): Время верификации.
        verifiedBy (Optional[Any]): Кто верифицировал.
        completedBy (Optional[Any]): Кто завершил.
        paymentMethodId (Optional[str]): ID метода оплаты.
        completedAt (str): Время завершения.
        isSuspicious (Optional[bool]): Подозрительность.
    """
    id: Optional[str] = ''
    operation: Optional[str] = ''
    direction: Optional[str] = ''
    providerId: Optional[str] = ''
    provider: Optional[TransactionProvider] = None
    user: Optional[UserFragment] = None
    creator: Optional[Any] = None
    status: Optional[str] = ''
    statusDescription: Optional[str] = None
    statusExpirationDate: Optional[str] = None
    value: Optional[int] = 0
    fee: Optional[int] = 0
    createdAt: Optional[str] = ''
    props: Optional[TransactionPropsFragment] = None
    verifiedAt: Optional[str] = None
    verifiedBy: Optional[Any] = None
    completedBy: Optional[Any] = None
    paymentMethodId: Optional[str] = None
    completedAt: Optional[str] = ''
    isSuspicious: Optional[bool] = None

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'CreateDeal':
        return cls(
            id=data.get('id', ''),
            operation=data.get('operation', ''),
            direction=data.get('direction', ''),
            providerId=data.get('providerId', ''),
            provider=TransactionProvider.from_dict(data.get('provider', {})),
            user=UserFragment.from_dict(data.get('user', {})),
            creator=data.get('creator'),
            status=data.get('status', ''),
            statusDescription=data.get('statusDescription'),
            statusExpirationDate=data.get('statusExpirationDate'),
            value=data.get('value', 0),
            fee=data.get('fee', 0),
            createdAt=data.get('createdAt', ''),
            props=TransactionPropsFragment.from_dict(data.get('props', {})),
            verifiedAt=data.get('verifiedAt'),
            verifiedBy=data.get('verifiedBy'),
            completedBy=data.get('completedBy'),
            paymentMethodId=data.get('paymentMethodId'),
            completedAt=data.get('completedAt', ''),
            isSuspicious=data.get('isSuspicious')
        )

@dataclass
class TransactionPropsFragment:
    creatorId: Optional[str]
    dealId: str
    paidFromPendingIncome: Optional[Any]
    paymentURL: Optional[str]
    successURL: Optional[str]
    paymentAccount: Optional[Any]
    paymentGateway: Optional[Any]
    alreadySpent: Optional[Any]
    exchangeRate: Optional[float]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransactionPropsFragment':
        return cls(
            creatorId=data.get('creatorId'),
            dealId=data.get('dealId', ''),
            paidFromPendingIncome=data.get('paidFromPendingIncome'),
            paymentURL=data.get('paymentURL'),
            successURL=data.get('successURL'),
            paymentAccount=data.get('paymentAccount'),
            paymentGateway=data.get('paymentGateway'),
            alreadySpent=data.get('alreadySpent'),
            exchangeRate=float(data.get('exchangeRate', 0)) if data.get('exchangeRate') else None
        )

@dataclass
class TransactionProvider:
    id: str
    name: str
    fee: float
    account: Optional[Any]
    props: Any
    limits: ProviderLimits
    paymentMethods: list

@dataclass
class ProviderLimits:
    incoming: ProviderLimitRange
    outgoing: ProviderLimitRange

@dataclass
class ProviderLimitRange:
    min: int
    max: int

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
        self.edges = self.edges[::-1]
        return self.edges[-1].get_last_chat_id if self.edges else ''

@dataclass
class ChatsPageInfo:
    startCursor: str
    endCursor: str
    hasPreviousPage: bool
    hasNextPage: bool

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'ChatsPageInfo':
        return cls(
            startCursor=data.get('startCursor', ''),
            endCursor=data.get('endCursor', ''),
            hasPreviousPage=data.get('hasPreviousPage', False),
            hasNextPage=data.get('hasNextPage', False)
        )

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
        return self.deals[-1] if self.deals else None

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
    text: Optional[str] = None
    createdAt: Optional[str] = None
    isRead: Optional[bool] = None
    isBulkMessaging: Optional[bool] = None
    event: Optional[str] = None
    file: Optional[Dict[str, Any]] = None
    user: Optional['UserFragment'] = None
    eventByUser: Optional['UserFragment'] = None
    eventToUser: Optional['UserFragment'] = None
    deal: Optional[Dict[str, Any]] = None

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
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
    text: str = None
    createdAt: str = None
    deletedAt: str = None
    isRead: bool = False
    isSuspicious: bool = False
    isBulkMessaging: bool = False
    game: Optional[Any] = None
    file: Optional[File] = None
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
        user_data = data.get('user', {})
        user = await UserFragment.from_dict(user_data) if user_data else None
        message_type = await get_message_type(data.get('text', '')) if data.get('text') else MessageTypes.IMAGE
        file = await File.from_dict(data.get('file', {})) if data.get('file') else None

        return cls(
            id=data.get('id', ''),
            text=data.get('text', ''),
            createdAt=data.get('createdAt', ''),
            deletedAt=data.get('deletedAt'),
            isRead=data.get('isRead', False),
            isSuspicious=data.get('isSuspicious', False),
            isBulkMessaging=data.get('isBulkMessaging', False),
            game=data.get('game'),
            file=file,
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
        return await asyncio.gather(*[cls.from_dict(item['node']) for item in data])

@dataclass
class MessageTemplate:
    id: str
    type: str
    title: str
    text: str
    sequence: int
    created_at: str
    group: Optional[str] = None

@dataclass
class ReportMessageTemplates:
    """
    После подтверждения получения доступ к товару был утрачен. - 1edb94f4-c0ba-6560-9fcf-1b87aa5d5fca
    Продавец обманным путем принудил вас подтвердить получение товара до того, как товар был получен. - 1edb94f5-a5f8-6dc0-49d1-d752dcd3df16
    После подтверждения получения доступ к товару был заблокирован. - 1ee5c06b-a41f-6cf0-4efb-4edf20a0b8fd
    Продавец пытается получить доступ к вашей игровой учетной записи или нарушить его целостность после выполнения заказа. - 1ee5c05e-cf7a-6ab0-1eff-dae8982b935f
    Продавец пытается получить доступ к вашему профилю на сайте или к вашей учетной записи, которая привязана к Playerok. - 1edb94f5-ecab-6010-5e01-b6faba51923e
    Продавец использует оскорбления и ведет себя недружелюбно без видимых на то причин. - 1edb94f6-556b-6690-1be3-5afffb413f5d
    Вы заподозрили неправомерные действия со стороны продавца или не нашли нужную причину для того, чтобы сообщить о проблеме. - 1edb94f8-56d9-6660-e5ea-413593681bd7
    """
    message_templates: List[MessageTemplate] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> 'ReportMessageTemplates':
        templates = []
        for edge in data['edges']:
            node = edge['node']
            template = MessageTemplate(
                id=node['id'],
                type=node['type'],
                title=node['title'],
                text=node['text'],
                sequence=node['sequence'],
                created_at=node['createdAt'],
                group=node['group']
            )
            templates.append(template)
        
        return cls(message_templates=templates)

    def get_template_by_type(self, template_type: str) -> Optional[MessageTemplate]:
        for template in self.message_templates:
            if template.type == template_type:
                return template
        return None

    def get_all_titles(self) -> List[str]:
        return [template.title for template in self.message_templates]

    def count_templates(self) -> int:
        return len(self.message_templates)