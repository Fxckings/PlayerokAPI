from __future__ import annotations

import json
from typing import List
import aiofiles

class TelegramBotSettings():
    def __init__(self):
        self.registered_users: List[str] = self._load_registered_users()
        self.banned_users: List[str] = self._load_banned_users()

    def _load_registered_users(self) -> List[str]:
        try:
            with open('storage/telegram/users.json', 'r') as f:
                data = json.load(f)
                return list(data.keys())
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []

    def _load_banned_users(self) -> List[str]:
        try:
            with open('storage/telegram/banned.json', 'r') as f:
                data = json.load(f)
                return list(data.keys())
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []

    async def add_registered_user(self, user_id: str, username: str) -> None:
        if user_id not in self.registered_users:
            self.registered_users.append(user_id)
            async with aiofiles.open('storage/telegram/users.json', 'r+') as f:
                try:
                    data = json.loads(await f.read())
                except json.JSONDecodeError:
                    data = {}
                data[user_id] = {'username': username}
                await f.seek(0)
                await f.write(json.dumps(data, indent=2))
                await f.truncate()

    async def add_banned_user(self, user_id: str) -> None:
        if user_id not in self.banned_users:
            self.banned_users.append(user_id)
            async with aiofiles.open('storage/telegram/banned.json', 'r+') as f:
                try:
                    data = json.loads(await f.read())
                except json.JSONDecodeError:
                    data = {}
                data[user_id] = {}
                await f.seek(0)
                await f.write(json.dumps(data, indent=2))
                await f.truncate()

    async def is_user_registered(self, user_id: str) -> bool:
        return user_id in self.registered_users

    async def is_banned(self, user_id: str) -> bool:
        return user_id in self.banned_users
    
    async def get_registered_users(self) -> List[str]:
        return self.registered_users