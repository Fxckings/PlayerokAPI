from __future__ import annotations

from typing import List
from PlayerokAPI.types.chats import Message

class BaseEvent:
    pass

class NewMessageEvent(BaseEvent):
    def __init__(self, chat_id: str, message: Message):
        super().__init__()
        self.chat_id = chat_id
        self.message = message

class MessageEventsStack:
    def __init__(self):
        self.stack: List[NewMessageEvent] = []
    
    def add_event(self, event: NewMessageEvent):
        self.stack.append(event)
    
    def get_stack(self) -> List[dict]:
        return [event.to_dict() for event in self.stack]