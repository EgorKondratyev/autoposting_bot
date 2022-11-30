from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

from create_bot.bot import dp
from handlers.stop_fsm import create_keyboard_stop_fsm
from databases.client import ChannelDB
from states.delete_channel import DeleteChannelFSM


# @dp.callback_query_handler(Text(equals='start_delete_channel'), state=None)
async def get_channel(callback: CallbackQuery):
    await callback.answer('Считываю базу данных...')
    channel_db = ChannelDB()
    channels = channel_db.get_channels_by_user_id(user_id=callback.from_user.id)
    if channels:
        channels_text = '<i>Все имеющиеся каналы на данный момент:</i> \n\n'
        for i, attribute in enumerate(channels, 1):
            channel_id = attribute[0]
            channel_name = attribute[1]
            channels_text += f'<b>{i}. ID канала:</b> <code>{channel_id}</code> ' \
                             f'<b>| Название канала:</b> {channel_name}\n'

        channels_text += '\nВведи ID канала, который требуется удалить: '
        await callback.message.answer(channels_text, reply_markup=create_keyboard_stop_fsm(), parse_mode='html')
        await DeleteChannelFSM.get_id_channel.set()
    else:
        await callback.message.answer('На данный момент не было добавлено ни одного канала')


# @dp.message_handler(state=DeleteChannelFSM.get_id_channel)
async def delete_channel(message: Message, state: FSMContext):
    if message.text.startswith('-100'):
        if message.text[1:].isdigit():
            channel_db = ChannelDB()
            if channel_db.exists_user(user_id=message.from_user.id, channel_id=message.text):
                channel_db.delete_channel(user_id=message.from_user.id, channel_id=message.text)
                await message.answer('Канал успешно удалён')
                await state.finish()
            else:
                await message.answer('Канала с подобным ID нет в базе данных!', reply_markup=create_keyboard_stop_fsm())
        else:
            await message.answer('ID может состоять только из цифр!', reply_markup=create_keyboard_stop_fsm())
    else:
        await message.answer('❌<b>Внимание!</b> Нарушен синтаксис ввода ID канала❌\n'
                             'ID должен начинаться с -100. <i>Подробнее о синтаксисе ввода ID канала в '
                             '"/help"</i>\n\n', reply_markup=create_keyboard_stop_fsm(), parse_mode='html')


def register_handlers_delete_channel():
    dp.register_callback_query_handler(get_channel, Text(equals='start_delete_channel'), state=None)
    dp.register_message_handler(delete_channel, state=DeleteChannelFSM.get_id_channel)
