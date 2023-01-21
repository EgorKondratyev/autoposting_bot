import random
import re
import traceback

from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import BadRequest
from async_cron.job import CronJob

from create_bot.bot import dp
from databases.client import ChannelDB, PostDB, IndividualPostDB
from handlers.stop_fsm import create_keyboard_stop_fsm
from keyboards.inline.individual_post import create_keyboard_channels, create_keyboard_time_24_hours, \
    create_keyboard_tagged_channels, create_keyboard_day, create_confirm_post, create_url_menu, create_button_for_post, \
    create_interval_auto_delete, create_type_interval_auto_delete
from keyboards.inline.start_command import create_start_menu
from states.individual_post import IndividualPostFSM
from log.create_logger import logger
from utils.publication_post_individual import publication_post, send_album
from utils.generate_random_tag import generate_random_tag_md5
from utils.create_cron import msh


# @dp.callback_query_handler(Text(equals='start_create_post'))
async def start_create_post(callback: CallbackQuery):
    """
    Начало формирования самостоятельного поста. Данный обработчик позволяет получить канал, в который произойдет
    публикация поста.
    :param callback:
    :return:
    """
    await callback.answer()
    channel_db = ChannelDB()
    channels = channel_db.get_channels_by_user_id(user_id=callback.from_user.id)
    if channels:
        channels_menu = await create_keyboard_channels(channels=channels, user_id=callback.from_user.id)
        await callback.message.answer('Ты находишься в меню <i>"отложенного поста"</i>\n\n'
                                      'Выбери канал(-ы) (ниже представлен список всех каналов, которые ты ранее '
                                      'зарегистрировал): \n\n'
                                      'Для остановки воспользуйся командой "/stop"',
                                      reply_markup=channels_menu, parse_mode='html')
        await IndividualPostFSM.get_channel.set()
    else:
        await callback.message.answer('На данный момент у тебя не добавлено ни одного канала!')


# @dp.callback_query_handler(Text(equals='channels_tagged_back'), state=IndividualPostFSM.get_time)
async def set_channels_back(callback: CallbackQuery, state: FSMContext):
    """
    Возвращение из get_time handler в set_channel handler
    :param callback:
    :param state:
    :return:
    """
    async with state.proxy() as data:
        if data.get('channels_id'):
            del data['channels_id']

    await callback.answer()
    channel_db = ChannelDB()
    channels = channel_db.get_channels_by_user_id(user_id=callback.from_user.id)
    if channels:
        await callback.message.answer('Ты находишься в меню <i>"посты из донора"</i>\n\n'
                                      '<b>Выбери канал(-ы) для публикации постов:</b> \n\n'
                                      'Для остановки воспользуйся командой "/stop"',
                                      reply_markup=await create_keyboard_channels(channels=channels,
                                                                                  user_id=callback.from_user.id),
                                      parse_mode='html')
        await IndividualPostFSM.get_channel.set()
    else:
        await callback.message.answer('На данный момент у тебя не добавлено ни одного канала!')


# @dp.callback_query_handler(Text(startswith='channels_'), state=IndividualPostFSM.get_channel)
async def set_channels(callback: CallbackQuery, state: FSMContext):
    """
    Пользователь выбирает каналы, в которые будут опубликовываться посты
    :param callback:
    :param state:
    :return:
    """
    await callback.answer('Канал успешно выбран')
    data = str(callback.data[len('channels_'):]).split('_')
    channel_id = data[0]

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
                                                                                                user_id=callback.from_user.id,
                                                                                                channels_tagged=channels_tagged
                                                                                                ))


# @dp.callback_query_handler(Text(equals='channels_tagged_next'), state=IndividualPostFSM.get_channel)
async def get_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Канал успешно выбран')
    data = str(callback.data[len('channels_'):]).split('_')
    channel_id = data[0]

    async with state.proxy() as data:
        data['channel_id'] = channel_id

    await callback.message.edit_text('Отлично!<b>Выбери время</b>, когда будет опубликован пост или же напиши '
                                     'время вручную (Пример: 14:25, 17:03): \n\n'
                                     'Для остановки воспользуйся командой "/stop"',
                                     reply_markup=await create_keyboard_time_24_hours(),
                                     parse_mode='html')
    await IndividualPostFSM.get_time.set()


# @dp.callback_query_handler(Text(equals='time_back'), state=IndividualPostFSM.get_day)
async def get_time_back(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text('Отлично!<b>Выбери время</b>, когда будет опубликован пост или же напиши '
                                     'время вручную (Пример: 14:25, 17:03): \n\n'
                                     'Для остановки воспользуйся командой "/stop"',
                                     reply_markup=await create_keyboard_time_24_hours(),
                                     parse_mode='html')
    await IndividualPostFSM.get_time.set()


# @dp.callback_query_handler(Text(startswith='time_'), state=IndividualPostFSM.get_time)
async def get_day(callback: CallbackQuery, state: FSMContext):
    """
    Если пользователь выбрал время по кнопке, то создаем данный обработчик для выбора для публикации.
    :param callback:
    :param state:
    :return:
    """
    time = callback.data[5:]
    async with state.proxy() as data:
        data['time'] = time
    await callback.answer('Время успешно установлено')
    words = ['Замечательно🍵', 'Отлично☕️', 'Супер🍵']

    await callback.message.answer(f'{random.choice(words)}! <i>Выбрано время {time}</i>\n\n'
                                  f'<b>Выбери день</b>, в который будет опубликован пост: \n\n'
                                  f'Примечание*, если выбрать "Сегодня" и при этом время будет выходить за рамки этого '
                                  f'дня, то пост будет опубликован завтра',
                                  reply_markup=await create_keyboard_day(), parse_mode='html')
    await IndividualPostFSM.get_day.set()


# @dp.message_handler(state=IndividualPostFSM.get_time)
async def get_day_message(message: Message, state: FSMContext):
    """
    Если пользователь время ввёл вручную, то создаем данный обработчик для выбора для публикации.
    :param message:
    :param state:
    :return:
    """
    time = message.text
    # проверка синтаксиса времени от 00:00 до 19:59
    check_time_first = re.findall(r'[0-1][\d]:[0-5][\d]', time)
    # проверка синтаксиса времени от 20:00 до 23:59
    check_time_second = re.findall(r"2[0-3]:[0-5][\d]", time)
    if check_time_first or check_time_second:
        async with state.proxy() as data:
            data['time'] = time
        words = ['Замечательно🍵', 'Отлично☕️', 'Супер🍵']
        await message.answer(f'{random.choice(words)}! <i>Выбрано время {time}</i>\n\n'
                             f'<b>Выбери день</b>, в который будет опубликован пост: \n\n'
                             f'Примечание*, если выбрать "Сегодня" и при этом время будет выходить за рамки этого '
                             f'дня, то пост будет опубликован завтра',
                             reply_markup=await create_keyboard_day(), parse_mode='html')
        await IndividualPostFSM.get_day.set()
    else:
        await message.answer('Нарушен синтаксис ввода времени\n\n'
                             'Пример: 22:45', reply_markup=create_keyboard_stop_fsm())


# @dp.callback_query_handler(Text(equals='day_back'), state=IndividualPostFSM.get_button)
async def get_day_back(callback: CallbackQuery):
    await callback.answer()
    words = ['Замечательно🍵', 'Отлично☕️', 'Супер🍵']
    await callback.message.answer(f'{random.choice(words)}!\n\n'
                                  f'<b>Выбери день</b>, в который будет опубликован пост: \n\n'
                                  f'Примечание*, если выбрать "Сегодня" и при этом время будет выходить за рамки этого '
                                  f'дня, то пост будет опубликован завтра',
                                  reply_markup=await create_keyboard_day(), parse_mode='html')
    await IndividualPostFSM.get_day.set()


# @dp.callback_query_handler(Text(startswith='day_'), state=IndividualPostFSM.get_day)
async def get_button_for_post(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    day = callback.data[4:]
    async with state.proxy() as data:
        data['day'] = day
        data['tag'] = await generate_random_tag_md5()

    await callback.message.edit_text('Хочешь ли добавить кнопку к своему посту?', reply_markup=create_url_menu)
    await IndividualPostFSM.get_button.set()


# @dp.callback_query_handler(Text(startswith='create_url_'), state=IndividualPostFSM.get_button)
async def check_create_button(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик проверяет на то, хочет ли пользователь установить кнопку на свой пост, если да, то запрашиваем
    текст, который будет на кнопке.
    :param callback:
    :param state:
    :return:
    """
    check_create = callback.data[len('create_url_'):]
    if check_create == 'yes':
        await callback.message.edit_text('Какое название будет у кнопки, которая будет прикреплена к посту: ')
        await IndividualPostFSM.get_text_for_button.set()
    else:
        await callback.message.edit_text('Отправь пост из канала донора или спроектируй его сам (можно отправлять '
                                         'любые форматы: фото, видео, обычный текст):\n\n'
                                         'Для остановки: "/stop"', reply_markup=create_keyboard_stop_fsm())
        await IndividualPostFSM.get_post.set()


# @dp.message_handler(state=IndividualPostFSM.get_text_for_button)
async def get_url_for_button(message: Message, state: FSMContext):
    if len(message.text) < 50:
        async with state.proxy() as data:
            data['text_button'] = message.text
        await message.answer('Отлично☕️\n\n'
                             'Введи url для кнопки: ')
        await IndividualPostFSM.get_url_for_button.set()
    else:
        await message.answer('В названии кнопки не может быть более 50 символов!\n\n'
                             'Попробуй ещё раз или нажми кнопку стоп😴',
                             reply_markup=create_keyboard_stop_fsm())


# @dp.message_handler(state=IndividualPostFSM.get_url_for_button)
async def get_post(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['url_button'] = message.text

    await message.answer('Отправь пост из канала донора или спроектируй его сам (можно отправлять '
                         'любые форматы: фото, видео, обычный текст):\n\n'
                         'Для остановки: "/stop"', reply_markup=create_keyboard_stop_fsm())
    await IndividualPostFSM.get_post.set()


# @dp.message_handler(state=IndividualPostFSM.get_post, content_types='any')
async def confirm_create_post(message: Message, state: FSMContext):
    try:
        individual_post_db = IndividualPostDB()
        if message.photo:
            if message.caption is not None:
                if message.html_text:
                    text_user = message.html_text
                else:
                    text_user = message.caption
            else:
                text_user = ''
            async with state.proxy() as data:
                data['text'] = text_user
                data['photo'] = message.photo[-1].file_id
                tag = data['tag']

            if message.media_group_id:
                individual_post_db.add_post(tag=tag, photo_id=message.photo[-1].file_id, content=text_user)

            text_confirm_post = f'{text_user}'
            await message.answer_photo(photo=message.photo[-1].file_id,
                                       caption=text_confirm_post, parse_mode='html',
                                       reply_markup=await create_confirm_post())

        elif message.video:
            if message.caption is not None:
                if message.html_text:
                    text_user = message.html_text
                else:
                    text_user = message.caption
            else:
                text_user = ''
            async with state.proxy() as data:
                data['text'] = text_user
                data['video'] = message.video.file_id
                tag = data['tag']

            if message.media_group_id:
                individual_post_db.add_post(tag=tag, photo_id=message.video.file_id, content=text_user)

            text_confirm_post = f'{text_user}'
            await message.answer_video(video=message.video.file_id,
                                       caption=text_confirm_post, parse_mode='html',
                                       reply_markup=await create_confirm_post())

        elif message.animation:
            if message.caption is not None:
                if message.html_text:
                    text_user = message.html_text
                else:
                    text_user = message.caption
            else:
                text_user = ''
            async with state.proxy() as data:
                data['text'] = text_user
                data['animation'] = message.animation.file_id

            text_confirm_post = f'{text_user}'
            await message.answer_animation(animation=message.animation.file_id,
                                           caption=text_confirm_post, parse_mode='html',
                                           reply_markup=await create_confirm_post())

        elif message.text is not None:
            if message.html_text:
                text_user = message.html_text
            else:
                text_user = message.text
            async with state.proxy() as data:
                data['text'] = text_user

            text_confirm_post = f'{text_user}'
            await message.answer(text_confirm_post, parse_mode='html', reply_markup=await create_confirm_post(),
                                 disable_web_page_preview=True)

        await IndividualPostFSM.confirm.set()
    except Exception:
        logger.warning('...')
        traceback.print_exc()


# @dp.callback_query_handler(Text(equals='confirm_individual_auto_delete'), state=IndividualPostFSM.confirm)
async def get_type_time_auto_delete(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer('Выбери тип интервала для настройки "авто удаления" поста: ',
                                  reply_markup=await create_type_interval_auto_delete())
    await IndividualPostFSM.get_type_time.set()


# @dp.callback_query_handler(Text(startswith='autodelete_individual_type_time_'), state=IndividualPostFSM.get_type_time)
async def get_interval_auto_delete(callback: CallbackQuery, state: FSMContext):
    type_time = callback.data[len('autodelete_individual_type_time_'):]
    async with state.proxy() as data:
        data['type_time_auto_delete'] = type_time

    text_type_time = '<b>Выбери интервал</b>, с которым будут публиковаться посты: \n\n'
    if type_time == 'Минуты':
        text_type_time += 'Раз в 5 минут, каждые 10 минут'
    elif type_time == 'Часы':
        text_type_time += 'Раз в 2 часа, каждые 3 часа'
    else:
        text_type_time += 'Раз в день, раз в 3 дня'
    await callback.message.edit_text(text_type_time,
                                     reply_markup=await create_interval_auto_delete(type_time),
                                     parse_mode='html')
    await IndividualPostFSM.get_interval.set()


@dp.callback_query_handler(Text(startswith='autodelete_individual_interval_'), state=IndividualPostFSM.get_interval)
async def set_interval(callback: CallbackQuery, state: FSMContext):
    interval = callback.data[len('autodelete_individual_interval_'):]
    async with state.proxy() as data:
        data['interval_auto_delete'] = interval
        type_time = data['type_time_auto_delete']

    await callback.message.delete()
    await callback.message.answer(f'Настройки авто удаления: \n\n'
                                  f'<b>Тип интервала:</b> {type_time}  |  <b>Интервал:</b> {interval}',
                                  parse_mode='html')
    await IndividualPostFSM.confirm.set()


# @dp.callback_query_handler(Text(equals='confirm_individual_preview'), state=IndividualPostFSM.confirm)
async def preview_post(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    async with state.proxy() as data:
        text_button = data.get('text_button')
        url_button = data.get('url_button')
        text = data['text']
        photo = data.get('photo')
        video = data.get('video')
        animation = data.get('animation')

    if photo:
        if text_button:
            try:
                button_link = await create_button_for_post(text_button=text_button, url_button=url_button)
                await callback.message.answer_photo(photo=photo, caption=text, reply_markup=button_link,
                                                    parse_mode='html')
            except BadRequest:
                await callback.message.answer('Невалидная кнопка, прикрепленная к посту (вероятнее всего '
                                              'неверно указан url)\n\n'
                                              'Сформировать пост невозможно')
                await state.finish()
                await callback.message.answer('Процесс успешно остановлен')
        else:
            await callback.message.answer_photo(photo=photo, caption=text, parse_mode='html')
    elif video:
        if text_button:
            try:
                button_link = await create_button_for_post(text_button=text_button, url_button=url_button)
                await callback.message.answer_video(video=video, caption=text, reply_markup=button_link,
                                                    parse_mode='html')
            except BadRequest:
                await callback.message.answer('Невалидная кнопка, прикрепленная к посту (вероятнее всего '
                                              'неверно указан url)\n\n'
                                              'Сформировать пост невозможно')
                await state.finish()
                await callback.message.answer('Процесс успешно остановлен')
        else:
            await callback.message.answer_video(video=video, caption=text, parse_mode='html')
    elif animation:
        if text_button:
            try:
                button_link = await create_button_for_post(text_button=text_button, url_button=url_button)
                await callback.message.answer_animation(animation=animation, caption=text,
                                                        reply_markup=button_link, parse_mode='html')
            except BadRequest:
                await callback.message.answer('Невалидная кнопка, прикрепленная к посту (вероятнее всего '
                                              'неверно указан url)\n\n'
                                              'Сформировать пост невозможно')
                await state.finish()
                await callback.message.answer('Процесс успешно остановлен')
        else:
            await callback.message.answer_animation(animation=animation, caption=text, parse_mode='html')
    else:
        if text_button:
            try:
                button_link = await create_button_for_post(text_button=text_button, url_button=url_button)
                await callback.message.answer(text, reply_markup=button_link, parse_mode='html',
                                              disable_web_page_preview=True)
            except BadRequest:
                await callback.message.answer('Невалидная кнопка, прикрепленная к посту (вероятнее всего '
                                              'неверно указан url)\n\n'
                                              'Сформировать пост невозможно')
                await state.finish()
                await callback.message.answer('Процесс успешно остановлен')
        else:
            await callback.message.answer(text, parse_mode='html', disable_web_page_preview=True)


# @dp.callback_query_handler(Text(equals='confirm_individual_time'), state=IndividualPostFSM.confirm)
async def get_time_before_publication(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    async with state.proxy() as data:
        time = data['time']
        day = data['day']

    # no match ;(
    if day == '0':
        day_str = 'Понедельник'
    elif day == '1':
        day_str = 'Вторник'
    elif day == '2':
        day_str = 'Среда'
    elif day == '3':
        day_str = 'Четверг'
    elif day == '4':
        day_str = 'Пятница'
    elif day == '5':
        day_str = 'Суббота'
    elif day == '6':
        day_str = 'Воскресенье'
    else:
        day_str = 'Сегодня'

    await callback.message.answer(f'<b>Время:</b> {time} | <b>День:</b> {day_str}', parse_mode='html')


# @dp.callback_query_handler(Text('confirm_individual_channels'), state=IndividualPostFSM.confirm)
async def get_channels_before_publication(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    async with state.proxy() as data:
        channels = data['channels_id']

    text_channel = f'Все каналы, в которые будет опубликован данный пост: \n\n'
    channel_db = ChannelDB()
    i = 0
    for channel in channels:
        name_channel = channel_db.get_name_channel(channel_id=channel)
        if name_channel:
            i += 1
            text_channel += f'{i}. {name_channel} | {channel}\n'
    await callback.message.answer(text_channel)


# @dp.callback_query_handler(Text(equals='confirm_individual_next'), state=IndividualPostFSM.confirm)
async def publication(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    async with state.proxy() as data:
        channels = data['channels_id']
        time = data['time']
        day = data['day']
        text_button = data.get('text_button')
        url_button = data.get('url_button')
        photo = data.get('photo')
        video = data.get('video')
        animation = data.get('animation')
        text = data['text']
        tag = data['tag']

        # auto delete:
        type_time_auto_delete = data.get('type_time_auto_delete')
        interval_auto_delete = data.get('interval_auto_delete')

    await state.finish()
    # Добавления тега для последующей его отмены пользователем
    individual_post_db = IndividualPostDB()
    if not individual_post_db.exists_tag(tag=tag):
        post_db = PostDB()
        post_db.post_add(user_id=callback.from_user.id, tag=tag, context=text)
        await publication_post(tag=tag,
                               user_id=callback.from_user.id,
                               channels=channels,
                               time=time,
                               day=day,
                               text_button=text_button,
                               url_button=url_button,
                               text=text,
                               photo=photo, video=video, animation=animation,
                               type_time_auto_delete=type_time_auto_delete, interval_auto_delete=interval_auto_delete)
        await callback.message.answer(f'Пост успешно поставлен на очередь публикации\n\n'
                                      f'Тег прикрепленный к посту: <b>{tag}</b>\n\n'
                                      f'Данный тег необходим для последующей отмены поста', parse_mode='html')
        await callback.message.delete()
    else:  # Отправка альбома
        posts = individual_post_db.get_post_by_tag(tag=tag)
        if int(day) == 99:  # Сегодня
            job = CronJob(name=tag, tz='UTC+03:00').day.at(time).go(send_album, tag=tag,
                                                                    channels=channels, posts=posts,
                                                                    type_time_auto_delete=type_time_auto_delete,
                                                                    interval_auto_delete=interval_auto_delete)
        else:  # Остальные дни.
            job = CronJob(name=tag, tz='UTC+03:00').weekday(int(day)).at(time).go(send_album, tag=tag,
                                                                                  channels=channels, posts=posts,
                                                                                  type_time_auto_delete=type_time_auto_delete,
                                                                                  interval_auto_delete=interval_auto_delete)
        msh.add_job(job)
        await callback.message.answer(f'Пост успешно поставлен на очередь публикации\n\n'
                                      f'Тег прикрепленный к посту: <b>{tag}</b>\n\n'
                                      f'Данный тег необходим для последующей отмены поста', parse_mode='html')
        smiles = ['💎', '🦠', '☃️', '⭐️']
        start_text = f'<b>Привет</b>{random.choice(smiles)}\n\n' \
                     f'<i>Это бот помощник, позволяет публиковать посты с заданным интервалом!</i>\n\n'
        await callback.message.answer(start_text,
                                      reply_markup=create_start_menu, parse_mode='html')


def register_handlers_create_individual_post():
    dp.register_callback_query_handler(start_create_post, Text(equals='start_create_post'))
    dp.register_callback_query_handler(set_channels_back, Text(equals='channels_tagged_back'),
                                       state=IndividualPostFSM.get_time)
    dp.register_callback_query_handler(get_time, Text(equals='channels_tagged_next'),
                                       state=IndividualPostFSM.get_channel)
    dp.register_callback_query_handler(set_channels, Text(startswith='channels_'), state=IndividualPostFSM.get_channel)
    dp.register_callback_query_handler(get_time_back, Text(equals='time_back'), state=IndividualPostFSM.get_day)
    dp.register_callback_query_handler(get_day, Text(startswith='time_'), state=IndividualPostFSM.get_time)
    dp.register_message_handler(get_day_message, state=IndividualPostFSM.get_time)
    dp.register_callback_query_handler(get_day_back, Text(equals='day_back'), state=IndividualPostFSM.get_button)
    dp.register_callback_query_handler(get_button_for_post, Text(startswith='day_'), state=IndividualPostFSM.get_day)
    dp.register_callback_query_handler(check_create_button, Text(startswith='create_url_'),
                                       state=IndividualPostFSM.get_button)
    dp.register_message_handler(get_url_for_button, state=IndividualPostFSM.get_text_for_button)
    dp.register_message_handler(get_post, state=IndividualPostFSM.get_url_for_button)
    dp.register_message_handler(confirm_create_post, state=IndividualPostFSM.get_post, content_types='any')
    dp.register_callback_query_handler(get_type_time_auto_delete, Text(equals='confirm_individual_auto_delete'),
                                       state=IndividualPostFSM.confirm)
    dp.register_callback_query_handler(get_interval_auto_delete, Text(startswith='autodelete_individual_type_time_'),
                                       state=IndividualPostFSM.get_type_time)
    dp.register_callback_query_handler(preview_post, Text(equals='confirm_individual_preview'),
                                       state=IndividualPostFSM.confirm)
    dp.register_callback_query_handler(get_time_before_publication, Text(equals='confirm_individual_time'),
                                       state=IndividualPostFSM.confirm)
    dp.register_callback_query_handler(get_channels_before_publication, Text('confirm_individual_channels'),
                                       state=IndividualPostFSM.confirm)
    dp.register_callback_query_handler(publication, Text(equals='confirm_individual_next'),
                                       state=IndividualPostFSM.confirm)
