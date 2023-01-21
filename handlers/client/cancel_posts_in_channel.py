from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

from create_bot.bot import dp
from databases.client import CheckDonorPostDB, ChannelDB, DonorPostDB
from handlers.stop_fsm import create_keyboard_stop_fsm
from states.cancel_posts_in_channel_state import CancelPostChannelFSM


# @dp.callback_query_handler(Text(equals='start_cancel_donor_posts_channel'))
async def get_id_channel(callback: CallbackQuery):
    await callback.answer()
    text = 'Ты зашел в меню по отмене постов из конкретного канала\n\n' \
           'Выбери один из каналов и напиши его ID ниже: \n\n'
    channel_db = ChannelDB()
    channels = channel_db.get_channels_by_user_id(user_id=callback.from_user.id)
    for i, attribute in enumerate(channels, 1):
        channel_id = attribute[0]
        channel_name = attribute[1]
        text += f'{i}. ID: <code>{channel_id}</code> | Название: <b>{channel_name}</b>\n'

    await callback.message.answer(text, parse_mode='html')
    await CancelPostChannelFSM.get_id_channel.set()


@dp.message_handler(state=CancelPostChannelFSM.get_id_channel)
async def confirm_cancel_posts_in_channel(message: Message, state: FSMContext):
    if message.text.startswith('-'):
        channel_id = int(message.text)
        await message.answer(f'Если ты уверен, что хочешь удалить все запланированные посты в текущем канале, то '
                             f'напиши "<code>УДАЛИТЬ ПОСТЫ</code>"\n\n'
                             f'Для отмены напиши любой другой символ', parse_mode='html')

        async with state.proxy() as data:
            data['channel_id'] = channel_id

        await CancelPostChannelFSM.confirm.set()
    else:
        await message.answer('ID канала должен начинаться со знака "-"')


@dp.message_handler(state=CancelPostChannelFSM.confirm)
async def delete_posts_in_channel(message: Message, state: FSMContext):
    if message.text == 'УДАЛИТЬ ПОСТЫ':
        async with state.proxy() as data:
            channel_id = data['channel_id']
        check_donor_post_db = CheckDonorPostDB()
        donor_post_db = DonorPostDB()
        posts = donor_post_db.get_all_pk_by_user_id(user_id=message.from_user.id)
        for attribute in posts:
            pk = attribute[0]
            check_donor_post_db.add(user_id=message.from_user.id, channel_id=channel_id, pk_donor_posts=pk)
        await state.finish()
        await message.answer('Все посты успешно сняты с данного канала')
    else:
        await state.finish()
        await message.answer('Действие успешно отменено')


def register_cancel_posts_channel():
    dp.register_callback_query_handler(get_id_channel, Text(equals='start_cancel_donor_posts_channel'))
