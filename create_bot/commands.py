from create_bot.bot import bot
from aiogram.types.bot_command import BotCommand


async def set_command():
    commands = [
        BotCommand(command='start', description='Вызов стартовых функций'),
        BotCommand(command='help', description='Справочник'),
        BotCommand(command='stop', description='Использовать если застрял')
    ]
    await bot.set_my_commands(commands)
