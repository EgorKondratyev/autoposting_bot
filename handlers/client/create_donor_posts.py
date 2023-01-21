import random
import traceback
import re

from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

from create_bot.bot import dp
from databases.client import ChannelDB, DonorPostDB
from handlers.stop_fsm import create_keyboard_stop_fsm
from keyboards.inline.donor_posts import create_type_time_keyboard, create_keyboard_channels, \
    create_keyboard_tagged_channels, create_interval_keyboard, delete_post_keyboard, create_confirm_keyboards, \
    create_interval_keyboard_for_delete_post, create_type_time_keyboard_for_delete_posts, \
    create_buttons_url, create_schedule_day_keyboard
from keyboards.inline.start_command import create_start_menu
from keyboards.reply.donor_post_keyboard import confirmation_donor_posts_menu
from log.create_logger import logger
from states.donor_posts import DonorPostsFSM, IntervalDeleteDonorPostFSM, CreateDonorButtonsFSM, \
    CreateDescriptionDonorFSM
from utils.generate_random_tag import generate_random_tag_md5
from utils.publication_post_donor import publication_post_donor
from utils.utils import date_last_post


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


# @dp.callback_query_handler(Text(equals='channels_donor_back'), state=DonorPostsFSM.get_type_time)
async def set_channels_back(callback: CallbackQuery, state: FSMContext):
    """
    Вызывается если пользователь нажал кнопку "назад" в процессе get_type_time (handler).
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


# @dp.callback_query_handler(Text(equals='channels_tagged_next_for_donor_back'),
#                            state=[
#                                DonorPostsFSM.get_arbitrary,
#                                DonorPostsFSM.get_schedule_day,
#                                DonorPostsFSM.get_interval
#                            ])
async def get_type_time_back(callback: CallbackQuery, state: FSMContext):
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
        data['tag'] = await generate_random_tag_md5()

    if type_time == 'arbitrary':
        await callback.message.answer('Примеры: \n\n'
                                      '5м 30м (произвольный интервал от 5 минут до 30 минут)\n'
                                      '10м 13ч (произвольный интервал от 10 минут до 13 часов)\n'
                                      '1ч 2д (произвольный интервал от 1 часа до 2-ух дней)')
        await callback.message.answer('Введи интервал: ')
        await DonorPostsFSM.get_arbitrary.set()
    elif type_time == 'schedule':
        await callback.message.answer('Ты зашел в настройку собственного расписания для отправки постов\n\n'
                                      '<b>Выбери день, в котором начнется отправка постов:</b> \n\n'
                                      '*Примечание: если выбрать день, который является младше дня текущего месяца, '
                                      'то будет выбран день следующего месяца относительно текущего'
                                      ' (Допустим, что сегодня 15 января, но ты выбрал дату 10 января, а значит '
                                      'рассылка начнется 10 февраля. Допустим (2), что сегодня 30 января, но ты выбрал '
                                      'дату рассылки 29 числа, в феврале менее 29 дней, а значит начало рассылки '
                                      'будет в марте 29 числа)', parse_mode='html',
                                      reply_markup=await create_schedule_day_keyboard())
        await DonorPostsFSM.get_schedule_day.set()
    else:
        text_type_time = '<b>Выбери интервал</b>, с которым будут публиковаться посты: \n\n'
        if type_time == 'Минуты':
            text_type_time += 'Раз в 5 минут, каждые 10 минут'
        elif type_time == 'Часы':
            text_type_time += 'Раз в 2 часа, каждые 3 часа'
        else:
            text_type_time += 'Раз в день, раз в 3 дня'
        await callback.message.edit_text(text_type_time,
                                         reply_markup=await create_interval_keyboard(type_time),
                                         parse_mode='html')
        await DonorPostsFSM.get_interval.set()


# @dp.callback_query_handler(Text(startswith='schedule_day_'), state=DonorPostsFSM.get_schedule_day)
async def get_schedule_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer('День в расписании успешно установлен')
    day = callback.data[len('schedule_day_'):]
    async with state.proxy() as data:
        data['schedule_day'] = day

    await callback.message.answer(f'Отлично☕️ был выбран {day}-ый день\n\n'
                                  f'<b>Введи времена, в которые будет происходить постинг:</b> \n\n'
                                  f'Пример: <code>08:15 | 12:30 | 23:40</code>\n\n'
                                  f'*Примечание: времён может быть сколько угодно, но их обязательно вводить через '
                                  f'вертикальную черту "<code>|</code>"',
                                  parse_mode='html')
    await DonorPostsFSM.get_schedule_time.set()


# @dp.message_handler(state=DonorPostsFSM.get_schedule_time)
async def set_schedule(message: Message, state: FSMContext):
    times = message.text.split('|')
    message_schedule = await message.answer('Проверка')
    for i, time in enumerate(times):  # Проверяем на то все ли правильно ввел пользователь
        await message_schedule.edit_text('Проверка.')
        # Не охватывает ограничения с 20-24 часы, т.е. возможно 25:23, 28:45 и так далее
        match = re.findall(r'[0-2]\d:[0-5]\d', time)
        await message_schedule.edit_text('Проверка..')
        if not match:
            await message_schedule.edit_text(f'Нарушение синтаксиса, невозможное существование времени: {time}\n\n'
                                             f'Повтори ввод времени или останови операцию',
                                             reply_markup=create_keyboard_stop_fsm())
            return
        times[i] = times[i].replace(' ', '')
        await message_schedule.edit_text('Проверка...')
    async with state.proxy() as data:
        data['schedule_times'] = times
    await message_schedule.edit_text('<b>Перешли из канала донора посты:</b> \n\n'
                                     'Дождись загрузки всех медиа-файлов, после этого нажми на кнопку сохранить',
                                     parse_mode='html', reply_markup=create_keyboard_stop_fsm())
    await message.answer('<i>Будь крайне внимателен с коллекциями медиа! Если в посте содержится '
                         'более чем 1 картинка или же видео, то это будет считаться за коллекцию. Каждый '
                         'медиа-файл в коллекции бот считает как за отдельное сообщение. Соответственно '
                         'пост из 5 медиа-файлов будет интерпретирован как 5 постов</i>',
                         parse_mode='html', reply_markup=confirmation_donor_posts_menu)
    await DonorPostsFSM.get_posts.set()


# @dp.message_handler(state=DonorPostsFSM.get_arbitrary)
async def set_arbitrary_interval(message: Message, state: FSMContext):
    """
    Сохраняем рандомный пользовательский интервал (со всеми исходящими проверками)
    :param message:
    :param state:
    :return:
    """
    try:
        match = re.findall(r'\b\d{1,2}[мчд]\b \b\d{1,2}[мчд]\b', message.text)
        if match:
            first_interval = int(message.text.split(' ')[0][:-1])
            first_type = message.text.split(' ')[0][-1:]

            second_interval = int(message.text.split(' ')[1][:-1])
            second_type = message.text.split(' ')[1][-1:]
            if first_type == 'м':
                if first_interval < 59:
                    pass
                else:
                    await message.answer('В одном часу лишь 60 минут! (можно указать лишь 59 минут)',
                                         reply_markup=create_keyboard_stop_fsm())
                    return
            elif first_type == 'ч':
                if first_interval < 23:
                    pass
                else:
                    await message.answer('В одном дне лишь 24 часа! (можно указать лишь 23 часа)',
                                         reply_markup=create_keyboard_stop_fsm())
                    return
            elif first_type == 'д':
                if first_interval < 5:
                    pass
                else:
                    await message.answer('Количество дней в рандомном интервале не может превышать 5',
                                         reply_markup=create_keyboard_stop_fsm())
                    return

            if second_type == 'м':
                if second_interval < 59:
                    pass
                else:
                    await message.answer('В одном часу лишь 60 минут! (можно указать лишь 59 минут)',
                                         reply_markup=create_keyboard_stop_fsm())
                    return
            elif second_type == 'ч':
                if second_interval < 23:
                    pass
                else:
                    await message.answer('В одном дне лишь 24 часа! (можно указать лишь 23 часа)',
                                         reply_markup=create_keyboard_stop_fsm())
                    return
            elif second_type == 'д':
                if second_interval < 5:
                    pass
                else:
                    await message.answer('Количество дней в рандомном интервале не может превышать 5',
                                         reply_markup=create_keyboard_stop_fsm())
                    return

            await message.answer('Интервал успешно выбран')
            async with state.proxy() as data:
                data['first_type_time'] = first_type
                data['first_interval'] = first_interval
                data['second_type_time'] = second_type
                data['second_interval'] = second_interval

            await message.answer('<b>Перешли из канала донора посты:</b> \n\n'
                                 'Дождись загрузки всех медиа-файлов, после этого нажми на кнопку сохранить',
                                 parse_mode='html', reply_markup=create_keyboard_stop_fsm())
            await message.answer('<i>Будь крайне внимателен с коллекциями медиа! Если в посте содержится '
                                 'более чем 1 картинка или же видео, то это будет считаться за коллекцию. Каждый '
                                 'медиа-файл в коллекции бот считает как за отдельное сообщение. Соответственно '
                                 'пост из 5 медиа-файлов будет интерпретирован как 5 постов</i>',
                                 parse_mode='html', reply_markup=confirmation_donor_posts_menu)
            await DonorPostsFSM.get_posts.set()
        else:
            await message.answer('Нарушен синтаксис!',
                                 reply_markup=create_keyboard_stop_fsm())
            await message.answer('Примеры: \n\n'
                                 '5м 30м (произвольный интервал от 5 минут до 30 минут)\n'
                                 '10м 13ч (произвольный интервал от 10 минут до 13 часов)\n'
                                 '1ч 2д (произвольный интервал от 1 часа до 2-ух дней)')
    except Exception as ex:
        logger.warning(f'Возникла ошибка при считывании произвольного интервала\n\n'
                       f'{ex}')


# @dp.callback_query_handler(Text(startswith='interval_'), state=DonorPostsFSM.get_interval)
async def get_posts(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Интервал успешно выбран')
    async with state.proxy() as data:
        data['interval'] = callback.data[len('interval_'):]

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
        try:
            donor_post_db = DonorPostDB()
            if message.photo:
                if message.caption is not None:
                    if message.html_text:
                        text_user = message.html_text
                    else:
                        text_user = message.caption
                else:
                    text_user = ''
                async with state.proxy() as data:
                    tag = data['tag']

                group_media_id = None
                if message.media_group_id:
                    group_media_id = message.media_group_id

                donor_post_db.add_post(tag=tag, photo_id=message.photo[-1].file_id, content=text_user,
                                       unique_id_media_file=message.photo[-1].file_unique_id,
                                       user_id=message.from_user.id, group_media_id=group_media_id)

                text_confirm_post = f'{text_user}'
                await message.answer_photo(photo=message.photo[-1].file_id,
                                           caption=text_confirm_post, parse_mode='html',
                                           reply_markup=await delete_post_keyboard())

            elif message.video:
                if message.caption is not None:
                    if message.html_text:
                        text_user = message.html_text
                    else:
                        text_user = message.caption
                else:
                    text_user = ''
                async with state.proxy() as data:
                    tag = data['tag']

                group_media_id = None
                if message.media_group_id:
                    group_media_id = message.media_group_id

                donor_post_db.add_post(tag=tag, video_id=message.video.file_id, content=text_user,
                                       unique_id_media_file=message.video.file_unique_id,
                                       user_id=message.from_user.id, group_media_id=group_media_id)

                text_confirm_post = f'{text_user}'
                await message.answer_video(video=message.video.file_id,
                                           caption=text_confirm_post, parse_mode='html',
                                           reply_markup=await delete_post_keyboard())

            elif message.animation:
                if message.caption is not None:
                    if message.html_text:
                        text_user = message.html_text
                    else:
                        text_user = message.caption
                else:
                    text_user = ''
                async with state.proxy() as data:
                    tag = data['tag']

                group_media_id = None
                if message.media_group_id:
                    group_media_id = message.media_group_id

                donor_post_db.add_post(tag=tag, animation_id=message.animation.file_id, content=text_user,
                                       unique_id_media_file=message.animation.file_unique_id,
                                       user_id=message.from_user.id, group_media_id=group_media_id)

                text_confirm_post = f'{text_user}'
                await message.answer_animation(animation=message.animation.file_id,
                                               caption=text_confirm_post, parse_mode='html',
                                               reply_markup=await delete_post_keyboard())
            elif message.video_note:
                async with state.proxy() as data:
                    tag = data['tag']

                group_media_id = None
                if message.media_group_id:
                    group_media_id = message.media_group_id

                donor_post_db.add_post(tag=tag, animation_id=message.video_note.file_id,
                                       unique_id_media_file=message.video_note.file_unique_id,
                                       user_id=message.from_user.id, group_media_id=group_media_id)

                await message.answer_video_note(video_note=message.video_note.file_id,
                                                reply_markup=await delete_post_keyboard())

            elif message.text is not None:
                if message.html_text:
                    text_user = message.html_text
                else:
                    text_user = message.text
                async with state.proxy() as data:
                    tag = data['tag']

                donor_post_db.add_post(user_id=message.from_user.id, tag=tag, content=text_user)

                text_confirm_post = f'{text_user}'
                await message.answer(text_confirm_post, parse_mode='html',
                                     reply_markup=await delete_post_keyboard(), disable_web_page_preview=True)
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
async def confirm(message: Message, state: FSMContext):
    async with state.proxy() as data:
        tag = data['tag']
    post_donor_db = DonorPostDB()
    posts = post_donor_db.get_posts_by_tag(tag=tag)
    if posts:
        await message.answer('Выбери дополнительные характеристики публикации (если таковые необходимы): ',
                             reply_markup=await create_confirm_keyboards())
        await DonorPostsFSM.confirm.set()
    else:
        await message.answer('Прежде чем нажимать кнопку "Продолжить", '
                             '<b>ты должен отправить мне хотя бы 1 пост</b>!\n\n'
                             'Если ты хочешь остановить процесс, то нажми на кнопку "Остановить❌"',
                             parse_mode='html')


# @dp.callback_query_handler(Text(equals='confirm_donor_preview_link'), state=DonorPostsFSM.confirm)
async def set_preview_link(callback: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['preview_link'] = True
        delete_text = data.get('delete_text')
        buttons = data.get('buttons')
        mix_post = data.get('mix_post')
        add_description = data.get('add_description')
        auto_delete = data.get('auto_delete_interval')

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=await create_confirm_keyboards(buttons=buttons,
                                                                                         mix_post=mix_post,
                                                                                         add_description=add_description,
                                                                                         delete_text=delete_text,
                                                                                         auto_delete=auto_delete,
                                                                                         preview_link=True))


# @dp.callback_query_handler(Text(equals='confirm_donor_preview_link_yes'), state=DonorPostsFSM.confirm)
async def cancellation_preview_link(callback: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        del data['preview_link']
        delete_text = data.get('delete_text')
        buttons = data.get('buttons')
        mix_post = data.get('mix_post')
        add_description = data.get('add_description')
        auto_delete = data.get('auto_delete_interval')

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=await create_confirm_keyboards(buttons=buttons,
                                                                                         mix_post=mix_post,
                                                                                         add_description=add_description,
                                                                                         delete_text=delete_text,
                                                                                         auto_delete=auto_delete))


# @dp.callback_query_handler(Text(equals='confirm_donor_delete_text'), state=DonorPostsFSM.confirm)
async def delete_text_from_donor_posts(callback: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['delete_text'] = True
        buttons = data.get('buttons')
        mix_post = data.get('mix_post')
        add_description = data.get('add_description')
        auto_delete = data.get('auto_delete_interval')
        preview_link = data.get('preview_link')

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=await create_confirm_keyboards(buttons=buttons,
                                                                                         mix_post=mix_post,
                                                                                         add_description=add_description,
                                                                                         delete_text=True,
                                                                                         auto_delete=auto_delete,
                                                                                         preview_link=preview_link))


# @dp.callback_query_handler(Text(equals='confirm_donor_delete_text_yes'), state=DonorPostsFSM.confirm)
async def cancellation_delete_text(callback: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        del data['delete_text']
        buttons = data.get('buttons')
        mix_post = data.get('mix_post')
        add_description = data.get('add_description')
        auto_delete = data.get('auto_delete_interval')
        preview_link = data.get('preview_link')

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=await create_confirm_keyboards(buttons=buttons,
                                                                                         mix_post=mix_post,
                                                                                         add_description=add_description,
                                                                                         auto_delete=auto_delete,
                                                                                         preview_link=preview_link))


# @dp.callback_query_handler(Text(equals='confirm_donor_auto_delete_posts'), state=DonorPostsFSM.confirm)
async def get_type_time_for_setting_auto_delete_posts(callback: CallbackQuery):
    """
    Обработчик позволяет установить время авто удаления поста через время.
    :param callback:
    :return:
    """
    await callback.answer()
    await callback.message.answer('Выбери тип интервала для последующего удаления сообщения: ',
                                  reply_markup=await create_type_time_keyboard_for_delete_posts())
    await IntervalDeleteDonorPostFSM.get_type_time.set()


# @dp.callback_query_handler(Text(equals='confirm_donor_auto_delete_posts_yes'), state=DonorPostsFSM.confirm)
async def cancellation_auto_delete(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик позволяет отменить авто удаление постов.
    :param state:
    :param callback:
    :return:
    """
    async with state.proxy() as data:
        del data['auto_delete_type_time']
        del data['auto_delete_interval']
        buttons = data.get('buttons')
        mix_post = data.get('mix_post')
        add_description = data.get('add_description')
        delete_text = data.get('delete_text')
        preview_link = data.get('preview_link')

    await callback.answer('Авто удаление отменено')
    await callback.message.edit_reply_markup(reply_markup=await create_confirm_keyboards(buttons=buttons,
                                                                                         mix_post=mix_post,
                                                                                         add_description=add_description,
                                                                                         delete_text=delete_text,
                                                                                         preview_link=preview_link))


# @dp.callback_query_handler(Text(startswith='autodelete_donor_type_time_'),
#                            state=IntervalDeleteDonorPostFSM.get_type_time).
async def get_interval_for_setting_auto_delete_posts(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    type_time = callback.data[len('autodelete_donor_type_time_'):]
    async with state.proxy() as data:
        data['auto_delete_type_time'] = type_time

    await callback.message.answer('Выбери шаг, с которым посты будут удаляться после публикации: ',
                                  reply_markup=await create_interval_keyboard_for_delete_post(type_time=type_time))
    await IntervalDeleteDonorPostFSM.get_interval.set()


# @dp.callback_query_handler(Text(startswith='autodelete_donor_interval_'),
#                            state=IntervalDeleteDonorPostFSM.get_interval)
async def confirm_auto_delete(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    auto_delete_interval = callback.data[len('autodelete_donor_interval_'):]
    async with state.proxy() as data:
        tag = data['tag']
        data['auto_delete_interval'] = auto_delete_interval
        buttons = data.get('buttons')
        mix_post = data.get('mix_post')
        add_description = data.get('add_description')
        delete_text = data.get('delete_text')
        preview_link = data.get('preview_link')

    post_donor_db = DonorPostDB()
    posts = post_donor_db.get_posts_by_tag(tag=tag)
    if posts:
        await callback.message.answer('Выбери дополнительные характеристики публикации (если таковые необходимы): ',
                                      reply_markup=await create_confirm_keyboards(auto_delete=auto_delete_interval,
                                                                                  buttons=buttons,
                                                                                  add_description=add_description,
                                                                                  mix_post=mix_post,
                                                                                  delete_text=delete_text,
                                                                                  preview_link=preview_link)
                                      )
        await DonorPostsFSM.confirm.set()
    else:
        await callback.message.answer('Прежде чем нажимать кнопку "Продолжить", '
                                      '<b>ты должен отправить мне хотя бы 1 пост</b>!\n\n'
                                      'Если ты хочешь остановить процесс, то нажми на кнопку "Остановить❌"',
                                      parse_mode='html')


# @dp.callback_query_handler(Text(equals='confirm_donor_add_urls'),
#                            state=[DonorPostsFSM.confirm, CreateDonorButtonsFSM.confirm])
async def get_buttons(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer('Отправьте мне список URL-кнопок в одном сообщении. Пожалуйста, '
                                  'следуйте этому формату:\n\n'
                                  'Кнопка 1 - http://example1.com\n'
                                  'Кнопка 2 - http://example2.com\n\n'
                                  'Внимание! Для альбомов кнопки не будут добавлены')
    await CreateDonorButtonsFSM.get_name.set()


# @dp.message_handler(state=CreateDonorButtonsFSM.get_name)
async def set_button(message: Message, state: FSMContext):
    """
    Установка кнопок в state, а также уточнение хочет ли пользователь добавить ещё кнопки
    :param message:
    :param state:
    :return:
    """
    buttons_list = message.text.split('\n')  # ['Кнопка 1 - http://example1.com', 'Кнопка 2 - http://example2.com']
    buttons_result = []
    for button in buttons_list:
        button_list = button.split('-')
        button_name = button_list[0].strip()
        button_url = button_list[1].strip()

        buttons_result.append({button_name: button_url})

    async with state.proxy() as data:
        data['buttons'] = buttons_result
        auto_delete = data.get('auto_delete_interval')
        mix_post = data.get('mix_post')
        add_description = data.get('add_description')
        delete_text = data.get('delete_text')
        preview_link = data.get('preview_link')

    await message.answer('Все кнопки успешно добавлены!')
    await message.answer('Выбери дополнительные характеристики публикации (если таковые необходимы): ',
                         reply_markup=await create_confirm_keyboards(auto_delete=auto_delete,
                                                                     buttons=buttons_result,
                                                                     add_description=add_description,
                                                                     mix_post=mix_post,
                                                                     delete_text=delete_text,
                                                                     preview_link=preview_link))
    await DonorPostsFSM.confirm.set()


# @dp.callback_query_handler(Text(equals='confirm_donor_add_urls_yes'), state=DonorPostsFSM.confirm)
async def cancellation_url_buttons(callback: CallbackQuery, state: FSMContext):
    """
    Удаление всех созданных кнопок перед публикацией.
    :param callback:
    :param state:
    :return:
    """
    async with state.proxy() as data:
        del data['buttons']
        auto_delete = data.get('auto_delete_interval')
        mix_post = data.get('mix_post')
        add_description = data.get('add_description')
        delete_text = data.get('delete_text')
        preview_link = data.get('preview_link')

    await callback.message.edit_reply_markup(reply_markup=await create_confirm_keyboards(auto_delete=auto_delete,
                                                                                         add_description=add_description,
                                                                                         mix_post=mix_post,
                                                                                         delete_text=delete_text,
                                                                                         preview_link=preview_link))
    await callback.answer('Кнопки удалены')


# @dp.callback_query_handler(Text(equals='confirm_donor_add_description'), state=DonorPostsFSM.confirm)
async def get_description_for_all_donor_post(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer('Отправь мне описание, которое будет прикреплено ко всем постам: ')
    await CreateDescriptionDonorFSM.get_description.set()


# @dp.message_handler(state=CreateDescriptionDonorFSM.get_description)
async def confirm_description(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if message.html_text:
            data['add_description'] = message.html_text
        else:
            data['add_description'] = message.text
        auto_delete = data.get('auto_delete_interval')
        mix_post = data.get('mix_post')
        buttons = data.get('buttons')
        delete_text = data.get('delete_text')
        preview_link = data.get('preview_link')

    await message.answer('Выбери дополнительные характеристики публикации (если таковые необходимы): ',
                         reply_markup=await create_confirm_keyboards(auto_delete=auto_delete,
                                                                     buttons=buttons,
                                                                     add_description=message.text,
                                                                     mix_post=mix_post,
                                                                     delete_text=delete_text,
                                                                     preview_link=preview_link))
    await DonorPostsFSM.confirm.set()


# @dp.callback_query_handler(Text(equals='confirm_donor_add_description_yes'), state=DonorPostsFSM.confirm)
async def cancellation_description(callback: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        del data['add_description']
        auto_delete = data.get('auto_delete_interval')
        mix_post = data.get('mix_post')
        buttons = data.get('buttons')
        delete_text = data.get('delete_text')
        preview_link = data.get('preview_link')

    await callback.answer('Описание успешно удалено')
    await callback.message.edit_reply_markup(reply_markup=await create_confirm_keyboards(auto_delete=auto_delete,
                                                                                         buttons=buttons,
                                                                                         mix_post=mix_post,
                                                                                         delete_text=delete_text,
                                                                                         preview_link=preview_link))


# @dp.callback_query_handler(Text(equals='confirm_donor_mix_post'), state=DonorPostsFSM.confirm)
async def set_mix_post(callback: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['mix_post'] = True
        description = data.get('add_description')
        auto_delete = data.get('auto_delete_interval')
        buttons = data.get('buttons')
        delete_text = data.get('delete_text')
        preview_link = data.get('preview_link')

    await callback.answer('Перемешивание постов установлено')
    await callback.message.edit_reply_markup(reply_markup=await create_confirm_keyboards(auto_delete=auto_delete,
                                                                                         buttons=buttons,
                                                                                         mix_post=True,
                                                                                         add_description=description,
                                                                                         delete_text=delete_text,
                                                                                         preview_link=preview_link))


# @dp.callback_query_handler(Text(equals='confirm_donor_mix_post_yes'), state=DonorPostsFSM.confirm)
async def cancellation_mix_post(callback: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        del data['mix_post']
        description = data.get('add_description')
        auto_delete = data.get('auto_delete_interval')
        buttons = data.get('buttons')
        delete_text = data.get('delete_text')
        preview_link = data.get('preview_link')

    await callback.answer('Перемешивание удалено')
    await callback.message.edit_reply_markup(reply_markup=await create_confirm_keyboards(auto_delete=auto_delete,
                                                                                         buttons=buttons,
                                                                                         add_description=description,
                                                                                         delete_text=delete_text,
                                                                                         preview_link=preview_link))


# @dp.callback_query_handler(Text(equals='confirm_donor_start_pub'), state=DonorPostsFSM.confirm)
async def publication(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        async with state.proxy() as data:
            channels_id = data['channels_id']
            type_time = data['type_time']
            interval = data.get('interval')  # Если задан рандомный интервал, то здесь None.
            tag = data['tag']

            # Параметры, которые устанавливаются из дополнительного меню.
            type_time_auto_delete = data.get('auto_delete_type_time')
            interval_auto_delete = data.get('auto_delete_interval')
            buttons_dict = data.get('buttons')
            description = data.get('add_description')
            mix_post = data.get('mix_post')
            delete_text = data.get('delete_text')
            preview_link = data.get('preview_link')

            # Если был задан рандомный интервал, то считываем все необходимые данные
            first_type_time = data.get('first_type_time')
            first_interval = data.get('first_interval')
            second_type_time = data.get('second_type_time')
            second_interval = data.get('second_interval')

            # Если было задано расписание, то считываем все необходимые данные
            schedule_day = data.get('schedule_day')
            schedule_times = data.get('schedule_times')

        post_donor_db = DonorPostDB()
        posts = post_donor_db.get_posts_by_tag(tag=tag)
        if posts:
            try:
                await state.finish()
                if buttons_dict:  # Формируем кнопки, если таковые есть
                    buttons = await create_buttons_url(buttons_dict)
                else:
                    buttons = None
            except Exception as ex:
                await callback.message.answer('Возникла ошибка на этапе формирования кнопок!\n\n'
                                              'Убедись, что вводил все правильно и повтори действия.')
                logger.warning(f'Возникла ошибка при подтверждении публикации (создание кнопок)\n'
                               f'{ex}')
                return

            date = date_last_post(type_time=type_time, interval=interval, posts_amount=len(posts),
                                  schedule_times=schedule_times)
            messages = ['Комфортной работы🍫', 'Приятной работы🧃']
            await callback.message.answer('🚀')
            await callback.message.answer(f'Все посты успешно добавлены в очередь!\n\n'
                                          f'Количество добавленных постов в очередь: <b>{len(posts)}</b>\n\n'
                                          f'Дата публикации последнего поста: <b>{date}</b>\n\n'
                                          f'Тег публикаций: {tag}\n\n'
                                          f'<i>{random.choice(messages)}</i>',
                                          parse_mode='html',
                                          reply_markup=ReplyKeyboardRemove())
            status_pub = await publication_post_donor(tag=tag, type_time=type_time, interval=interval,
                                                      channels=channels_id,
                                                      type_time_auto_delete=type_time_auto_delete,
                                                      interval_auto_delete=interval_auto_delete,
                                                      first_type_time=first_type_time, first_interval=first_interval,
                                                      second_type_time=second_type_time,
                                                      second_interval=second_interval,
                                                      buttons=buttons,
                                                      description=description,
                                                      mix_post=mix_post, delete_text=delete_text,
                                                      schedule_times=schedule_times, schedule_day=schedule_day,
                                                      preview_link=preview_link,
                                                      user_id=callback.from_user.id)
            smiles = ['💎', '🦠', '☃️', '⭐️']
            start_text = f'<b>Привет</b>{random.choice(smiles)}\n\n' \
                         f'<i>Это бот помощник, позволяет публиковать посты с заданным интервалом!</i>\n\n'
            await callback.message.answer(start_text,
                                          reply_markup=create_start_menu, parse_mode='html')
            if status_pub == 2:
                await callback.message.answer('Внимание! Посты не были поставлены на публикацию, так как '
                                              'был нарушен синтаксис произвольного интервала!')
    except Exception as ex:
        logger.warning(f'Произошла ошибка в обработчике публикации\n\n'
                       f'{ex}')


def register_handlers_donor_posts():
    dp.register_callback_query_handler(get_channels, Text(equals='start_post_in_turn'), state=None)
    dp.register_callback_query_handler(set_channels_back, Text(equals='channels_donor_back'),
                                       state=DonorPostsFSM.get_type_time)
    dp.register_callback_query_handler(set_channels, Text(startswith='channels_donor_'),
                                       state=DonorPostsFSM.get_channels)
    dp.register_callback_query_handler(get_type_time, Text(startswith='channels_tagged_next_for_donor'),
                                       state=DonorPostsFSM.get_channels)
    dp.register_callback_query_handler(get_type_time_back, Text(equals='channels_tagged_next_for_donor_back'),
                                       state=[
                                           DonorPostsFSM.get_arbitrary,
                                           DonorPostsFSM.get_schedule_day,
                                           DonorPostsFSM.get_interval
                                       ])
    dp.register_callback_query_handler(get_interval, Text(startswith='type_time_'), state=DonorPostsFSM.get_type_time)
    dp.register_callback_query_handler(get_schedule_time, Text(startswith='schedule_day_'),
                                       state=DonorPostsFSM.get_schedule_day)
    dp.register_message_handler(set_schedule, state=DonorPostsFSM.get_schedule_time)
    dp.register_message_handler(set_arbitrary_interval, state=DonorPostsFSM.get_arbitrary)
    dp.register_callback_query_handler(get_posts, Text(startswith='interval_'), state=DonorPostsFSM.get_interval)
    dp.register_message_handler(confirm, Text(equals='Продолжить🚀'), state=DonorPostsFSM.get_posts)
    dp.register_callback_query_handler(set_preview_link,
                                       Text(equals='confirm_donor_preview_link'), state=DonorPostsFSM.confirm)
    dp.register_callback_query_handler(cancellation_preview_link,
                                       Text(equals='confirm_donor_preview_link_yes'), state=DonorPostsFSM.confirm)
    dp.register_callback_query_handler(delete_text_from_donor_posts, Text(equals='confirm_donor_delete_text'),
                                       state=DonorPostsFSM.confirm)
    dp.register_callback_query_handler(cancellation_delete_text, Text(equals='confirm_donor_delete_text_yes'),
                                       state=DonorPostsFSM.confirm)
    dp.register_callback_query_handler(get_type_time_for_setting_auto_delete_posts,
                                       Text(equals='confirm_donor_auto_delete_posts'), state=DonorPostsFSM.confirm)
    dp.register_callback_query_handler(cancellation_auto_delete,
                                       Text(equals='confirm_donor_auto_delete_posts_yes'), state=DonorPostsFSM.confirm)
    dp.register_callback_query_handler(get_interval_for_setting_auto_delete_posts,
                                       Text(startswith='autodelete_donor_type_time_'),
                                       state=IntervalDeleteDonorPostFSM.get_type_time)
    dp.register_message_handler(set_posts, state=DonorPostsFSM.get_posts, content_types='any')
    dp.register_callback_query_handler(delete_donor_post_before_publication,
                                       Text(equals='delete_post'), state=DonorPostsFSM.get_posts)
    dp.register_callback_query_handler(confirm_auto_delete, Text(startswith='autodelete_donor_interval_'),
                                       state=IntervalDeleteDonorPostFSM.get_interval)
    dp.register_callback_query_handler(get_buttons, Text(equals='confirm_donor_add_urls'),
                                       state=[DonorPostsFSM.confirm])
    dp.register_message_handler(set_button, state=CreateDonorButtonsFSM.get_name)
    dp.register_callback_query_handler(cancellation_url_buttons, Text(equals='confirm_donor_add_urls_yes'),
                                       state=DonorPostsFSM.confirm)
    dp.register_callback_query_handler(get_description_for_all_donor_post, Text(equals='confirm_donor_add_description'),
                                       state=DonorPostsFSM.confirm)
    dp.register_message_handler(confirm_description, state=CreateDescriptionDonorFSM.get_description)
    dp.register_callback_query_handler(cancellation_description, Text(equals='confirm_donor_add_description_yes'),
                                       state=DonorPostsFSM.confirm)
    dp.register_callback_query_handler(set_mix_post, Text(equals='confirm_donor_mix_post'), state=DonorPostsFSM.confirm)
    dp.register_callback_query_handler(cancellation_mix_post, Text(equals='confirm_donor_mix_post_yes'),
                                       state=DonorPostsFSM.confirm)
    dp.register_callback_query_handler(publication, Text(equals='confirm_donor_start_pub'), state=DonorPostsFSM.confirm)
