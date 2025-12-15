import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from datemate.config import load_settings
from datemate.domain.db import create_engine, init_db
from datemate.tgbot.functional import Phrases
from datemate.tgbot.handlers.matchmaking import router as matchmaking_router
from datemate.tgbot.handlers.registration import router as registration_router
from datemate.tgbot.middlewares.db import DbSessionMiddleware
from datemate.tgbot.middlewares.interface import InterfaceMiddleware


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()
    phrases = Phrases()

    engine = create_engine(settings.database_url)
    session_factory = await init_db(engine)

    redis = Redis.from_url(settings.redis_url)
    # storage = RedisStorage(redis=redis)
    storage = MemoryStorage()

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)
    dp.include_router(registration_router)
    dp.include_router(matchmaking_router)

    dp.message.middleware(DbSessionMiddleware(session_factory))
    dp.callback_query.middleware(DbSessionMiddleware(session_factory))
    dp.message.middleware(InterfaceMiddleware(phrases))
    dp.callback_query.middleware(InterfaceMiddleware(phrases))

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot, phrases=phrases)
    finally:
        # await redis.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
