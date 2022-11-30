import asyncio
from aiogram import Bot, Dispatcher

from create_bot.storage import memory
from create_bot.config import token


bot = Bot(token=token)
main_loop = asyncio.get_event_loop()
dp = Dispatcher(bot=bot, storage=memory, loop=main_loop)
