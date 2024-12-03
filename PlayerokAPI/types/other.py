from __future__ import annotations

import random
import string
from faker import Faker
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from PlayerokAPI.types.user import *

class RequestsModel:
    @staticmethod
    def generate_random_string(length: int = 10) -> str:
        """
        Генерирует случайную строку заданной длины.

        Args:
            length (int): Длина строки. Значение по умолчанию равно 10.

        Returns:
            str: Случайная строка заданной длины.
        """
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for _ in range(length))

    @staticmethod
    def generate_random_uuid() -> str:
        """
        Генерирует случайный UUID.

        Returns:
            str: Случайный UUID.
        """
        return f"{RequestsModel.generate_random_string(8)}-{RequestsModel.generate_random_string(4)}-{RequestsModel.generate_random_string(4)}-{RequestsModel.generate_random_string(4)}-{RequestsModel.generate_random_string(12)}"

    @staticmethod
    def generate_random_trace_id() -> str:
        """
        Генерирует случайный trace_id для заголовка Sentry-Trace.

        Returns:
            str: Случайный trace_id.
        """
        return f"{RequestsModel.generate_random_uuid()}-{RequestsModel.generate_random_uuid()}-0"

    @staticmethod
    def generate_random_baggage() -> str:
        """
        Генерирует случайный baggage для заголовка Baggage.

        Returns:
            str: Случайный baggage.
        """
        fake = Faker()
        return (
            f"sentry-environment=production,"
            f"sentry-release={fake.sha1()[:12]},"
            f"sentry-public_key={fake.sha1()},"
            f"sentry-trace_id={RequestsModel.generate_random_uuid()},"
            f"sentry-sample_rate=0.01,"
            f"sentry-transaction=%2Fprofile%2F%5Busername%5D%2Fproducts,"
            f"sentry-sampled=false"
        )

    @staticmethod
    def get_default_headers() -> Dict[str, str]:
        """
        Возвращает дефолтные заголовки для запросов, которые позволяют обойти клаудфлейр.

        Returns:
            Dict: Дефолтные заголовки.
        """
        headers = {
            "User-Agent": Faker().user_agent(),
            "Accept": "*/*",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/json",
            "Apollo-Require-Preflight": "true",
            "Access-Control-Allow-Headers": "sentry-trace, baggage",
            "Apollographql-Client-Name": "web",
            "X-Timezone-Offset": "-240",
            "Sentry-Trace": RequestsModel.generate_random_trace_id(),
            "Baggage": RequestsModel.generate_random_baggage(),
            "Origin": "https://playerok.com",
            "DNT": "1",
            "Sec-GPC": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        return headers
    
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
        """
        Создает экземпляр GameCategory из словаря данных.
        
        Args:
            data (Dict[str, Any]): Словарь с данными категории.
        
        Returns:
            GameCategory: Новый экземпляр GameCategory.
        """
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
class File:
    """
    Класс, представляющий файл.
    
    Attributes:
        id (Optional[str]): Идентификатор файла.
        url (Optional[str]): URL файла.
    """

    id: Optional[str] = None
    url: Optional[str] = None

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'File':
        """
        Создает экземпляр File из словаря данных.
        
        Args:
            data (Dict[str, Any]): Словарь с данными файла.
        
        Returns:
            File: Новый экземпляр File.
        """
        return cls(
            id=data.get('id'),
            url=data.get('url'),
        )

@dataclass
class FileGame:
    """
    Класс, представляющий файл игры.
    
    Attributes:
        id (str): Идентификатор файла.
        url (str): URL файла.
    """

    id: str
    url: str

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'FileGame':
        """
        Создает экземпляр FileGame из словаря данных.
        
        Args:
            data (Dict[str, Any]): Словарь с данными файла игры.
        
        Returns:
            FileGame: Новый экземпляр FileGame.
        """
        return cls(
            id=data.get('id'),
            url=data.get('url'),
        )
    
@dataclass
class GameProfile:
    """
    Класс, представляющий профиль игры.
    
    Attributes:
        id (str): Идентификатор профиля.
        name (str): Название профиля.
        type (str): Тип профиля.
        slug (str): Слаг профиля.
        logo (FileGame): Логотип профиля.
    """

    id: str
    name: str
    type: str
    slug: str
    logo: FileGame

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'GameProfile':
        """
        Создает экземпляр GameProfile из словаря данных.
        
        Args:
            data (Dict[str, Any]): Словарь с данными профиля игры.
        
        Returns:
            GameProfile: Новый экземпляр GameProfile.
        """
        logo_data = data.get('logo', {})
        logo = FileGame.from_dict(logo_data) if logo_data else None

        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            type=data.get('type', ''),
            slug=data.get('slug', ''),
            logo=logo,
        )

@dataclass
class TransactionPropsFragment:
    """
    Класс, представляющий фрагмент свойств транзакции.
    
    Attributes:
        paymentURL (Optional[str]): URL для оплаты.
    """

    paymentURL: Optional[str] = None

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'TransactionPropsFragment':
        """
        Создает экземпляр TransactionPropsFragment из словаря данных.
        
        Args:
            data (Dict[str, Any]): Словарь с данными фрагмента свойств транзакции.
        
        Returns:
            TransactionPropsFragment: Новый экземпляр TransactionPropsFragment.
        """
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
        """
        Создает экземпляр Transaction из словаря данных.
        
        Args:
            data (Dict[str, Any]): Словарь с данными транзакции.
        
        Returns:
            Transaction: Новый экземпляр Transaction.
        """
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
        game (GameProfile): Профиль игры.
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
    game: Optional[GameProfile] = None
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
        """
        Создает экземпляр LotDetails из словаря данных.
        
        Args:
            data (Dict[str, Any]): Словарь с данными лота.
        
        Returns:
            LotDetails: Новый экземпляр LotDetails.
        """
        user = await UserFragment.from_dict(data.get('user', {})) if data.get('user') else None
        buyer = await UserFragment.from_dict(data.get('buyer', {})) if data.get('buyer') else None
        attachments = [await File.from_dict(attachment) for attachment in data.get('attachments', [])]
        category = await GameCategory.from_dict(data.get('category', {})) if data.get('category') else None
        game = await GameProfile.from_dict(data.get('game', {})) if data.get('game') else None
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
            game=game,
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
        """
        Создает экземпляр ItemProfileList из словаря данных.
        
        Args:
            data (Dict[str, Any]): Словарь с данными списка профилей лотов.
        
        Returns:
            ItemProfileList: Новый экземпляр ItemProfileList.
        """
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
        """
        Создает экземпляр ItemDealProfile из словаря данных.
        
        Args:
            data (Dict[str, Any]): Словарь с данными сделки.
        
        Returns:
            ItemDealProfile: Новый экземпляр ItemDealProfile.
        """
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
