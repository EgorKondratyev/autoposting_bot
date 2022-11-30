import random

from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from create_bot.bot import dp


def create_keyboard_stop_fsm() -> InlineKeyboardMarkup:
    menu_stop = InlineKeyboardMarkup(row_width=1)
    stop_button = InlineKeyboardButton('🛑STOP🛑', callback_data='stop_fsm')
    menu_stop.insert(stop_button)

    return menu_stop


# @dp.message_handler(commands='stop', state='*')
# @dp.message_handler(Text(equals=['stop'], ignore_case=True), state='*')
async def stop_fsm(message: [Message, CallbackQuery], state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        try:  # callback
            await message.answer()
            await message.message.answer("Нет запущенных процессов")
        except Exception:  # message
            await message.answer("Нет запущенных процессов")
        return

    await state.finish()
    smiles = ['🍵', '🧃', '☕', '✨']
    try:  # callback
        await message.answer()
        if random.randint(1, 20) == 19:
            await message.message.answer('✨')
        await message.message.answer(f'Операция успешно остановлена {random.choice(smiles)}')
    except Exception:  # message
        await message.answer(f'Операция успешно остановлена {random.choice(smiles)}', reply_markup=ReplyKeyboardRemove())


def register_stop_fsm_handler():
    dp.register_message_handler(stop_fsm, commands='stop', state='*')
    dp.register_message_handler(stop_fsm, Text(equals=['stop', 'Остановить❌'], ignore_case=True), state='*')
    dp.register_callback_query_handler(stop_fsm, Text(equals='stop_fsm', ignore_case=True), state='*')
