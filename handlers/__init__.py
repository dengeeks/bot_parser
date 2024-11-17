# Собираем все роутеры проекта

from aiogram import Router


def setup_routers() -> Router:
    from . import (
        start,
        parse,
    )
    router = Router()
    router.include_router(start.router)
    router.include_router(parse.router)
    return router
