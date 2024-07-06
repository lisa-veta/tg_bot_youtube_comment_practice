import sys
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters.command import Command
from aiogram.fsm.storage.memory import MemoryStorage
import config
from handlersaio import router
sys.path.insert(1, os.path.join(sys.path[0], 'D:/УНИВЕР/практика/проба/code/bot/database'))
from db_service import DatabaseService

db_service = None
async def main():
    global db_service
    db_service = DatabaseService(config.DB_USER, config.DB_PASSWORD)
    await db_service.create_engine()
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage(), timeout=18000000)
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())