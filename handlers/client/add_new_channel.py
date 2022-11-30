import random

from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import NeedAdministratorRightsInTheChannel, ChatNotFound

from create_bot.bot import dp, bot
from databases.client import ChannelDB
from handlers.stop_fsm import create_keyboard_stop_fsm
from keyboards.inline.add_new_channel import confirm_add_channel_menu
from states.add_new_channel import AddNewChannelFSM
from log.create_logger import logger


# @dp.callback_query_handler(Text(equals='start_add_channel'))
async def get_id_channel(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(f'Ты находишься в меню "Добавления канала"!\n\n'
                                  f'Отправь мне <b>ID</b> канала: ',
                                  reply_markup=create_keyboard_stop_fsm(), parse_mode='html')
    await AddNewChannelFSM.get_group_id.set()


# @dp.message_handler(state=AddNewChannelFSM.get_group_id)
async def check_and_confirm_register_channel(message: Message, state: FSMContext):
    """
    Обработчик проверяющий корректность ID канала, имеются ли соответсвующее права у бота в данном канале, если ОК, то
    бот просит подтверждения на добавление в базу данных нового канала для конкретного пользователя.
    :param message:
    :param state:
    :return:
    """
    try:

        if message.text.startswith('-100'):
            if message.text[1:].isdigit():
                chat = await bot.get_chat(chat_id=message.text)
                test_message = await bot.send_message(chat_id=message.text,
                                                      text='Съешь эти мягкие французские булочки да выпей чаю',
                                                      disable_notification=True)
                await test_message.delete()
                async with state.proxy() as data:
                    data['chat_id'] = message.text
                    data['chat_name'] = chat.title

                text_confirm = f'Данный канал успешно прошел все этапы подготовки и готов к добавлению!\n\n' \
                               f'Осталось лишь <i>кликнуть</i> на кнопку ниже, чтобы добавить канал <b>{chat.title}</b>'
                await AddNewChannelFSM.confirm.set()
                await message.answer(text_confirm, reply_markup=confirm_add_channel_menu, parse_mode='html')
            else:
                await message.answer('ID может состоять только из цифр!', reply_markup=create_keyboard_stop_fsm())
        else:
            await message.answer('❌<b>Внимание!</b> Нарушен синтаксис ввода ID канала❌\n'
                                 'ID должен начинаться с -100. <i>Подробнее о синтаксисе ввода ID канала в '
                                 '"/help"</i>\n\n'
                                 'Если желаешь остановить процесс добавления канала, то воспользуйся командой '
                                 '"/stop"', reply_markup=create_keyboard_stop_fsm(), parse_mode='html')

    except NeedAdministratorRightsInTheChannel:
        await message.answer('Для выполнение базового функционала бота необходимы следующие разрешения: ',
                             reply_markup=create_keyboard_stop_fsm())
        with open('media/photo/m4LN8p01ifA.jpg', 'rb') as photo_file:
            await message.answer_photo(photo_file)
    except ChatNotFound:
        await message.answer('По каким-то причинам данный канал не был найден в переписках бота, удостоверься, что '
                             'добавил бота в нужный тебе канал\n'
                             'Также стоит проверить на то, правильно ли ты ввёл ID данного канала и совпадает ли он '
                             'с тем ID, который ты получил от бота @getmyid_bot',
                             reply_markup=create_keyboard_stop_fsm())
    except Exception as ex:
        await message.answer('По каким-то причинам данный канал не был найден в переписках бота, удостоверься, что '
                             'добавил бота в нужный тебе канал\n'
                             'Также стоит проверить на то, правильно ли ты ввёл ID данного канала и совпадает ли он '
                             'с тем ID, который ты получил от бота @getmyid_bot',
                             reply_markup=create_keyboard_stop_fsm())
        if hasattr(ex, 'message'):
            logger.warning(f'Возникла ошибка в обработчике check_and_confirm_register_channel у пользователя '
                           f'{message.from_user.id}\n\n'
                           f'{ex.message}')
        else:
            logger.warning(f'Возникла ошибка в обработчике check_and_confirm_register_channel у пользователя '
                           f'{message.from_user.id}\n\n'
                           f'{ex}')


# @dp.callback_query_handler(Text(startswith='add_channel_'))
async def add_new_channel(callback: CallbackQuery, state: FSMContext):
    data = callback.data[len('add_channel_'):]
    if data == 'confirm':
        await callback.answer('Начинаю добавление нового канала в базу данных...')

        async with state.proxy() as data:
            chat_id = data['chat_id']
            chat_name = data['chat_name']
        await state.finish()

        channel_db = ChannelDB()
        if not channel_db.exists_user(user_id=callback.from_user.id, channel_id=chat_id):
            job = ['Приятной работы...☕', 'Комфортной работы...🍩', 'Успешной работы!💸']
            channel_db.add_user(user_id=callback.from_user.id, channel_id=chat_id, channel_name=chat_name)
            await callback.message.answer(f'Канал был успешно добавлен!\n\n'
                                          f'{random.choice(job)}')
        else:
            await callback.message.answer('Данный канал уже зарегистрирован на твоем аккаунте!')
    else:
        await state.finish()
        await callback.answer()
        await callback.message.answer('Добавление канала успешно остановлено')


def register_handlers_add_new_channel():
    dp.register_callback_query_handler(get_id_channel, Text(equals='start_add_channel'))
    dp.register_message_handler(check_and_confirm_register_channel, state=AddNewChannelFSM.get_group_id)
    dp.register_callback_query_handler(add_new_channel, Text(startswith='add_channel_'), state=AddNewChannelFSM.confirm)
