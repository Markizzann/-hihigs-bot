import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN
from handlers import all_routers, set_my_commands, set_up_logger
from script.db import async_create_table

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_routers(*all_routers)

    set_up_logger(fname=__name__)

    await async_create_table()
    await set_my_commands(bot)

    logging.info("Script bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("End Script!")
