from __future__ import annotations

from aiogram import Router

def get_handlers_router() -> Router:
    from .start import start_router
    from .auth import auth_router
    from .chat import chat_router

    router = Router()
    router.include_router(router=start_router)
    router.include_router(router=auth_router)
    router.include_router(router=chat_router)

    return router