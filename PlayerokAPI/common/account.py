from __future__ import annotations
from io import BytesIO

from PlayerokAPI.types.main import *
from PlayerokAPI.types.requests import RequestsModel
from PlayerokAPI.common.exceptions import *

from config import SETTINGS
from typing import Optional, Union
import curl_cffi.requests
from curl_cffi import CurlMime
from loguru import logger
import hashlib
from urllib.parse import urlencode

class Account:
    def __init__(self) -> None:
        self.settings = SETTINGS
        self.cookies = {"token": self.settings.token}

        self.session = curl_cffi.requests.AsyncSession()
        """Ассинхронная сессия для запросов."""
        self.syncsession = curl_cffi.requests.Session()
        """Синхронная сессия для инициализации аккаунта."""

        self.user_id: Optional[str] = None
        self.token: Optional[str] = self.settings.token
        self.username: Optional[str] = None

        self.is_initialized = False
        self.headers = RequestsModel().generate_headers()
        self.impersonate = RequestsModel().generate_impersonate()

        if not self.is_initialized:
            self.initialize()

    async def _make_request(
            self, 
            func: Any, 
            url: str, 
            payload=None,
            max_retries=3,
            sleep: Optional[int | float] = 2.5,
            **kwargs) -> Optional[str]:
        """
        Выполняет запрос к плеерку с повторными попытками.

        :param url: URL запроса
        :param payload: Параметры запроса
        :param max_retries: Максимальное количество попыток
        :param sleep: Задержка между попытками
        :param kwargs: Дополнительные параметры запроса
        :return: Ответ сервера
        """
        response_json = None
        for attempt in range(1, max_retries + 1):
            response = await func(url, payload, **kwargs)
            
            if response.status_code != 200:
                logger.warning(f"Попытка {attempt}/{max_retries}: Ошибка {response.status_code}: {response.text}")
                if attempt == max_retries:
                    raise StatusCodeError(response.status_code)
                
            try:
                response_json = response.json()

            except json.JSONDecodeError:
                if "Access denied" in response.text or response.status_code == 403:
                    self.headers = RequestsModel().generate_headers()
                    self.impersonate = RequestsModel().generate_impersonate()
                    raise CloudflareError
                    
                logger.warning(f"Попытка {attempt}/{max_retries}: Ошибка NotJsonResponseError: {response.text}")
                if attempt == max_retries:
                    raise NotJsonResponseError
                
                await asyncio.sleep(sleep)
                
            if response_json is not None:
                return response_json
        
        raise MaxRetryError(max_retries)

    async def post(
        self, 
        url: str = "https://playerok.com/graphql", 
        payload: Optional[Dict[str, Any]] = None, 
        headers: Optional[Dict[str, Any]] = None, 
        **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Выполняет POST-запрос к плеерку с повторными попытками.

        :param url: str: URL запроса
        :param payload: Optional[Dict[str, Any]]: Параметры запроса
        :param headers: Optional[Dict[str, Any]]: Заголовки запроса
        :param kwargs: Дополнительные параметры запроса
        :return: Optional[Dict[str, Any]]: Ответ сервера в виде JSON
        """

        return await self._make_request(
            self.session.post,
            url=url,
            json=payload,
            impersonate=self.impersonate,
            headers=headers if headers else self.headers,
            cookies=self.cookies,
            **kwargs
        )

    async def get(self, url: str, **kwargs: Any) -> Optional[str]:
        """
        Выполняет GET-запрос к плеерку с повторными попытками.

        :param url: str: URL запроса
        :param kwargs: Дополнительные параметры запроса
        :return: Optional[str]: Ответ сервера
        """

        return await self._make_request(
            self.session.get,
            url=url,
            impersonate=self.impersonate,
            cookies=self.cookies,
            headers=self.headers,
            **kwargs
        )

    def initialize(self) -> bool:
        """
        Инициализация аккаунта: получает айди и токен.

        :return: bool - True если аккаунт успешно инициализирован, False - если неудачно
        """
        try:
            if self.is_initialized:
                return True

            data: Dict[str, Any] = self._initialize_viwer()
            viewer: Dict[str, Any] = data.get('data', {}).get('viewer', {})

            if viewer:
                self.user_id: str = viewer.get('id')
                self.username: str = viewer.get('username')
                self.is_initialized: bool = True
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Ошибка инициализации аккаунта: {e}")
            return False
        
    def _initialize_viwer(self) -> Dict[str, Any]:
        """
        Выполняет вивер-запрос к плеерку для получения информации о текущем пользователе, чей токен указан.

        :return: dict: {'data': {'viewer': {id: str, username: str, ...}}
        """
        payload = {
            "operationName": "viewer",
            "variables": {},
            "query": "query viewer {\n  viewer {\n    ...Viewer\n    __typename\n  }\n}\n\nfragment Viewer on User {\n  id\n  username\n  email\n  role\n  hasFrozenBalance\n  supportChatId\n  systemChatId\n  unreadChatsCounter\n  isBlocked\n  isBlockedFor\n  createdAt\n  profile {\n    id\n    avatarURL\n    __typename\n  }\n  __typename\n}"
        }

        response = self.syncsession.post(
            url="https://playerok.com/graphql",
            json=payload,
            impersonate="chrome116",
            cookies=self.cookies,
            headers=self.headers
        )
        return response.json()

    async def get_userdata(self, username: str = None, get_me: bool = False) -> MyUserProfile:
        """
        Выполняет запрос к плеерку для получения информации о пользователе по его username.
        Может получать данные не только со своего аккаунта. НО со своего больше данных.

        :param username: username пользователя
        :param get_me: True - получить данные о себе, False - получить данные о другом пользователе

        :return: class: MyUserProfile
        """
        if get_me:
            username = await self.getme()
            username = username.username
    
        query = "query user($id: UUID, $username: String) {\n  user(id: $id, username: $username) {\n    ...RegularUserProfile\n    __typename\n  }\n}\n\nfragment RegularUserProfile on UserProfile {\n  ...RegularUser\n  ...RegularUserFragment\n  __typename\n}\n\nfragment RegularUser on User {\n  id\n  isBlocked\n  isVerified\n  isBlockedFor\n  hasFrozenBalance\n  username\n  email\n  role\n  balance {\n    ...RegularUserBalance\n    __typename\n  }\n  profile {\n    ...RegularUserFragment\n    __typename\n  }\n  stats {\n    ...RegularUserStats\n    __typename\n  }\n  hasEnabledNotifications\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment RegularUserBalance on UserBalance {\n  id\n  value\n  frozen\n  available\n  withdrawable\n  pendingIncome\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment RegularUserStats on UserStats {\n  id\n  items {\n    ...RegularUserItemsStats\n    __typename\n  }\n  deals {\n    ...RegularUserDealsStats\n    __typename\n  }\n  __typename\n}\n\nfragment RegularUserItemsStats on UserItemsStats {\n  total\n  finished\n  __typename\n}\n\nfragment RegularUserDealsStats on UserDealsStats {\n  incoming {\n    total\n    finished\n    __typename\n  }\n  outgoing {\n    total\n    finished\n    __typename\n  }\n  __typename\n}"
        
        hash_object = hashlib.sha256(query.encode())
        sha256_hash = hash_object.hexdigest()

        payload = {
            "operationName": "user",
            "variables": json.dumps({"username": username}),
            "extensions": json.dumps({
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": sha256_hash
                }
            })
        }

        url = f"https://playerok.com/graphql?{urlencode(payload)}"
        response = await self.get(url=url)
        return await MyUserProfile.from_dict(response['data']['user'])

    async def getme(self) -> MyUserProfile:
        """
        Выполняет вивер-запрос к плеерку для получения информации о текущем пользователе, чей токен указан.

        :return: class: MyUserProfile
        """
        payload = {
            "operationName": "viewer",
            "variables": {},
            "query": "query viewer {\n  viewer {\n    ...Viewer\n    __typename\n  }\n}\n\nfragment Viewer on User {\n  id\n  username\n  email\n  role\n  hasFrozenBalance\n  supportChatId\n  systemChatId\n  unreadChatsCounter\n  isBlocked\n  isBlockedFor\n  createdAt\n  profile {\n    id\n    avatarURL\n    __typename\n  }\n  __typename\n}"
        }

        response = await self.post(payload=payload, initialize=True)
        return await MyUserProfile.from_dict(response)
        
    async def get_chats(self, count: Union[int, str] = 10) -> Chats:
        """
        Получает список чатов со страницы https://playerok.com/chats.
        
        :param count: Количество чатов, которое нужно получить.
        :return: class: Chats
        """
        payload = {
            "operationName": "chats",
            "variables": {
                "pagination": {
                    "first": count
                },
                "filter": {
                    "userId": self.user_id
                }
            },
            "query": "query chats($pagination: Pagination, $filter: ChatFilter) {\n  chats(pagination: $pagination, filter: $filter) {\n    edges {\n      ...ChatEdgeFields\n      __typename\n    }\n    pageInfo {\n      startCursor\n      endCursor\n      hasPreviousPage\n      hasNextPage\n      __typename\n    }\n    totalCount\n    __typename\n  }\n}\n\nfragment ChatEdgeFields on ChatEdge {\n  cursor\n  node {\n    ...ChatEdgeNode\n    __typename\n  }\n  __typename\n}\n\nfragment ChatEdgeNode on Chat {\n  id\n  type\n  status\n  unreadMessagesCounter\n  bookmarked\n  lastMessage {\n    ...LastChatMessageFields\n    __typename\n  }\n  participants {\n    ...ChatParticipant\n    __typename\n  }\n  __typename\n}\n\nfragment LastChatMessageFields on ChatMessage {\n  id\n  text\n  createdAt\n  isRead\n  isBulkMessaging\n  event\n  file {\n    ...RegularFile\n    __typename\n  }\n  user {\n    ...ChatMessageUserFields\n    __typename\n  }\n  eventByUser {\n    ...ChatMessageUserFields\n    __typename\n  }\n  eventToUser {\n    ...ChatMessageUserFields\n    __typename\n  }\n  deal {\n    ...ChatMessageItemDeal\n    __typename\n  }\n  __typename\n}\n\nfragment RegularFile on File {\n  id\n  url\n  filename\n  mime\n  __typename\n}\n\nfragment ChatMessageUserFields on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment UserEdgeNode on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment ChatMessageItemDeal on ItemDeal {\n  id\n  direction\n  status\n  statusDescription\n  hasProblem\n  user {\n    ...ChatParticipant\n    __typename\n  }\n  testimonial {\n    ...ChatMessageDealTestimonial\n    __typename\n  }\n  item {\n    id\n    name\n    price\n    slug\n    rawPrice\n    sellerType\n    user {\n      ...ChatParticipant\n      __typename\n    }\n    category {\n      id\n      __typename\n    }\n    attachments {\n      ...PartialFile\n      __typename\n    }\n    comment\n    dataFields {\n      ...GameCategoryDataFieldWithValue\n      __typename\n    }\n    obtainingType {\n      ...GameCategoryObtainingType\n      __typename\n    }\n    __typename\n  }\n  obtainingFields {\n    ...GameCategoryDataFieldWithValue\n    __typename\n  }\n  chat {\n    id\n    type\n    __typename\n  }\n  transaction {\n    id\n    statusExpirationDate\n    __typename\n  }\n  statusExpirationDate\n  commentFromBuyer\n  __typename\n}\n\nfragment ChatParticipant on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment ChatMessageDealTestimonial on Testimonial {\n  id\n  status\n  text\n  rating\n  createdAt\n  updatedAt\n  creator {\n    ...RegularUserFragment\n    __typename\n  }\n  moderator {\n    ...RegularUserFragment\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PartialFile on File {\n  id\n  url\n  __typename\n}\n\nfragment GameCategoryDataFieldWithValue on GameCategoryDataFieldWithValue {\n  id\n  label\n  type\n  inputType\n  copyable\n  hidden\n  required\n  value\n  __typename\n}\n\nfragment GameCategoryObtainingType on GameCategoryObtainingType {\n  id\n  name\n  description\n  gameCategoryId\n  noCommentFromBuyer\n  instructionForBuyer\n  instructionForSeller\n  sequence\n  __typename\n}"
        }
        
        response = await self.post(payload=payload)
        return await Chats.from_dict(response.get('data', {}).get('chats', {}))

    async def get_chat(self, chat_id: Union[int, str]) -> Optional[Chat]:
        """
        Получает информацию о чате.
        
        :param chat_id: ID чата.
        :type chat_id: Union[int, str]
        :return: class: Chat
        :rtype: Chat
        """
        query = "query chat($id: UUID!) {\n  chat(id: $id) {\n    ...RegularChat\n    __typename\n  }\n}\n\nfragment RegularChat on Chat {\n  id\n  type\n  unreadMessagesCounter\n  bookmarked\n  isTextingAllowed\n  owner {\n    ...ChatParticipant\n    __typename\n  }\n  agent {\n    ...ChatParticipant\n    __typename\n  }\n  participants {\n    ...ChatParticipant\n    __typename\n  }\n  deals {\n    ...ChatActiveItemDeal\n    __typename\n  }\n  status\n  startedAt\n  finishedAt\n  __typename\n}\n\nfragment ChatParticipant on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment ChatActiveItemDeal on ItemDealProfile {\n  id\n  direction\n  status\n  hasProblem\n  statusDescription\n  testimonial {\n    id\n    rating\n    __typename\n  }\n  item {\n    ...ItemEdgeNode\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  __typename\n}\n\nfragment ItemEdgeNode on ItemProfile {\n  ...MyItemEdgeNode\n  ...ForeignItemEdgeNode\n  __typename\n}\n\nfragment MyItemEdgeNode on MyItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  statusExpirationDate\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  createdAt\n  priorityPosition\n  __typename\n}\n\nfragment PartialFile on File {\n  id\n  url\n  __typename\n}\n\nfragment UserItemEdgeNode on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment UserEdgeNode on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment ForeignItemEdgeNode on ForeignItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  priorityPosition\n  createdAt\n  __typename\n}"
        
        sha_object = hashlib.sha256(query.encode())
        sha256_hash = sha_object.hexdigest()

        payload = {
            "operationName": "chat",
            "variables": json.dumps({
                "id": chat_id
            }),
            "extensions": json.dumps({
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": sha256_hash
                }
            })
        }

        response = await self.get(url=f"https://playerok.com/graphql?{urlencode(payload)}")
        return await Chat.from_dict(response['data']['chat'])
    
    async def send_message(self, chat_id: Union[int, str], message: str) -> Message:
        """
        Отправялет сообщение в чат.
        
        :param chat_id: ID чата.
        :param message: Текст сообщения.
        :return: class: `Message`
        """
        payload = {
            "operationName": "createChatMessage",
            "variables": {
                "input": {
                    "chatId": chat_id,
                    "text": message
                    }
            },
            "query": "mutation createChatMessage($input: CreateChatMessageInput!, $file: Upload) {\n  createChatMessage(input: $input, file: $file) {\n    ...RegularChatMessage\n    __typename\n  }\n}\n\nfragment RegularChatMessage on ChatMessage {\n  id\n  text\n  createdAt\n  deletedAt\n  isRead\n  isSuspicious\n  isBulkMessaging\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  file {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...ChatMessageUserFields\n    __typename\n  }\n  deal {\n    ...ChatMessageItemDeal\n    __typename\n  }\n  item {\n    ...ItemEdgeNode\n    __typename\n  }\n  transaction {\n    ...RegularTransaction\n    __typename\n  }\n  moderator {\n    ...UserEdgeNode\n    __typename\n  }\n  eventByUser {\n    ...ChatMessageUserFields\n    __typename\n  }\n  eventToUser {\n    ...ChatMessageUserFields\n    __typename\n  }\n  isAutoResponse\n  event\n  buttons {\n    ...ChatMessageButton\n    __typename\n  }\n  __typename\n}\n\nfragment RegularGameProfile on GameProfile {\n  id\n  name\n  type\n  slug\n  logo {\n    ...PartialFile\n    __typename\n  }\n  __typename\n}\n\nfragment PartialFile on File {\n  id\n  url\n  __typename\n}\n\nfragment ChatMessageUserFields on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment UserEdgeNode on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment ChatMessageItemDeal on ItemDeal {\n  id\n  direction\n  status\n  statusDescription\n  hasProblem\n  user {\n    ...ChatParticipant\n    __typename\n  }\n  testimonial {\n    ...ChatMessageDealTestimonial\n    __typename\n  }\n  item {\n    id\n    name\n    price\n    slug\n    rawPrice\n    sellerType\n    user {\n      ...ChatParticipant\n      __typename\n    }\n    category {\n      id\n      __typename\n    }\n    attachments {\n      ...PartialFile\n      __typename\n    }\n    comment\n    dataFields {\n      ...GameCategoryDataFieldWithValue\n      __typename\n    }\n    obtainingType {\n      ...GameCategoryObtainingType\n      __typename\n    }\n    __typename\n  }\n  obtainingFields {\n    ...GameCategoryDataFieldWithValue\n    __typename\n  }\n  chat {\n    id\n    type\n    __typename\n  }\n  transaction {\n    id\n    statusExpirationDate\n    __typename\n  }\n  statusExpirationDate\n  commentFromBuyer\n  __typename\n}\n\nfragment ChatParticipant on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment ChatMessageDealTestimonial on Testimonial {\n  id\n  status\n  text\n  rating\n  createdAt\n  updatedAt\n  creator {\n    ...RegularUserFragment\n    __typename\n  }\n  moderator {\n    ...RegularUserFragment\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  __typename\n}\n\nfragment GameCategoryDataFieldWithValue on GameCategoryDataFieldWithValue {\n  id\n  label\n  type\n  inputType\n  copyable\n  hidden\n  required\n  value\n  __typename\n}\n\nfragment GameCategoryObtainingType on GameCategoryObtainingType {\n  id\n  name\n  description\n  gameCategoryId\n  noCommentFromBuyer\n  instructionForBuyer\n  instructionForSeller\n  sequence\n  __typename\n}\n\nfragment ItemEdgeNode on ItemProfile {\n  ...MyItemEdgeNode\n  ...ForeignItemEdgeNode\n  __typename\n}\n\nfragment MyItemEdgeNode on MyItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  statusExpirationDate\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  createdAt\n  priorityPosition\n  __typename\n}\n\nfragment UserItemEdgeNode on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment ForeignItemEdgeNode on ForeignItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  priorityPosition\n  createdAt\n  __typename\n}\n\nfragment RegularTransaction on Transaction {\n  id\n  operation\n  direction\n  providerId\n  provider {\n    ...RegularTransactionProvider\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  creator {\n    ...RegularUserFragment\n    __typename\n  }\n  status\n  statusDescription\n  statusExpirationDate\n  value\n  fee\n  createdAt\n  props {\n    ...RegularTransactionProps\n    __typename\n  }\n  verifiedAt\n  verifiedBy {\n    ...UserEdgeNode\n    __typename\n  }\n  completedBy {\n    ...UserEdgeNode\n    __typename\n  }\n  paymentMethodId\n  completedAt\n  isSuspicious\n  __typename\n}\n\nfragment RegularTransactionProvider on TransactionProvider {\n  id\n  name\n  fee\n  account {\n    ...RegularTransactionProviderAccount\n    __typename\n  }\n  props {\n    ...TransactionProviderPropsFragment\n    __typename\n  }\n  limits {\n    ...ProviderLimits\n    __typename\n  }\n  paymentMethods {\n    ...TransactionPaymentMethod\n    __typename\n  }\n  __typename\n}\n\nfragment RegularTransactionProviderAccount on TransactionProviderAccount {\n  id\n  value\n  userId\n  __typename\n}\n\nfragment TransactionProviderPropsFragment on TransactionProviderPropsFragment {\n  requiredUserData {\n    ...TransactionProviderRequiredUserData\n    __typename\n  }\n  tooltip\n  __typename\n}\n\nfragment TransactionProviderRequiredUserData on TransactionProviderRequiredUserData {\n  email\n  phoneNumber\n  __typename\n}\n\nfragment ProviderLimits on ProviderLimits {\n  incoming {\n    ...ProviderLimitRange\n    __typename\n  }\n  outgoing {\n    ...ProviderLimitRange\n    __typename\n  }\n  __typename\n}\n\nfragment ProviderLimitRange on ProviderLimitRange {\n  min\n  max\n  __typename\n}\n\nfragment TransactionPaymentMethod on TransactionPaymentMethod {\n  id\n  name\n  fee\n  providerId\n  account {\n    ...RegularTransactionProviderAccount\n    __typename\n  }\n  props {\n    ...TransactionProviderPropsFragment\n    __typename\n  }\n  limits {\n    ...ProviderLimits\n    __typename\n  }\n  __typename\n}\n\nfragment RegularTransactionProps on TransactionPropsFragment {\n  creatorId\n  dealId\n  paidFromPendingIncome\n  paymentURL\n  successURL\n  paymentAccount {\n    id\n    value\n    __typename\n  }\n  paymentGateway\n  alreadySpent\n  exchangeRate\n  __typename\n}\n\nfragment ChatMessageButton on ChatMessageButton {\n  type\n  url\n  text\n  __typename\n}"
        }
        
        response = await self.post(payload=payload)
        return await Message.from_dict(response['data']['createChatMessage'])
    
    async def send_image(self, chat_id: Union[int, str], file_name: Optional[str] = "image.jpg", local_path: Optional[str] = "./images/") -> Message:
        """
        Отправляет изображение в чат.
        Из-за multipart нужно чтобы изображение было в директории.

        :param chat_id: ID чата, куда будет отправлено изображение.
        :param file_name: Optional Имя изображения, по дефолту имя "image.jpg".
        :param local_path: Optional Путь к изображению, по дефолту "./images/"
        :return: class: `Message`
        """
        operations = {
            "operationName": "createChatMessage",
            "variables": {
                "input": {"chatId": chat_id},
                "file": None
            },
            "query": "mutation createChatMessage($input: CreateChatMessageInput!, $file: Upload) {\n  createChatMessage(input: $input, file: $file) {\n    ...RegularChatMessage\n    __typename\n  }\n}\n\nfragment RegularChatMessage on ChatMessage {\n  id\n  text\n  createdAt\n  deletedAt\n  isRead\n  isSuspicious\n  isBulkMessaging\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  file {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...ChatMessageUserFields\n    __typename\n  }\n  deal {\n    ...ChatMessageItemDeal\n    __typename\n  }\n  item {\n    ...ItemEdgeNode\n    __typename\n  }\n  transaction {\n    ...RegularTransaction\n    __typename\n  }\n  moderator {\n    ...UserEdgeNode\n    __typename\n  }\n  eventByUser {\n    ...ChatMessageUserFields\n    __typename\n  }\n  eventToUser {\n    ...ChatMessageUserFields\n    __typename\n  }\n  isAutoResponse\n  event\n  buttons {\n    ...ChatMessageButton\n    __typename\n  }\n  __typename\n}\n\nfragment RegularGameProfile on GameProfile {\n  id\n  name\n  type\n  slug\n  logo {\n    ...PartialFile\n    __typename\n  }\n  __typename\n}\n\nfragment PartialFile on File {\n  id\n  url\n  __typename\n}\n\nfragment ChatMessageUserFields on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment UserEdgeNode on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment ChatMessageItemDeal on ItemDeal {\n  id\n  direction\n  status\n  statusDescription\n  hasProblem\n  user {\n    ...ChatParticipant\n    __typename\n  }\n  testimonial {\n    ...ChatMessageDealTestimonial\n    __typename\n  }\n  item {\n    id\n    name\n    price\n    slug\n    rawPrice\n    sellerType\n    user {\n      ...ChatParticipant\n      __typename\n    }\n    category {\n      id\n      __typename\n    }\n    attachments {\n      ...PartialFile\n      __typename\n    }\n    comment\n    dataFields {\n      ...GameCategoryDataFieldWithValue\n      __typename\n    }\n    obtainingType {\n      ...GameCategoryObtainingType\n      __typename\n    }\n    __typename\n  }\n  obtainingFields {\n    ...GameCategoryDataFieldWithValue\n    __typename\n  }\n  chat {\n    id\n    type\n    __typename\n  }\n  transaction {\n    id\n    statusExpirationDate\n    __typename\n  }\n  statusExpirationDate\n  commentFromBuyer\n  __typename\n}\n\nfragment ChatParticipant on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment ChatMessageDealTestimonial on Testimonial {\n  id\n  status\n  text\n  rating\n  createdAt\n  updatedAt\n  creator {\n    ...RegularUserFragment\n    __typename\n  }\n  moderator {\n    ...RegularUserFragment\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  __typename\n}\n\nfragment GameCategoryDataFieldWithValue on GameCategoryDataFieldWithValue {\n  id\n  label\n  type\n  inputType\n  copyable\n  hidden\n  required\n  value\n  __typename\n}\n\nfragment GameCategoryObtainingType on GameCategoryObtainingType {\n  id\n  name\n  description\n  gameCategoryId\n  noCommentFromBuyer\n  instructionForBuyer\n  instructionForSeller\n  sequence\n  __typename\n}\n\nfragment ItemEdgeNode on ItemProfile {\n  ...MyItemEdgeNode\n  ...ForeignItemEdgeNode\n  __typename\n}\n\nfragment MyItemEdgeNode on MyItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  statusExpirationDate\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  createdAt\n  priorityPosition\n  __typename\n}\n\nfragment UserItemEdgeNode on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment ForeignItemEdgeNode on ForeignItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  priorityPosition\n  createdAt\n  __typename\n}\n\nfragment RegularTransaction on Transaction {\n  id\n  operation\n  direction\n  providerId\n  provider {\n    ...RegularTransactionProvider\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  creator {\n    ...RegularUserFragment\n    __typename\n  }\n  status\n  statusDescription\n  statusExpirationDate\n  value\n  fee\n  createdAt\n  props {\n    ...RegularTransactionProps\n    __typename\n  }\n  verifiedAt\n  verifiedBy {\n    ...UserEdgeNode\n    __typename\n  }\n  completedBy {\n    ...UserEdgeNode\n    __typename\n  }\n  paymentMethodId\n  completedAt\n  isSuspicious\n  __typename\n}\n\nfragment RegularTransactionProvider on TransactionProvider {\n  id\n  name\n  fee\n  account {\n    ...RegularTransactionProviderAccount\n    __typename\n  }\n  props {\n    ...TransactionProviderPropsFragment\n    __typename\n  }\n  limits {\n    ...ProviderLimits\n    __typename\n  }\n  paymentMethods {\n    ...TransactionPaymentMethod\n    __typename\n  }\n  __typename\n}\n\nfragment RegularTransactionProviderAccount on TransactionProviderAccount {\n  id\n  value\n  userId\n  __typename\n}\n\nfragment TransactionProviderPropsFragment on TransactionProviderPropsFragment {\n  requiredUserData {\n    ...TransactionProviderRequiredUserData\n    __typename\n  }\n  tooltip\n  __typename\n}\n\nfragment TransactionProviderRequiredUserData on TransactionProviderRequiredUserData {\n  email\n  phoneNumber\n  __typename\n}\n\nfragment ProviderLimits on ProviderLimits {\n  incoming {\n    ...ProviderLimitRange\n    __typename\n  }\n  outgoing {\n    ...ProviderLimitRange\n    __typename\n  }\n  __typename\n}\n\nfragment ProviderLimitRange on ProviderLimitRange {\n  min\n  max\n  __typename\n}\n\nfragment TransactionPaymentMethod on TransactionPaymentMethod {\n  id\n  name\n  fee\n  providerId\n  account {\n    ...RegularTransactionProviderAccount\n    __typename\n  }\n  props {\n    ...TransactionProviderPropsFragment\n    __typename\n  }\n  limits {\n    ...ProviderLimits\n    __typename\n  }\n  __typename\n}\n\nfragment RegularTransactionProps on TransactionPropsFragment {\n  creatorId\n  dealId\n  paidFromPendingIncome\n  paymentURL\n  successURL\n  paymentAccount {\n    id\n    value\n    __typename\n  }\n  paymentGateway\n  alreadySpent\n  exchangeRate\n  __typename\n}\n\nfragment ChatMessageButton on ChatMessageButton {\n  type\n  url\n  text\n  __typename\n}"
        }

        map_data = {
            "0": ["variables.file"]
        }

        mp = CurlMime()

        mp.addpart(
            name="operations", 
            content_type="application/json",
            data=json.dumps(operations)
        )

        mp.addpart(
            name="map", 
            content_type="application/json", 
            data=json.dumps(map_data)
        )

        mp.addpart(
            name="0",
            filename=file_name,
            content_type="image/jpeg",
            local_path=f"{local_path}{file_name}"
        )

        response = await self.post(
            headers={
                "Content-Type": "multipart/form-data",
                "X-Apollo-Operation-Name": "UploadImage"
            },
            multipart=mp,
        )

        return await Message.from_dict(response["data"]["createChatMessage"])
    
    async def mark_chat_as_read(self, chat_id: Optional[Union[str, List[str]]]) -> bool:
        """
        Отмечает чат и все сообщения в нем как прочитанные.

        :param chat_id: Идентификатор чата или список идентификаторов.
        :return: True, если операция выполнена успешно, False в противном случае.
        """
        if isinstance(chat_id, List) or isinstance(chat_id, list):
            for cid in chat_id:
                payload = {
                    "operationName": "markChatAsRead",
                    "variables": {
                        "input": {
                            "chatId": cid
                        }
                    },
                    "query": "mutation markChatAsRead($input: MarkChatAsReadInput!) {\n  markChatAsRead(input: $input) {\n    ...RegularChat\n    __typename\n  }\n}\n\nfragment RegularChat on Chat {\n  id\n  type\n  unreadMessagesCounter\n  bookmarked\n  isTextingAllowed\n  owner {\n    ...ChatParticipant\n    __typename\n  }\n  agent {\n    ...ChatParticipant\n    __typename\n  }\n  participants {\n    ...ChatParticipant\n    __typename\n  }\n  deals {\n    ...ChatActiveItemDeal\n    __typename\n  }\n  status\n  startedAt\n  finishedAt\n  __typename\n}\n\nfragment ChatParticipant on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment ChatActiveItemDeal on ItemDealProfile {\n  id\n  direction\n  status\n  hasProblem\n  statusDescription\n  testimonial {\n    id\n    rating\n    __typename\n  }\n  item {\n    ...ItemEdgeNode\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  __typename\n}\n\nfragment ItemEdgeNode on ItemProfile {\n  ...MyItemEdgeNode\n  ...ForeignItemEdgeNode\n  __typename\n}\n\nfragment MyItemEdgeNode on MyItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  statusExpirationDate\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  createdAt\n  priorityPosition\n  __typename\n}\n\nfragment PartialFile on File {\n  id\n  url\n  __typename\n}\n\nfragment UserItemEdgeNode on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment UserEdgeNode on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment ForeignItemEdgeNode on ForeignItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  priorityPosition\n  createdAt\n  __typename\n}"
                }
                response = await self.post(payload=payload)
            return True
        else:
            payload = {
                "operationName": "markChatAsRead",
                "variables": {
                    "input": {
                        "chatId": chat_id
                    }
                },
                "query": "mutation markChatAsRead($input: MarkChatAsReadInput!) {\n  markChatAsRead(input: $input) {\n    ...RegularChat\n    __typename\n  }\n}\n\nfragment RegularChat on Chat {\n  id\n  type\n  unreadMessagesCounter\n  bookmarked\n  isTextingAllowed\n  owner {\n    ...ChatParticipant\n    __typename\n  }\n  agent {\n    ...ChatParticipant\n    __typename\n  }\n  participants {\n    ...ChatParticipant\n    __typename\n  }\n  deals {\n    ...ChatActiveItemDeal\n    __typename\n  }\n  status\n  startedAt\n  finishedAt\n  __typename\n}\n\nfragment ChatParticipant on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment ChatActiveItemDeal on ItemDealProfile {\n  id\n  direction\n  status\n  hasProblem\n  statusDescription\n  testimonial {\n    id\n    rating\n    __typename\n  }\n  item {\n    ...ItemEdgeNode\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  __typename\n}\n\nfragment ItemEdgeNode on ItemProfile {\n  ...MyItemEdgeNode\n  ...ForeignItemEdgeNode\n  __typename\n}\n\nfragment MyItemEdgeNode on MyItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  statusExpirationDate\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  createdAt\n  priorityPosition\n  __typename\n}\n\nfragment PartialFile on File {\n  id\n  url\n  __typename\n}\n\nfragment UserItemEdgeNode on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment UserEdgeNode on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment ForeignItemEdgeNode on ForeignItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  priorityPosition\n  createdAt\n  __typename\n}"
            }
            response = await self.post(payload=payload)
            return True if response['data']['markChatAsRead'] else False
    
    async def get_chat_messages(self, chat_id: Optional[str | 'Chat'], count: Optional[int | str] = 10) -> List[Message]:
        """
        Получает список сообщений в чате.

        :param chat_id: Айдишник чата.
        :return: `List[Message]` - список сообщений.
        """
        if isinstance(chat_id, Chat):
            chat_id = chat_id.id
        payload = {
            "operationName": "chatMessages",
            "variables": {
                "pagination": {
                    "first": count if type(count) == int else 100
                    },
                "filter": {
                    "chatId": chat_id
                }
            }, "query": "query chatMessages($pagination: Pagination, $filter: ChatMessageFilter) {\n  chatMessages(pagination: $pagination, filter: $filter) {\n    edges {\n      ...ChatMessageEdgeFields\n      __typename\n    }\n    pageInfo {\n      startCursor\n      endCursor\n      hasPreviousPage\n      hasNextPage\n      __typename\n    }\n    totalCount\n    __typename\n  }\n}\n\nfragment ChatMessageEdgeFields on ChatMessageEdge {\n  cursor\n  node {\n    ...RegularChatMessage\n    __typename\n  }\n  __typename\n}\n\nfragment RegularChatMessage on ChatMessage {\n  id\n  text\n  createdAt\n  deletedAt\n  isRead\n  isSuspicious\n  isBulkMessaging\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  file {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...ChatMessageUserFields\n    __typename\n  }\n  deal {\n    ...ChatMessageItemDeal\n    __typename\n  }\n  item {\n    ...ItemEdgeNode\n    __typename\n  }\n  transaction {\n    ...RegularTransaction\n    __typename\n  }\n  moderator {\n    ...UserEdgeNode\n    __typename\n  }\n  eventByUser {\n    ...ChatMessageUserFields\n    __typename\n  }\n  eventToUser {\n    ...ChatMessageUserFields\n    __typename\n  }\n  isAutoResponse\n  event\n  buttons {\n    ...ChatMessageButton\n    __typename\n  }\n  __typename\n}\n\nfragment RegularGameProfile on GameProfile {\n  id\n  name\n  type\n  slug\n  logo {\n    ...PartialFile\n    __typename\n  }\n  __typename\n}\n\nfragment PartialFile on File {\n  id\n  url\n  __typename\n}\n\nfragment ChatMessageUserFields on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment UserEdgeNode on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment ChatMessageItemDeal on ItemDeal {\n  id\n  direction\n  status\n  statusDescription\n  hasProblem\n  user {\n    ...ChatParticipant\n    __typename\n  }\n  testimonial {\n    ...ChatMessageDealTestimonial\n    __typename\n  }\n  item {\n    id\n    name\n    price\n    slug\n    rawPrice\n    sellerType\n    user {\n      ...ChatParticipant\n      __typename\n    }\n    category {\n      id\n      __typename\n    }\n    attachments {\n      ...PartialFile\n      __typename\n    }\n    comment\n    dataFields {\n      ...GameCategoryDataFieldWithValue\n      __typename\n    }\n    obtainingType {\n      ...GameCategoryObtainingType\n      __typename\n    }\n    __typename\n  }\n  obtainingFields {\n    ...GameCategoryDataFieldWithValue\n    __typename\n  }\n  chat {\n    id\n    type\n    __typename\n  }\n  transaction {\n    id\n    statusExpirationDate\n    __typename\n  }\n  statusExpirationDate\n  commentFromBuyer\n  __typename\n}\n\nfragment ChatParticipant on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment ChatMessageDealTestimonial on Testimonial {\n  id\n  status\n  text\n  rating\n  createdAt\n  updatedAt\n  creator {\n    ...RegularUserFragment\n    __typename\n  }\n  moderator {\n    ...RegularUserFragment\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  __typename\n}\n\nfragment GameCategoryDataFieldWithValue on GameCategoryDataFieldWithValue {\n  id\n  label\n  type\n  inputType\n  copyable\n  hidden\n  required\n  value\n  __typename\n}\n\nfragment GameCategoryObtainingType on GameCategoryObtainingType {\n  id\n  name\n  description\n  gameCategoryId\n  noCommentFromBuyer\n  instructionForBuyer\n  instructionForSeller\n  sequence\n  __typename\n}\n\nfragment ItemEdgeNode on ItemProfile {\n  ...MyItemEdgeNode\n  ...ForeignItemEdgeNode\n  __typename\n}\n\nfragment MyItemEdgeNode on MyItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  statusExpirationDate\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  createdAt\n  priorityPosition\n  __typename\n}\n\nfragment UserItemEdgeNode on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment ForeignItemEdgeNode on ForeignItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  priorityPosition\n  createdAt\n  __typename\n}\n\nfragment RegularTransaction on Transaction {\n  id\n  operation\n  direction\n  providerId\n  provider {\n    ...RegularTransactionProvider\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  creator {\n    ...RegularUserFragment\n    __typename\n  }\n  status\n  statusDescription\n  statusExpirationDate\n  value\n  fee\n  createdAt\n  props {\n    ...RegularTransactionProps\n    __typename\n  }\n  verifiedAt\n  verifiedBy {\n    ...UserEdgeNode\n    __typename\n  }\n  completedBy {\n    ...UserEdgeNode\n    __typename\n  }\n  paymentMethodId\n  completedAt\n  isSuspicious\n  __typename\n}\n\nfragment RegularTransactionProvider on TransactionProvider {\n  id\n  name\n  fee\n  account {\n    ...RegularTransactionProviderAccount\n    __typename\n  }\n  props {\n    ...TransactionProviderPropsFragment\n    __typename\n  }\n  limits {\n    ...ProviderLimits\n    __typename\n  }\n  paymentMethods {\n    ...TransactionPaymentMethod\n    __typename\n  }\n  __typename\n}\n\nfragment RegularTransactionProviderAccount on TransactionProviderAccount {\n  id\n  value\n  userId\n  __typename\n}\n\nfragment TransactionProviderPropsFragment on TransactionProviderPropsFragment {\n  requiredUserData {\n    ...TransactionProviderRequiredUserData\n    __typename\n  }\n  tooltip\n  __typename\n}\n\nfragment TransactionProviderRequiredUserData on TransactionProviderRequiredUserData {\n  email\n  phoneNumber\n  __typename\n}\n\nfragment ProviderLimits on ProviderLimits {\n  incoming {\n    ...ProviderLimitRange\n    __typename\n  }\n  outgoing {\n    ...ProviderLimitRange\n    __typename\n  }\n  __typename\n}\n\nfragment ProviderLimitRange on ProviderLimitRange {\n  min\n  max\n  __typename\n}\n\nfragment TransactionPaymentMethod on TransactionPaymentMethod {\n  id\n  name\n  fee\n  providerId\n  account {\n    ...RegularTransactionProviderAccount\n    __typename\n  }\n  props {\n    ...TransactionProviderPropsFragment\n    __typename\n  }\n  limits {\n    ...ProviderLimits\n    __typename\n  }\n  __typename\n}\n\nfragment RegularTransactionProps on TransactionPropsFragment {\n  creatorId\n  dealId\n  paidFromPendingIncome\n  paymentURL\n  successURL\n  paymentAccount {\n    id\n    value\n    __typename\n  }\n  paymentGateway\n  alreadySpent\n  exchangeRate\n  __typename\n}\n\nfragment ChatMessageButton on ChatMessageButton {\n  type\n  url\n  text\n  __typename\n}"}
        
        response = await self.post(payload=payload)
        messages = response.get('data', {}).get('chatMessages', {}).get('edges', [])
        messages = messages[::-1] #Чтобы корректно возвращало с верху (старые) вниз (новые)
        return [await Message.from_dict(message["node"]) for message in messages]

    async def get_item(self, item_id: str) -> LotDetails:
        """
        Получает информацию о лоте по его ID.

        :param item_id: str - Айдишник лота.
        :return: `LotDetails` - информация о лоте
        """
        payload = {
            "operationName": "item",
            "variables": {
                "slug": item_id
            },
            "query": "query item($slug: String, $id: UUID) {\n  item(slug: $slug, id: $id) {\n    ...RegularItem\n    __typename\n  }\n}\n\nfragment RegularItem on Item {\n  ...RegularMyItem\n  ...RegularForeignItem\n  __typename\n}\n\nfragment RegularMyItem on MyItem {\n  ...ItemFields\n  priority\n  sequence\n  priorityPrice\n  statusExpirationDate\n  comment\n  viewsCounter\n  statusDescription\n  editable\n  statusPayment {\n    ...StatusPaymentTransaction\n    __typename\n  }\n  moderator {\n    id\n    username\n    __typename\n  }\n  approvalDate\n  deletedAt\n  createdAt\n  updatedAt\n  mayBePublished\n  __typename\n}\n\nfragment ItemFields on Item {\n  id\n  slug\n  name\n  description\n  rawPrice\n  price\n  attributes\n  status\n  priorityPosition\n  sellerType\n  user {\n    ...ItemUser\n    __typename\n  }\n  buyer {\n    ...ItemUser\n    __typename\n  }\n  attachments {\n    ...PartialFile\n    __typename\n  }\n  category {\n    ...RegularGameCategory\n    __typename\n  }\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  comment\n  dataFields {\n    ...GameCategoryDataFieldWithValue\n    __typename\n  }\n  obtainingType {\n    ...GameCategoryObtainingType\n    __typename\n  }\n  __typename\n}\n\nfragment ItemUser on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment UserEdgeNode on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment PartialFile on File {\n  id\n  url\n  __typename\n}\n\nfragment RegularGameCategory on GameCategory {\n  id\n  slug\n  name\n  categoryId\n  gameId\n  obtaining\n  options {\n    ...RegularGameCategoryOption\n    __typename\n  }\n  props {\n    ...GameCategoryProps\n    __typename\n  }\n  noCommentFromBuyer\n  instructionForBuyer\n  instructionForSeller\n  useCustomObtaining\n  autoConfirmPeriod\n  autoModerationMode\n  __typename\n}\n\nfragment RegularGameCategoryOption on GameCategoryOption {\n  id\n  group\n  label\n  type\n  field\n  value\n  sequence\n  valueRangeLimit {\n    min\n    max\n    __typename\n  }\n  __typename\n}\n\nfragment GameCategoryProps on GameCategoryPropsObjectType {\n  minTestimonials\n  __typename\n}\n\nfragment RegularGameProfile on GameProfile {\n  id\n  name\n  type\n  slug\n  logo {\n    ...PartialFile\n    __typename\n  }\n  __typename\n}\n\nfragment GameCategoryDataFieldWithValue on GameCategoryDataFieldWithValue {\n  id\n  label\n  type\n  inputType\n  copyable\n  hidden\n  required\n  value\n  __typename\n}\n\nfragment GameCategoryObtainingType on GameCategoryObtainingType {\n  id\n  name\n  description\n  gameCategoryId\n  noCommentFromBuyer\n  instructionForBuyer\n  instructionForSeller\n  sequence\n  __typename\n}\n\nfragment StatusPaymentTransaction on Transaction {\n  id\n  operation\n  direction\n  providerId\n  status\n  statusDescription\n  statusExpirationDate\n  value\n  props {\n    paymentURL\n    __typename\n  }\n  __typename\n}\n\nfragment RegularForeignItem on ForeignItem {\n  ...ItemFields\n  __typename\n}"}
        
        response = await self.post(payload=payload)
        return await LotDetails.from_dict(response['data']['item'])

    async def update_item(self, item_id: str, 
                    comment: Optional[str] = None,
                    description: Optional[str] = None, 
                    name: Optional[str] = None, 
                    price: Optional[int] = None) -> LotDetails:
        """
        Обновляет информацию о лоте по его айдишнику.
        
        :param item_id: ID лота.
        :param comment: Optional Текст в "Данные товара".
        :param description: Optional Текст в описание товара.
        :param name: Optional Название лота.
        :param price: Optional Цена лота.

        :return: class: LotDetails
        """
        _input = {}
        if comment is not None:
            _input["comment"] = comment
        if description is not None:
            _input["description"] = description
        if name is not None:
            _input["name"] = name
        if price is not None:
            _input["price"] = price
        _input["id"] = item_id

        payload = {
            "operationName": "updateItem",
            "variables": {
                "input": _input,
                "addedAttachments": None
            },
            "query": "mutation updateItem($input: UpdateItemInput!, $addedAttachments: [Upload!]) {\n  updateItem(input: $input, addedAttachments: $addedAttachments) {\n    ...RegularItem\n    __typename\n  }\n}\n\nfragment RegularItem on Item {\n  ...RegularMyItem\n  ...RegularForeignItem\n  __typename\n}\n\nfragment RegularMyItem on MyItem {\n  ...ItemFields\n  priority\n  sequence\n  priorityPrice\n  statusExpirationDate\n  comment\n  viewsCounter\n  statusDescription\n  editable\n  statusPayment {\n    ...StatusPaymentTransaction\n    __typename\n  }\n  moderator {\n    id\n    username\n    __typename\n  }\n  approvalDate\n  deletedAt\n  createdAt\n  updatedAt\n  mayBePublished\n  __typename\n}\n\nfragment ItemFields on Item {\n  id\n  slug\n  name\n  description\n  rawPrice\n  price\n  attributes\n  status\n  priorityPosition\n  sellerType\n  user {\n    ...ItemUser\n    __typename\n  }\n  buyer {\n    ...ItemUser\n    __typename\n  }\n  attachments {\n    ...PartialFile\n    __typename\n  }\n  category {\n    ...RegularGameCategory\n    __typename\n  }\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  comment\n  dataFields {\n    ...GameCategoryDataFieldWithValue\n    __typename\n  }\n  obtainingType {\n    ...GameCategoryObtainingType\n    __typename\n  }\n  __typename\n}\n\nfragment ItemUser on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment UserEdgeNode on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment PartialFile on File {\n  id\n  url\n  __typename\n}\n\nfragment RegularGameCategory on GameCategory {\n  id\n  slug\n  name\n  categoryId\n  gameId\n  obtaining\n  options {\n    ...RegularGameCategoryOption\n    __typename\n  }\n  props {\n    ...GameCategoryProps\n    __typename\n  }\n  noCommentFromBuyer\n  instructionForBuyer\n  instructionForSeller\n  useCustomObtaining\n  autoConfirmPeriod\n  autoModerationMode\n  __typename\n}\n\nfragment RegularGameCategoryOption on GameCategoryOption {\n  id\n  group\n  label\n  type\n  field\n  value\n  sequence\n  valueRangeLimit {\n    min\n    max\n    __typename\n  }\n  __typename\n}\n\nfragment GameCategoryProps on GameCategoryPropsObjectType {\n  minTestimonials\n  __typename\n}\n\nfragment RegularGameProfile on GameProfile {\n  id\n  name\n  type\n  slug\n  logo {\n    ...PartialFile\n    __typename\n  }\n  __typename\n}\n\nfragment GameCategoryDataFieldWithValue on GameCategoryDataFieldWithValue {\n  id\n  label\n  type\n  inputType\n  copyable\n  hidden\n  required\n  value\n  __typename\n}\n\nfragment GameCategoryObtainingType on GameCategoryObtainingType {\n  id\n  name\n  description\n  gameCategoryId\n  noCommentFromBuyer\n  instructionForBuyer\n  instructionForSeller\n  sequence\n  __typename\n}\n\nfragment StatusPaymentTransaction on Transaction {\n  id\n  operation\n  direction\n  providerId\n  status\n  statusDescription\n  statusExpirationDate\n  value\n  props {\n    paymentURL\n    __typename\n  }\n  __typename\n}\n\nfragment RegularForeignItem on ForeignItem {\n  ...ItemFields\n  __typename\n}"
        }
        response = await self.post(payload=payload)
        return await LotDetails.from_dict(response['data']['updateItem'])
    
    async def remove_item(self, item_id: str) -> LotDetails:
        """
        Удаляет лот по его айдишнику.
        
        :param item_id: ID лота.
        :return: class: LotDetails
        """
        payload = {
            "operationName": "removeItem",
            "variables": {
                "id": item_id
            },
            "query": "mutation removeItem($id: UUID!) {\n  removeItem(id: $id) {\n    ...RegularItem\n    __typename\n  }\n}\n\nfragment RegularItem on Item {\n  ...RegularMyItem\n  ...RegularForeignItem\n  __typename\n}\n\nfragment RegularMyItem on MyItem {\n  ...ItemFields\n  priority\n  sequence\n  priorityPrice\n  statusExpirationDate\n  comment\n  viewsCounter\n  statusDescription\n  editable\n  statusPayment {\n    ...StatusPaymentTransaction\n    __typename\n  }\n  moderator {\n    id\n    username\n    __typename\n  }\n  approvalDate\n  deletedAt\n  createdAt\n  updatedAt\n  mayBePublished\n  __typename\n}\n\nfragment ItemFields on Item {\n  id\n  slug\n  name\n  description\n  rawPrice\n  price\n  attributes\n  status\n  priorityPosition\n  sellerType\n  user {\n    ...ItemUser\n    __typename\n  }\n  buyer {\n    ...ItemUser\n    __typename\n  }\n  attachments {\n    ...PartialFile\n    __typename\n  }\n  category {\n    ...RegularGameCategory\n    __typename\n  }\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  comment\n  dataFields {\n    ...GameCategoryDataFieldWithValue\n    __typename\n  }\n  obtainingType {\n    ...GameCategoryObtainingType\n    __typename\n  }\n  __typename\n}\n\nfragment ItemUser on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment UserEdgeNode on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment PartialFile on File {\n  id\n  url\n  __typename\n}\n\nfragment RegularGameCategory on GameCategory {\n  id\n  slug\n  name\n  categoryId\n  gameId\n  obtaining\n  options {\n    ...RegularGameCategoryOption\n    __typename\n  }\n  props {\n    ...GameCategoryProps\n    __typename\n  }\n  noCommentFromBuyer\n  instructionForBuyer\n  instructionForSeller\n  useCustomObtaining\n  autoConfirmPeriod\n  autoModerationMode\n  __typename\n}\n\nfragment RegularGameCategoryOption on GameCategoryOption {\n  id\n  group\n  label\n  type\n  field\n  value\n  sequence\n  valueRangeLimit {\n    min\n    max\n    __typename\n  }\n  __typename\n}\n\nfragment GameCategoryProps on GameCategoryPropsObjectType {\n  minTestimonials\n  __typename\n}\n\nfragment RegularGameProfile on GameProfile {\n  id\n  name\n  type\n  slug\n  logo {\n    ...PartialFile\n    __typename\n  }\n  __typename\n}\n\nfragment GameCategoryDataFieldWithValue on GameCategoryDataFieldWithValue {\n  id\n  label\n  type\n  inputType\n  copyable\n  hidden\n  required\n  value\n  __typename\n}\n\nfragment GameCategoryObtainingType on GameCategoryObtainingType {\n  id\n  name\n  description\n  gameCategoryId\n  noCommentFromBuyer\n  instructionForBuyer\n  instructionForSeller\n  sequence\n  __typename\n}\n\nfragment StatusPaymentTransaction on Transaction {\n  id\n  operation\n  direction\n  providerId\n  status\n  statusDescription\n  statusExpirationDate\n  value\n  props {\n    paymentURL\n    __typename\n  }\n  __typename\n}\n\nfragment RegularForeignItem on ForeignItem {\n  ...ItemFields\n  __typename\n}"}
        
        response = await self.post(payload=payload)
        return await LotDetails.from_dict(response['data']['removeItem'])
    
    async def get_count_items(self) -> int:
        """
        Возвращает количество лотов на аккаунте прямым запросом,
        Тоже самое можно сделать через функцию getme(), get_profile_items.
        
        :return: int
        """
        payload = {
            "operationName": "countItems",
            "variables": {
                "filter": {
                    "userId": self.user_id
                    }
                },
            "query": "query countItems($filter: ItemFilter) {\n  countItems(filter: $filter)\n}"
            }

        response = await self.post(payload=payload)
        return response['data']['countItems']
    
    async def get_profile_items(self, count: Union[int, str] = 16) -> ItemProfileList:
        """
        Возвращает список лотов на аккаунте.

        :param count: Union[int, str]: Количество лотов, которое нужно получить.
        :return: `ItemProfileList`: Список лотов на аккаунте.
        """
        payload: Dict[str, Any] = {
            "operationName": "items",
            "variables": {
                "pagination": {
                    "first": count
                },
                "filter": {
                    "userId": self.user_id,
                    "status": ["APPROVED","PENDING_MODERATION","PENDING_APPROVAL"]
                }
            },
            "query":"query items($filter: ItemFilter, $pagination: Pagination) {\n  items(filter: $filter, pagination: $pagination) {\n    ...ItemProfileList\n    __typename\n  }\n}\n\nfragment ItemProfileList on ItemProfileList {\n  edges {\n    ...ItemEdgeFields\n    __typename\n  }\n  pageInfo {\n    startCursor\n    endCursor\n    hasPreviousPage\n    hasNextPage\n    __typename\n  }\n  totalCount\n  __typename\n}\n\nfragment ItemEdgeFields on ItemProfileEdge {\n  cursor\n  node {\n    ...ItemEdgeNode\n    __typename\n  }\n  __typename\n}\n\nfragment ItemEdgeNode on ItemProfile {\n  ...MyItemEdgeNode\n  ...ForeignItemEdgeNode\n  __typename\n}\n\nfragment MyItemEdgeNode on MyItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  statusExpirationDate\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  createdAt\n  priorityPosition\n  __typename\n}\n\nfragment PartialFile on File {\n  id\n  url\n  __typename\n}\n\nfragment UserItemEdgeNode on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment UserEdgeNode on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment ForeignItemEdgeNode on ForeignItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  priorityPosition\n  createdAt\n  __typename\n}"
        }
        response = await self.post(payload=payload)
        return await ItemProfileList.from_dict(response['data']['items'])
    
    async def update_deal(self, deal_id: str, status: str = "SENT") -> bool:
        """
        Обновляет статус лота, возвращает деньги/выполняет заказ.
        SENT - Подтвержает заказ (продавец).
        ROLLED_BACK - Возвращает деньги за заказ.
        CONFIRMED - Подтвержает выполнение заказа (покупатель).

        :param deal_id: ID лота.
        :param status: Статус лота.
        :return: bool: True, если операция выполнена успешно, False в противном случае.
        """
        payload = {
            "operationName": "updateDeal",
            "variables": {
                "input": {
                    "id": deal_id,
                    "status": status
                }
            }, "query": "mutation updateDeal($input: UpdateItemDealInput!) {\n  updateDeal(input: $input) {\n    ...RegularItemDeal\n    __typename\n  }\n}\n\nfragment RegularItemDeal on ItemDeal {\n  id\n  status\n  direction\n  statusExpirationDate\n  statusDescription\n  obtaining\n  hasProblem\n  reportProblemEnabled\n  completedBy {\n    ...UserEdgeNode\n    __typename\n  }\n  props {\n    ...ItemDealProps\n    __typename\n  }\n  prevStatus\n  completedAt\n  createdAt\n  logs {\n    ...ItemLog\n    __typename\n  }\n  transaction {\n    ...ItemDealTransaction\n    __typename\n  }\n  user {\n    ...UserEdgeNode\n    __typename\n  }\n  chat {\n    ...RegularChat\n    __typename\n  }\n  item {\n    ...PartialItem\n    __typename\n  }\n  testimonial {\n    ...RegularTestimonial\n    __typename\n  }\n  obtainingFields {\n    ...GameCategoryDataFieldWithValue\n    __typename\n  }\n  commentFromBuyer\n  __typename\n}\n\nfragment UserEdgeNode on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment ItemDealProps on ItemDealProps {\n  autoConfirmPeriod\n  __typename\n}\n\nfragment ItemLog on ItemLog {\n  id\n  event\n  createdAt\n  user {\n    ...UserEdgeNode\n    __typename\n  }\n  __typename\n}\n\nfragment ItemDealTransaction on Transaction {\n  id\n  operation\n  direction\n  providerId\n  status\n  value\n  createdAt\n  paymentMethodId\n  statusExpirationDate\n  __typename\n}\n\nfragment RegularChat on Chat {\n  id\n  type\n  unreadMessagesCounter\n  bookmarked\n  isTextingAllowed\n  owner {\n    ...ChatParticipant\n    __typename\n  }\n  agent {\n    ...ChatParticipant\n    __typename\n  }\n  participants {\n    ...ChatParticipant\n    __typename\n  }\n  deals {\n    ...ChatActiveItemDeal\n    __typename\n  }\n  status\n  startedAt\n  finishedAt\n  __typename\n}\n\nfragment ChatParticipant on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment ChatActiveItemDeal on ItemDealProfile {\n  id\n  direction\n  status\n  hasProblem\n  statusDescription\n  testimonial {\n    id\n    rating\n    __typename\n  }\n  item {\n    ...ItemEdgeNode\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  __typename\n}\n\nfragment ItemEdgeNode on ItemProfile {\n  ...MyItemEdgeNode\n  ...ForeignItemEdgeNode\n  __typename\n}\n\nfragment MyItemEdgeNode on MyItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  statusExpirationDate\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  createdAt\n  priorityPosition\n  __typename\n}\n\nfragment PartialFile on File {\n  id\n  url\n  __typename\n}\n\nfragment UserItemEdgeNode on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment ForeignItemEdgeNode on ForeignItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  priorityPosition\n  createdAt\n  __typename\n}\n\nfragment PartialItem on Item {\n  ...PartialMyItem\n  ...PartialForeignItem\n  __typename\n}\n\nfragment PartialMyItem on MyItem {\n  id\n  slug\n  name\n  price\n  rawPrice\n  comment\n  attachments {\n    ...RegularFile\n    __typename\n  }\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  category {\n    ...RegularGameCategory\n    __typename\n  }\n  user {\n    ...UserEdgeNode\n    __typename\n  }\n  priorityPrice\n  priority\n  dataFields {\n    ...GameCategoryDataFieldWithValue\n    __typename\n  }\n  obtainingType {\n    ...GameCategoryObtainingType\n    __typename\n  }\n  status\n  sellerType\n  createdAt\n  __typename\n}\n\nfragment RegularFile on File {\n  id\n  url\n  filename\n  mime\n  __typename\n}\n\nfragment RegularGameProfile on GameProfile {\n  id\n  name\n  type\n  slug\n  logo {\n    ...PartialFile\n    __typename\n  }\n  __typename\n}\n\nfragment RegularGameCategory on GameCategory {\n  id\n  slug\n  name\n  categoryId\n  gameId\n  obtaining\n  options {\n    ...RegularGameCategoryOption\n    __typename\n  }\n  props {\n    ...GameCategoryProps\n    __typename\n  }\n  noCommentFromBuyer\n  instructionForBuyer\n  instructionForSeller\n  useCustomObtaining\n  autoConfirmPeriod\n  autoModerationMode\n  __typename\n}\n\nfragment RegularGameCategoryOption on GameCategoryOption {\n  id\n  group\n  label\n  type\n  field\n  value\n  sequence\n  valueRangeLimit {\n    min\n    max\n    __typename\n  }\n  __typename\n}\n\nfragment GameCategoryProps on GameCategoryPropsObjectType {\n  minTestimonials\n  __typename\n}\n\nfragment GameCategoryDataFieldWithValue on GameCategoryDataFieldWithValue {\n  id\n  label\n  type\n  inputType\n  copyable\n  hidden\n  required\n  value\n  __typename\n}\n\nfragment GameCategoryObtainingType on GameCategoryObtainingType {\n  id\n  name\n  description\n  gameCategoryId\n  noCommentFromBuyer\n  instructionForBuyer\n  instructionForSeller\n  sequence\n  __typename\n}\n\nfragment PartialForeignItem on ForeignItem {\n  id\n  slug\n  name\n  price\n  rawPrice\n  comment\n  priority\n  attachments {\n    ...RegularFile\n    __typename\n  }\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  category {\n    id\n    slug\n    name\n    obtaining\n    autoConfirmPeriod\n    __typename\n  }\n  user {\n    ...UserEdgeNode\n    __typename\n  }\n  dataFields {\n    ...GameCategoryDataFieldWithValue\n    __typename\n  }\n  obtainingType {\n    ...GameCategoryObtainingType\n    __typename\n  }\n  status\n  sellerType\n  createdAt\n  __typename\n}\n\nfragment RegularTestimonial on Testimonial {\n  id\n  status\n  text\n  rating\n  createdAt\n  updatedAt\n  deal {\n    ...RegularItemDealProfile\n    __typename\n  }\n  creator {\n    ...RegularUserFragment\n    __typename\n  }\n  moderator {\n    ...RegularUserFragment\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  __typename\n}\n\nfragment RegularItemDealProfile on ItemDealProfile {\n  id\n  direction\n  status\n  item {\n    ...RegularItemProfile\n    __typename\n  }\n  testimonial {\n    ...TestimonialProfileFields\n    __typename\n  }\n  __typename\n}\n\nfragment RegularItemProfile on ItemProfile {\n  ...RegularMyItemProfile\n  ...RegularForeignItemProfile\n  __typename\n}\n\nfragment RegularMyItemProfile on MyItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  statusExpirationDate\n  viewsCounter\n  approvalDate\n  createdAt\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  category {\n    ...RegularGameCategoryProfile\n    __typename\n  }\n  user {\n    ...ItemUser\n    __typename\n  }\n  __typename\n}\n\nfragment RegularGameCategoryProfile on GameCategoryProfile {\n  id\n  slug\n  name\n  __typename\n}\n\nfragment ItemUser on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment RegularForeignItemProfile on ForeignItemProfile {\n  id\n  slug\n  priority\n  name\n  price\n  rawPrice\n  approvalDate\n  createdAt\n  sellerType\n  attachment {\n    ...RegularFile\n    __typename\n  }\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  category {\n    ...RegularGameCategoryProfile\n    __typename\n  }\n  user {\n    ...ItemUser\n    __typename\n  }\n  __typename\n}\n\nfragment TestimonialProfileFields on TestimonialProfile {\n  id\n  status\n  text\n  rating\n  createdAt\n  __typename\n}"
        }
        response = await self.post(payload=payload)
        return True if response["data"]["updateDeal"] else False
    
    async def get_unreaded_chats(self) -> Optional[List[str]]:
        """
        Получает список ID чатов, в которых есть непрочитанные сообщения.

        :return: Optional[List[str]]: список ID чатов, в которых есть непрочитанные сообщения.
        
        :return: Optional[List[str]]: Список ID чатов, в которых есть непрочитанные сообщения.
        """
        chats: Chats = await self.get_chats()
        chats = await self.get_chats()
        unreaded_chats: List[str] = []

        for chat in chats.edges:
            if chat.node.unreadMessagesCounter > 0:
                unreaded_chats.append(chat.node.id)
        return unreaded_chats
    
    async def get_link_stats(self) -> LinkStatsSummary:
        """
        Получает статистику с вашей реферальной ссылки.
        С этого момента query у меня закончились, поэтому
        Используется sha-256 хеш. Удобно вроде.
        
        :return: LinkStatsSummary
        """
        variables: Dict[str, Any] = {
            "filter": {
                "type": "REFERRAL",
                "userId": self.user_id
            }
        }
        extensions: Dict[str, Any] = {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "b9b974c77cbddfaaa756e963d4c86e72721d9081678eb7a4c885f2e3c56ae2d9"
            }
        }
        payload: Dict[str, Any] = {
            "operationName": "linkStatsSummary",
            "variables": json.dumps(variables),
            "extensions": json.dumps(extensions)
        }

        link: str = f'https://playerok.com/graphql?{urlencode(payload)}'

        response: Dict[str, Any] = await self.get(link)
        return await LinkStatsSummary.from_dict(response.get("data").get("linkStatsSummary"))

    async def get_email_code(self, email: str) -> bool:
        """
        Отправляет запрос для входа в аккаунт по почте.
        Кд - 60 секунд, при сильном спаме - "Слишком много попыток, пожалуйста, попробуйте повторить запрос позже".
        
        :param email: str: Почта
        :return: bool: True если запрос успешно отправлен
        :rtype: bool
        """
        payload: Dict[str, Any] = {
            "operationName": "getEmailAuthCode",
            "variables": {
                "email": email
            },
            "query": "mutation getEmailAuthCode($email: String!) {\n  getEmailAuthCode(input: {email: $email})\n}"
        }

        response = await self.session.post(
            url="https://playerok.com/graphql",
            json=payload,
            impersonate="chrome116"
        )
        if response.status != 200:
            response_json: Dict[str, Any] = response.json()
            logger.info(response_json['errors'][0]['message'])
            return False
        return True

    async def get_email_code_check(self, email: str, code: str) -> Optional[str]:
        """
        Проверяет код для входа в аккаунт по почте.
        Ответ либо удачный, либо нет. Использовать вместе с get_email_code.
        
        :param email: str: Почта
        :param code: str: 6-ти значный код
        :return: Optional[str]: Токен аккаунта, либо None если возникла ошибка
        """
        payload = {
            "operationName": "checkEmailAuthCode",
            "variables": {
                "input": {
                    "code": code,
                    "email": email
                    }
                }, 
            "query": "mutation checkEmailAuthCode($input: CheckEmailAuthCodeInput!) {\n  checkEmailAuthCode(input: $input) {\n    ...Viewer\n    __typename\n  }\n}\n\nfragment Viewer on User {\n  id\n  username\n  email\n  role\n  hasFrozenBalance\n  supportChatId\n  systemChatId\n  unreadChatsCounter\n  isBlocked\n  isBlockedFor\n  createdAt\n  profile {\n    id\n    avatarURL\n    __typename\n  }\n  __typename\n}"
        }

        response = await self.session.post(
            url="https://playerok.com/graphql",
            json=payload,
            impersonate="chrome116"
        )
        response = response.json()
        if 'errors' in response:
            logger.info(response['errors'][0]['message'])
            return None

        cookies = self.session.cookies.get_dict()
        return cookies.get("token")

    async def create_deal(self, item_id: str, transaction_provider_id: str = "LOCAL") -> CreateDeal:
        """
        Создает новую сделку (покупает товар).

        :param item_id: str: ID лота
        :param transaction_provider_id: str: ID провайдера: "LOCAL" - списать с баланса плеерка
        :return: CreateDeal: Созданная сделка
        """
        payload = {
            "operationName": "createDeal",
            "variables": {
                "input": {
                    "itemId": item_id,
                    "transactionProviderId": transaction_provider_id,
                    "transactionProviderData": {
                        "paymentMethodId": "null"
                    }
                }
            },
            "query": "mutation createDeal($input: CreateItemDealInput!) {\n  createDeal(input: $input) {\n    ...RegularTransaction\n    __typename\n  }\n}\n\nfragment RegularTransaction on Transaction {\n  id\n  operation\n  direction\n  providerId\n  provider {\n    ...RegularTransactionProvider\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  creator {\n    ...RegularUserFragment\n    __typename\n  }\n  status\n  statusDescription\n  statusExpirationDate\n  value\n  fee\n  createdAt\n  props {\n    ...RegularTransactionProps\n    __typename\n  }\n  verifiedAt\n  verifiedBy {\n    ...UserEdgeNode\n    __typename\n  }\n  completedBy {\n    ...UserEdgeNode\n    __typename\n  }\n  paymentMethodId\n  completedAt\n  isSuspicious\n  __typename\n}\n\nfragment RegularTransactionProvider on TransactionProvider {\n  id\n  name\n  fee\n  account {\n    ...RegularTransactionProviderAccount\n    __typename\n  }\n  props {\n    ...TransactionProviderPropsFragment\n    __typename\n  }\n  limits {\n    ...ProviderLimits\n    __typename\n  }\n  paymentMethods {\n    ...TransactionPaymentMethod\n    __typename\n  }\n  __typename\n}\n\nfragment RegularTransactionProviderAccount on TransactionProviderAccount {\n  id\n  value\n  userId\n  __typename\n}\n\nfragment TransactionProviderPropsFragment on TransactionProviderPropsFragment {\n  requiredUserData {\n    ...TransactionProviderRequiredUserData\n    __typename\n  }\n  tooltip\n  __typename\n}\n\nfragment TransactionProviderRequiredUserData on TransactionProviderRequiredUserData {\n  email\n  phoneNumber\n  __typename\n}\n\nfragment ProviderLimits on ProviderLimits {\n  incoming {\n    ...ProviderLimitRange\n    __typename\n  }\n  outgoing {\n    ...ProviderLimitRange\n    __typename\n  }\n  __typename\n}\n\nfragment ProviderLimitRange on ProviderLimitRange {\n  min\n  max\n  __typename\n}\n\nfragment TransactionPaymentMethod on TransactionPaymentMethod {\n  id\n  name\n  fee\n  providerId\n  account {\n    ...RegularTransactionProviderAccount\n    __typename\n  }\n  props {\n    ...TransactionProviderPropsFragment\n    __typename\n  }\n  limits {\n    ...ProviderLimits\n    __typename\n  }\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment RegularTransactionProps on TransactionPropsFragment {\n  creatorId\n  dealId\n  paidFromPendingIncome\n  paymentURL\n  successURL\n  paymentAccount {\n    id\n    value\n    __typename\n  }\n  paymentGateway\n  alreadySpent\n  exchangeRate\n  __typename\n}\n\nfragment UserEdgeNode on UserFragment {\n  ...RegularUserFragment\n  __typename\n}"
        }

        response = await self.post(payload=payload)
        return await CreateDeal.from_dict(response["data"]["createDeal"])
    
    async def send_review(self, deal_id: str, rating: int, text: str) -> bool:
        """
        Отправляет отзыв о заказе.

        :param deal_id: str: ID сделки
        :param rating: int: Оценка, которую оставить, например 5
        :param text: str: Текст отзыва

        :return: bool: True, если отзыв успешно отправлен
        """
        payload = {
            "operationName": "createTestimonial",
            "variables": {
                "input": {
                    "dealId": deal_id,
                    "rating": rating,
                    "text": text
                }
            }, "query": "mutation createTestimonial($input: CreateTestimonialInput!) {\n  createTestimonial(input: $input) {\n    ...RegularTestimonial\n    __typename\n  }\n}\n\nfragment RegularTestimonial on Testimonial {\n  id\n  status\n  text\n  rating\n  createdAt\n  updatedAt\n  deal {\n    ...RegularItemDealProfile\n    __typename\n  }\n  creator {\n    ...RegularUserFragment\n    __typename\n  }\n  moderator {\n    ...RegularUserFragment\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  __typename\n}\n\nfragment RegularItemDealProfile on ItemDealProfile {\n  id\n  direction\n  status\n  item {\n    ...RegularItemProfile\n    __typename\n  }\n  testimonial {\n    ...TestimonialProfileFields\n    __typename\n  }\n  __typename\n}\n\nfragment RegularItemProfile on ItemProfile {\n  ...RegularMyItemProfile\n  ...RegularForeignItemProfile\n  __typename\n}\n\nfragment RegularMyItemProfile on MyItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  statusExpirationDate\n  viewsCounter\n  approvalDate\n  createdAt\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  category {\n    ...RegularGameCategoryProfile\n    __typename\n  }\n  user {\n    ...ItemUser\n    __typename\n  }\n  __typename\n}\n\nfragment PartialFile on File {\n  id\n  url\n  __typename\n}\n\nfragment RegularGameProfile on GameProfile {\n  id\n  name\n  type\n  slug\n  logo {\n    ...PartialFile\n    __typename\n  }\n  __typename\n}\n\nfragment RegularGameCategoryProfile on GameCategoryProfile {\n  id\n  slug\n  name\n  __typename\n}\n\nfragment ItemUser on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment UserEdgeNode on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment RegularForeignItemProfile on ForeignItemProfile {\n  id\n  slug\n  priority\n  name\n  price\n  rawPrice\n  approvalDate\n  createdAt\n  sellerType\n  attachment {\n    ...RegularFile\n    __typename\n  }\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  category {\n    ...RegularGameCategoryProfile\n    __typename\n  }\n  user {\n    ...ItemUser\n    __typename\n  }\n  __typename\n}\n\nfragment RegularFile on File {\n  id\n  url\n  filename\n  mime\n  __typename\n}\n\nfragment TestimonialProfileFields on TestimonialProfile {\n  id\n  status\n  text\n  rating\n  createdAt\n  __typename\n}"
        }

        response = await self.post(payload=payload)
        return bool(response["data"]["createTestimonial"])
    
    async def report_deal(self, deal_id: str, description: str, problem_type_id: str) -> bool:
        """
        Отправляет репорт на заказ.

        :param deal_id: str: ID сделки
        :param description: str: Описание проблемы
        :param problem_type_id: str: ID проблемы, можно брать из get_message_templates_report

        :return: bool: True, если отзыв успешно отправлен, вообще возвращает class reportDealProblem,
        Но я не вижу смысла в нем, поэтому возвращаю bool.
        """
        payload = {
            "operationName": "reportDealProblem",
            "variables": {
                "input": {
                    "dealId": deal_id,
                    "description": description,
                    "problemTypeId": problem_type_id
                }
            }, "query":"mutation reportDealProblem($input: ReportDealProblemInput!) {\n  reportDealProblem(input: $input) {\n    ...RegularItemDeal\n    __typename\n  }\n}\n\nfragment RegularItemDeal on ItemDeal {\n  id\n  status\n  direction\n  statusExpirationDate\n  statusDescription\n  obtaining\n  hasProblem\n  reportProblemEnabled\n  completedBy {\n    ...UserEdgeNode\n    __typename\n  }\n  props {\n    ...ItemDealProps\n    __typename\n  }\n  prevStatus\n  completedAt\n  createdAt\n  logs {\n    ...ItemLog\n    __typename\n  }\n  transaction {\n    ...ItemDealTransaction\n    __typename\n  }\n  user {\n    ...UserEdgeNode\n    __typename\n  }\n  chat {\n    ...RegularChat\n    __typename\n  }\n  item {\n    ...PartialItem\n    __typename\n  }\n  testimonial {\n    ...RegularTestimonial\n    __typename\n  }\n  obtainingFields {\n    ...GameCategoryDataFieldWithValue\n    __typename\n  }\n  commentFromBuyer\n  __typename\n}\n\nfragment UserEdgeNode on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment RegularUserFragment on UserFragment {\n  id\n  username\n  role\n  avatarURL\n  isOnline\n  isBlocked\n  rating\n  testimonialCounter\n  createdAt\n  supportChatId\n  systemChatId\n  __typename\n}\n\nfragment ItemDealProps on ItemDealProps {\n  autoConfirmPeriod\n  __typename\n}\n\nfragment ItemLog on ItemLog {\n  id\n  event\n  createdAt\n  user {\n    ...UserEdgeNode\n    __typename\n  }\n  __typename\n}\n\nfragment ItemDealTransaction on Transaction {\n  id\n  operation\n  direction\n  providerId\n  status\n  value\n  createdAt\n  paymentMethodId\n  statusExpirationDate\n  __typename\n}\n\nfragment RegularChat on Chat {\n  id\n  type\n  unreadMessagesCounter\n  bookmarked\n  isTextingAllowed\n  owner {\n    ...ChatParticipant\n    __typename\n  }\n  agent {\n    ...ChatParticipant\n    __typename\n  }\n  participants {\n    ...ChatParticipant\n    __typename\n  }\n  deals {\n    ...ChatActiveItemDeal\n    __typename\n  }\n  status\n  startedAt\n  finishedAt\n  __typename\n}\n\nfragment ChatParticipant on UserFragment {\n  ...RegularUserFragment\n  __typename\n}\n\nfragment ChatActiveItemDeal on ItemDealProfile {\n  id\n  direction\n  status\n  hasProblem\n  statusDescription\n  testimonial {\n    id\n    rating\n    __typename\n  }\n  item {\n    ...ItemEdgeNode\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  __typename\n}\n\nfragment ItemEdgeNode on ItemProfile {\n  ...MyItemEdgeNode\n  ...ForeignItemEdgeNode\n  __typename\n}\n\nfragment MyItemEdgeNode on MyItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  statusExpirationDate\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  createdAt\n  priorityPosition\n  __typename\n}\n\nfragment PartialFile on File {\n  id\n  url\n  __typename\n}\n\nfragment UserItemEdgeNode on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment ForeignItemEdgeNode on ForeignItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  user {\n    ...UserItemEdgeNode\n    __typename\n  }\n  approvalDate\n  priorityPosition\n  createdAt\n  __typename\n}\n\nfragment PartialItem on Item {\n  ...PartialMyItem\n  ...PartialForeignItem\n  __typename\n}\n\nfragment PartialMyItem on MyItem {\n  id\n  slug\n  name\n  price\n  rawPrice\n  comment\n  attachments {\n    ...RegularFile\n    __typename\n  }\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  category {\n    ...RegularGameCategory\n    __typename\n  }\n  user {\n    ...UserEdgeNode\n    __typename\n  }\n  priorityPrice\n  priority\n  dataFields {\n    ...GameCategoryDataFieldWithValue\n    __typename\n  }\n  obtainingType {\n    ...GameCategoryObtainingType\n    __typename\n  }\n  status\n  sellerType\n  createdAt\n  __typename\n}\n\nfragment RegularFile on File {\n  id\n  url\n  filename\n  mime\n  __typename\n}\n\nfragment RegularGameProfile on GameProfile {\n  id\n  name\n  type\n  slug\n  logo {\n    ...PartialFile\n    __typename\n  }\n  __typename\n}\n\nfragment RegularGameCategory on GameCategory {\n  id\n  slug\n  name\n  categoryId\n  gameId\n  obtaining\n  options {\n    ...RegularGameCategoryOption\n    __typename\n  }\n  props {\n    ...GameCategoryProps\n    __typename\n  }\n  noCommentFromBuyer\n  instructionForBuyer\n  instructionForSeller\n  useCustomObtaining\n  autoConfirmPeriod\n  autoModerationMode\n  __typename\n}\n\nfragment RegularGameCategoryOption on GameCategoryOption {\n  id\n  group\n  label\n  type\n  field\n  value\n  sequence\n  valueRangeLimit {\n    min\n    max\n    __typename\n  }\n  __typename\n}\n\nfragment GameCategoryProps on GameCategoryPropsObjectType {\n  minTestimonials\n  __typename\n}\n\nfragment GameCategoryDataFieldWithValue on GameCategoryDataFieldWithValue {\n  id\n  label\n  type\n  inputType\n  copyable\n  hidden\n  required\n  value\n  __typename\n}\n\nfragment GameCategoryObtainingType on GameCategoryObtainingType {\n  id\n  name\n  description\n  gameCategoryId\n  noCommentFromBuyer\n  instructionForBuyer\n  instructionForSeller\n  sequence\n  __typename\n}\n\nfragment PartialForeignItem on ForeignItem {\n  id\n  slug\n  name\n  price\n  rawPrice\n  comment\n  priority\n  attachments {\n    ...RegularFile\n    __typename\n  }\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  category {\n    id\n    slug\n    name\n    obtaining\n    autoConfirmPeriod\n    __typename\n  }\n  user {\n    ...UserEdgeNode\n    __typename\n  }\n  dataFields {\n    ...GameCategoryDataFieldWithValue\n    __typename\n  }\n  obtainingType {\n    ...GameCategoryObtainingType\n    __typename\n  }\n  status\n  sellerType\n  createdAt\n  __typename\n}\n\nfragment RegularTestimonial on Testimonial {\n  id\n  status\n  text\n  rating\n  createdAt\n  updatedAt\n  deal {\n    ...RegularItemDealProfile\n    __typename\n  }\n  creator {\n    ...RegularUserFragment\n    __typename\n  }\n  moderator {\n    ...RegularUserFragment\n    __typename\n  }\n  user {\n    ...RegularUserFragment\n    __typename\n  }\n  __typename\n}\n\nfragment RegularItemDealProfile on ItemDealProfile {\n  id\n  direction\n  status\n  item {\n    ...RegularItemProfile\n    __typename\n  }\n  testimonial {\n    ...TestimonialProfileFields\n    __typename\n  }\n  __typename\n}\n\nfragment RegularItemProfile on ItemProfile {\n  ...RegularMyItemProfile\n  ...RegularForeignItemProfile\n  __typename\n}\n\nfragment RegularMyItemProfile on MyItemProfile {\n  id\n  slug\n  priority\n  status\n  name\n  price\n  rawPrice\n  statusExpirationDate\n  viewsCounter\n  approvalDate\n  createdAt\n  sellerType\n  attachment {\n    ...PartialFile\n    __typename\n  }\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  category {\n    ...RegularGameCategoryProfile\n    __typename\n  }\n  user {\n    ...ItemUser\n    __typename\n  }\n  __typename\n}\n\nfragment RegularGameCategoryProfile on GameCategoryProfile {\n  id\n  slug\n  name\n  __typename\n}\n\nfragment ItemUser on UserFragment {\n  ...UserEdgeNode\n  __typename\n}\n\nfragment RegularForeignItemProfile on ForeignItemProfile {\n  id\n  slug\n  priority\n  name\n  price\n  rawPrice\n  approvalDate\n  createdAt\n  sellerType\n  attachment {\n    ...RegularFile\n    __typename\n  }\n  game {\n    ...RegularGameProfile\n    __typename\n  }\n  category {\n    ...RegularGameCategoryProfile\n    __typename\n  }\n  user {\n    ...ItemUser\n    __typename\n  }\n  __typename\n}\n\nfragment TestimonialProfileFields on TestimonialProfile {\n  id\n  status\n  text\n  rating\n  createdAt\n  __typename\n}"
        }
        response = await self.post(payload=payload)
        return response.get("data", {}).get("reportDealProblem") is not None
    
    async def get_message_templates_report(self) -> ReportMessageTemplates:
        """
        Получает возможные текста для репорта сделки, получает айди и название (и прочее)

        :return: class: ReportMessageTemplates
        """
        query = {
            "operationName": "messageTemplates",
            "variables": {
                "pagination": {"first": 20},
                "filter": {"type": "FINISHED_DEAL_PROBLEM"}
            },
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "f3d4b4053f7c758d4cd84429bbf974a27b0afed6a473ab47fbe8d13ac6bf87a2"
                }
            }
        }
        response = await self.get("https://playerok.com/graphql", payload=query)
        return ReportMessageTemplates.from_dict(response['data']['messageTemplates'])
