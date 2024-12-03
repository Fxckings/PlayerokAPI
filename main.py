from __future__ import annotations

from PlayerokAPI.common.account import Account
from PlayerokAPI.updater.runner import Runner
from utils.logger import configure_logger
from loguru import logger

async def main():
    await configure_logger()
    
    async for event in Runner().listen():
        logger.info(f"Получено новое сообщение в чате: {event.chat_id}: {event.message.text}")
    
if __name__ == '__main__':
    import asyncio
    asyncio.run(main())