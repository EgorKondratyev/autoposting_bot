import asyncio

from aiogram import executor
from create_bot.bot import dp
from databases.client import PostDB, DonorPostDB, CheckDonorPostDB
from log.create_logger import logger
from utils.create_cron import msh


async def start(_):
    asyncio.create_task(msh.start())
    logger.debug('Бот успешно запущен!')


async def end(_):
    # Чистка всех постов, ибо все задачи хранятся в буфере, а значит, после отключения бота нет смысла их держать в БД
    PostDB().clear_table()
    DonorPostDB().clear_table()
    CheckDonorPostDB().clear_table()
    logger.debug('Бот успешно отключен!')


if __name__ == '__main__':
    from handlers import register_handlers
    executor.start_polling(dispatcher=dp, skip_updates=True, on_startup=start, on_shutdown=end)
