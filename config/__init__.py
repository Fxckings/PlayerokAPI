from __future__ import annotations

import configparser

def load_config():
    config = configparser.ConfigParser()
    config.read("config/_main.cfg")
    
    if not config.has_section("token"):
        raise ValueError("В конфиге должна быть секция [token]")
    
    if not config.has_option("token", "api_key"):
        raise ValueError("В конфиге [token] должна быть опция api_key")
    
    token = config.get("token", "api_key")
    telegram_token = config.get("telegram", "token")
    telegram_password = config.get("telegram", "password")
    read_chats = config.get("other", "read_chats")
    return token, telegram_token, telegram_password, read_chats

class Settings:
    def __init__(self, token, telegram_token, telegram_password, read_chats):
        self.token = token
        self.telegram_token = telegram_token
        self.telegram_password = telegram_password
        self.read_chats = read_chats

SETTINGS = Settings(*load_config())