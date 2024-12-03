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
    return token

token = load_config()
