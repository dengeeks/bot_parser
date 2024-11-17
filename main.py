import asyncio

from config import dp, bot
from handlers import setup_routers


# from handlers import setup_routers
# from database.a_db import AsyncDatabase


async def main():
    # db = AsyncDatabase()
    # await db.create_tables()
    router = setup_routers()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    # запуск бота
    asyncio.run(main())
