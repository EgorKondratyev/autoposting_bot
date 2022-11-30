import random
import traceback

from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

from create_bot.bot import dp
from databases.client import ChannelDB, DonorPostDB
from handlers.stop_fsm import create_keyboard_stop_fsm
from keyboards.inline.donor_posts import create_type_time_keyboard, create_keyboard_channels, \
    create_keyboard_tagged_channels, create_interval_keyboard, delete_post_keyboard
from keyboards.reply.donor_post_keyboard import confirmation_donor_posts_menu
from log.create_logger import logger
from states.donor_posts import DonorPostsFSM
from utils.generate_random_tag import generate_random_tag_md5
from utils.publication_post_donor import publication_post_donor


# @dp.callback_query_handler(Text(equals='start_post_in_turn'), state=None)
async def get_channels(callback: CallbackQuery):
    await callback.answer()
    channel_db = ChannelDB()
    channels = channel_db.get_channels_by_user_id(user_id=callback.from_user.id)
    if channels:
        await callback.message.answer('Ты находишься в меню <i>"посты из донора"</i>\n\n'
                                      '<b>Выбери канал(-ы) для публикации постов:</b> \n\n'
                                      'Для остановки воспользуйся командой "/stop"',
                                      reply_markup=await create_keyboard_channels(channels=channels),
                                      parse_mode='html')
        await DonorPostsFSM.get_channels.set()
    else:
        await callback.message.answer('На данный момент у тебя не добавлено ни одного канала!')


# @dp.callback_query_handler(Text(startswith='channels_donor_'), state=DonorPostsFSM.get_channels)
async def set_channels(callback: CallbackQuery, state: FSMContext):
    """
    Пользователь выбирает каналы, в которые будут опубликовываться посты
    :param callback:
    :param state:
    :return:
    """
    await callback.answer('Канал успешно выбран')
    data = str(callback.data[len('channels_'):]).split('_')
    channel_id = data[1]

    async with state.proxy() as data:
        if data.get('channels_id'):
            if channel_id not in data['channels_id']:
                data['channels_id'].append(channel_id)
            else:
                data['channels_id'].remove(channel_id)
        else:
            data['channels_id'] = [channel_id]
        channels_tagged = data['channels_id']

    channel_db = ChannelDB()
    channels = channel_db.get_channels_by_user_id(user_id=callback.from_user.id)

    await callback.message.edit_reply_markup(reply_markup=await create_keyboard_tagged_channels(channels=channels,
                                                                                                channels_tagged=channels_tagged
                                                                                                ))


# @dp.callback_query_handler(Text(startswith='channels_tagged_next_for_donor'), state=DonorPostsFSM.get_channels)
async def get_type_time(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer('<b>Выбери тип интервала:</b> \n\n',
                                  reply_markup=await create_type_time_keyboard(),
                                  parse_mode='html')
    await DonorPostsFSM.get_type_time.set()


# @dp.callback_query_handler(Text(startswith='type_time_'), state=DonorPostsFSM.get_type_time)
async def get_interval(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Тип интервала успешно выбран')
    type_time = callback.data[len('type_time_'):]
    async with state.proxy() as data:
        data['type_time'] = type_time
    text_type_time = '<b>Выбери интервал</b>, с которым будут публиковаться посты: \n\n'
    if type_time == 'Минуты':
        text_type_time += 'Раз в 5 минут, каждые 10 минут'
    elif type_time == 'Часы':
        text_type_time += 'Раз в 2 часа, каждые 3 часа'
    else:
        text_type_time += 'Раз в день, hаз в 3 дня'
    await callback.message.edit_text(text_type_time,
                                     reply_markup=await create_interval_keyboard(type_time),
                                     parse_mode='html')
    await DonorPostsFSM.get_interval.set()


# @dp.callback_query_handler(Text(startswith='interval_'), state=DonorPostsFSM.get_interval)
async def get_posts(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Интервал успешно выбран')
    async with state.proxy() as data:
        data['interval'] = callback.data[len('interval_'):]
        data['tag'] = await generate_random_tag_md5()

    await callback.message.answer('<b>Перешли из канала донора посты:</b> \n\n'
                                  'Дождись загрузки всех медиа-файлов, после этого нажми на кнопку сохранить',
                                  parse_mode='html', reply_markup=create_keyboard_stop_fsm())
    await callback.message.answer('<i>Будь крайне внимателен с коллекциями медиа! Если в посте содержится '
                                  'более чем 1 картинка или же видео, то это будет считаться за коллекцию. Каждый '
                                  'медиа-файл в коллекции бот считает как за отдельное сообщение. Соответственно '
                                  'пост из 5 медиа-файлов будет интерпретирован как 5 постов</i>',
                                  parse_mode='html', reply_markup=confirmation_donor_posts_menu)
    await DonorPostsFSM.get_posts.set()


# @dp.message_handler(state=DonorPostsFSM.get_posts, content_types='any')
async def set_posts(message: Message, state: FSMContext):
    if message.forward_from_chat:
        print(message)
        try:
            donor_post_db = DonorPostDB()
            if message.photo:
                if message.caption is not None:
                    text_user = message.caption
                else:
                    text_user = ''
                async with state.proxy() as data:
                    tag = data['tag']

                donor_post_db.add_post(tag=tag, photo_id=message.photo[-1].file_id, content=text_user,
                                       unique_id_media_file=message.photo[-1].file_unique_id,
                                       user_id=message.from_user.id)

                text_confirm_post = f'{text_user}'
                await message.answer_photo(photo=message.photo[-1].file_id,
                                           caption=text_confirm_post, parse_mode='html',
                                           reply_markup=await delete_post_keyboard())

            elif message.video:
                if message.caption is not None:
                    text_user = message.caption
                else:
                    text_user = ''
                async with state.proxy() as data:
                    tag = data['tag']

                donor_post_db.add_post(tag=tag, video_id=message.video.file_id, content=text_user,
                                       unique_id_media_file=message.video.file_unique_id,
                                       user_id=message.from_user.id)

                text_confirm_post = f'{text_user}'
                await message.answer_video(video=message.video.file_id,
                                           caption=text_confirm_post, parse_mode='html',
                                           reply_markup=await delete_post_keyboard())

            elif message.animation:
                if message.caption is not None:
                    text_user = message.caption
                else:
                    text_user = ''
                async with state.proxy() as data:
                    tag = data['tag']

                donor_post_db.add_post(tag=tag, animation_id=message.animation.file_id, content=text_user,
                                       unique_id_media_file=message.animation.file_unique_id,
                                       user_id=message.from_user.id)

                text_confirm_post = f'{text_user}'
                await message.answer_animation(animation=message.animation.file_id,
                                               caption=text_confirm_post, parse_mode='html',
                                               reply_markup=await delete_post_keyboard())
            elif message.video_note:
                async with state.proxy() as data:
                    tag = data['tag']

                donor_post_db.add_post(tag=tag, animation_id=message.video_note.file_id,
                                       unique_id_media_file=message.video_note.file_unique_id,
                                       user_id=message.from_user.id)

                await message.answer_video_note(video_note=message.video_note.file_id,
                                                reply_markup=await delete_post_keyboard())

            elif message.text is not None:
                text_user = message.text
                async with state.proxy() as data:
                    tag = data['tag']

                donor_post_db.add_post(user_id=message.from_user.id, tag=tag, content=text_user)

                text_confirm_post = f'{text_user}'
                await message.answer(text_confirm_post, parse_mode='html',
                                     reply_markup=await delete_post_keyboard())
        except Exception:
            logger.warning('...')
            traceback.print_exc()
    else:
        await message.answer('Сообщение должно пересылаться из чата',
                             reply_markup=create_keyboard_stop_fsm())


# @dp.callback_query_handler(Text(equals='delete_post'), state=DonorPostsFSM.get_posts)
async def delete_donor_post_before_publication(callback: CallbackQuery):
    donor_post_db = DonorPostDB()

    if callback.message.photo:
        donor_post_db.del_post_by_unique_id_file(unique_id_media_file=callback.message.photo[-1].file_unique_id)
    elif callback.message.video:
        donor_post_db.del_post_by_unique_id_file(unique_id_media_file=callback.message.video.file_unique_id)
    elif callback.message.animation:
        donor_post_db.del_post_by_unique_id_file(unique_id_media_file=callback.message.animation.file_unique_id)
    elif callback.message.video_note:
        donor_post_db.del_post_by_unique_id_file(unique_id_media_file=callback.message.video_note.file_unique_id)
    else:
        donor_post_db.del_post_by_content(content=callback.message.text)

    await callback.message.delete()


# @dp.message_handler(Text(equals='Продолжить🚀'), state=DonorPostsFSM.get_posts)
async def publication(message: Message, state: FSMContext):
    async with state.proxy() as data:
        channels_id = data['channels_id']
        type_time = data['type_time']
        interval = data['interval']
        tag = data['tag']

    post_donor_db = DonorPostDB()
    posts = post_donor_db.get_posts_by_tag(tag=tag)
    if posts:
        await state.finish()
        messages = ['Комфортной работы🍫', 'Приятной работы🧃']
        await message.answer('🚀')
        await message.answer(f'Все посты успешно добавлены в очередь!\n\n'
                             f'Количество добавленных постов в очередь: <b>{len(posts)}</b>\n\n'
                             f'<i>{random.choice(messages)}</i>',
                             parse_mode='html',
                             reply_markup=ReplyKeyboardRemove())
        await publication_post_donor(tag=tag, user_id=message.from_user.id, type_time=type_time,
                                     interval=interval, channels=channels_id)
    else:
        await message.answer('Прежде чем нажимать кнопку "Продолжить", '
                             '<b>ты должен отправить мне хотя бы 1 пост</b>!\n\n'
                             'Если ты хочешь остановить процесс, то нажми на кнопку "Остановить❌"',
                             parse_mode='html')


def register_handlers_donor_posts():
    dp.register_callback_query_handler(get_channels, Text(equals='start_post_in_turn'), state=None)
    dp.register_callback_query_handler(set_channels, Text(startswith='channels_donor_'),
                                       state=DonorPostsFSM.get_channels)
    dp.register_callback_query_handler(get_type_time, Text(startswith='channels_tagged_next_for_donor'),
                                       state=DonorPostsFSM.get_channels)
    dp.register_callback_query_handler(get_interval, Text(startswith='type_time_'), state=DonorPostsFSM.get_type_time)
    dp.register_callback_query_handler(get_posts, Text(startswith='interval_'), state=DonorPostsFSM.get_interval)
    dp.register_message_handler(publication, Text(equals='Продолжить🚀'), state=DonorPostsFSM.get_posts)
    dp.register_message_handler(set_posts, state=DonorPostsFSM.get_posts, content_types='any')
    dp.register_callback_query_handler(delete_donor_post_before_publication,
                                       Text(equals='delete_post'), state=DonorPostsFSM.get_posts)
