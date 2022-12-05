import asyncio
import traceback

from aiogram.types import MediaGroup
from async_cron.job import CronJob
from aiogram.utils.exceptions import BadRequest

from create_bot.bot import bot
from databases.client import PostDB, IndividualPostDB
from keyboards.inline.individual_post import create_button_for_post
from log.create_logger import logger
from utils.create_cron import msh
from utils.generate_random_tag import generate_random_tag_md5


async def delete_message(tag: str, message, type_time_auto_delete: str, interval_auto_delete: str):
    if type_time_auto_delete == 'Минуты':
        if '🎅' in interval_auto_delete:
            interval_auto_delete = interval_auto_delete[:-1]
        sleep_time = int(interval_auto_delete) * 60
        await asyncio.sleep(sleep_time)
        if isinstance(message, list):  # удаление альбома
            for msg in message:
                await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)
        else:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    elif type_time_auto_delete == 'Часы':
        sleep_time = int(interval_auto_delete) * 3600
        await asyncio.sleep(sleep_time)
        if isinstance(message, list):  # удаление альбома
            for msg in message:
                await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)
        else:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    else:  # days
        sleep_time = int(interval_auto_delete) * 86400
        await asyncio.sleep(sleep_time)
        if isinstance(message, list):  # удаление альбома
            for msg in message:
                await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)
        else:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    msh.del_job(tag)


async def create_cron_delete_message(message, type_time_auto_delete, interval_auto_delete):
    if type_time_auto_delete and interval_auto_delete:
        tag = await generate_random_tag_md5()
        job = CronJob(tag, run_total=1).every(1).second.go(delete_message, tag=tag, message=message,
                                                           type_time_auto_delete=type_time_auto_delete,
                                                           interval_auto_delete=interval_auto_delete)
        msh.add_job(job)


async def send_text(tag, user_id: int, channels: list, text: str, text_button: str | None = None,
                    url_button: str | None = None, type_time_auto_delete: str = None, interval_auto_delete: str = None):
    """
    Отправка поста типа "текст" пользователю.
    :param interval_auto_delete:
    :param type_time_auto_delete:
    :param tag:
    :param user_id:
    :param channels:
    :param text:
    :param text_button:
    :param url_button:
    :return:
    """
    if text_button:
        for channel in channels:
            try:
                button_link = await create_button_for_post(text_button=text_button, url_button=url_button)
                message = await bot.send_message(chat_id=channel, text=text, reply_markup=button_link)
                await create_cron_delete_message(message=message,
                                                 type_time_auto_delete=type_time_auto_delete,
                                                 interval_auto_delete=interval_auto_delete)
                await asyncio.sleep(1)
            except BadRequest:
                await bot.send_message(chat_id=user_id, text=f'Возникла ошибка с одним из постов, невалидный '
                                                             f'url: {url_button}')
                logger.warning(f'Возникла ошибка с текстовым постом, неверный url: {url_button}\n'
                               f'User id: {user_id}')
                traceback.print_exc()
    else:
        for channel in channels:
            message = await bot.send_message(chat_id=channel, text=text)
            await create_cron_delete_message(message=message,
                                             type_time_auto_delete=type_time_auto_delete,
                                             interval_auto_delete=interval_auto_delete)
            await asyncio.sleep(1)

    msh.del_job(tag)
    post_db = PostDB()
    post_db.post_del(user_id=user_id, tag=tag)


async def send_photo(tag, user_id: int, channels: list, text, text_button: str | None = None,
                     url_button: str | None = None, photo_path: str | None = None, type_time_auto_delete: str = None,
                     interval_auto_delete: str = None):
    """
    Отправка поста типа "фото" пользователю.
    :param interval_auto_delete:
    :param type_time_auto_delete:
    :param tag:
    :param user_id:
    :param channels:
    :param text:
    :param text_button:
    :param url_button:
    :param photo_path:
    :return:
    """
    if text_button:
        for channel in channels:
            try:
                button_link = await create_button_for_post(text_button=text_button, url_button=url_button)
                message = await bot.send_photo(chat_id=channel, caption=text, photo=photo_path,
                                               reply_markup=button_link)
                await create_cron_delete_message(message=message,
                                                 type_time_auto_delete=type_time_auto_delete,
                                                 interval_auto_delete=interval_auto_delete)
                await asyncio.sleep(1)
            except BadRequest:
                await bot.send_message(chat_id=user_id, text=f'Возникла ошибка с одним из постов, невалидный '
                                                             f'url: {url_button}')
                logger.warning(f'Возникла ошибка с текстовым постом, неверный url: {url_button}\n'
                               f'User id: {user_id}')
                traceback.print_exc()
    else:
        for channel in channels:
            message = await bot.send_photo(chat_id=channel, caption=text, photo=photo_path)
            await create_cron_delete_message(message=message,
                                             type_time_auto_delete=type_time_auto_delete,
                                             interval_auto_delete=interval_auto_delete)
            await asyncio.sleep(1)

    msh.del_job(job_name=tag)
    post_db = PostDB()
    post_db.post_del(user_id=user_id, tag=tag)


async def send_animation(tag, user_id: int, channels: list, text, text_button: str | None = None,
                         url_button: str | None = None, animation_path: str | None = None,
                         type_time_auto_delete: str = None, interval_auto_delete: str = None):
    """
    Отправка поста типа "GIF, animation" пользователю.
    :param interval_auto_delete:
    :param type_time_auto_delete:
    :param tag:
    :param user_id:
    :param channels:
    :param text:
    :param text_button:
    :param url_button:
    :param animation_path:
    :return:
    """
    if text_button:
        for channel in channels:
            try:
                button_link = await create_button_for_post(text_button=text_button, url_button=url_button)
                message = await bot.send_animation(animation=animation_path, chat_id=channel, caption=text,
                                                   reply_markup=button_link)
                await create_cron_delete_message(message=message,
                                                 type_time_auto_delete=type_time_auto_delete,
                                                 interval_auto_delete=interval_auto_delete)
                await asyncio.sleep(1)
            except BadRequest:
                await bot.send_message(chat_id=user_id, text=f'Возникла ошибка с одним из постов, невалидный '
                                                             f'url: {url_button}')
                logger.warning(f'Возникла ошибка с текстовым постом, неверный url: {url_button}\n'
                               f'User id: {user_id}')
                traceback.print_exc()
    else:
        for channel in channels:
            message = await bot.send_animation(chat_id=channel, caption=text, animation=animation_path)
            await create_cron_delete_message(message=message,
                                             type_time_auto_delete=type_time_auto_delete,
                                             interval_auto_delete=interval_auto_delete)
            await asyncio.sleep(1)

    msh.del_job(job_name=tag)
    post_db = PostDB()
    post_db.post_del(user_id=user_id, tag=tag)


async def send_video(tag, user_id: int, channels: list, text, text_button: str | None = None,
                     url_button: str | None = None, video_path: str | None = None, type_time_auto_delete: str = None,
                     interval_auto_delete: str = None):
    """
    Отправка поста типа "видео" пользователю.
    :param interval_auto_delete:
    :param type_time_auto_delete:
    :param tag:
    :param user_id:
    :param channels:
    :param text:
    :param text_button:
    :param url_button:
    :param video_path:
    :return:
    """
    if text_button:
        for channel in channels:
            try:
                button_link = await create_button_for_post(text_button=text_button, url_button=url_button)
                message = await bot.send_video(chat_id=channel, caption=text, video=video_path, reply_markup=button_link)
                await create_cron_delete_message(message=message,
                                                 type_time_auto_delete=type_time_auto_delete,
                                                 interval_auto_delete=interval_auto_delete)
            except BadRequest:
                await bot.send_message(chat_id=user_id, text=f'Возникла ошибка с одним из постов, невалидный '
                                                             f'url: {url_button}')
                logger.warning(f'Возникла ошибка с текстовым постом, неверный url: {url_button}\n'
                               f'User id: {user_id}')
                traceback.print_exc()
    else:
        for channel in channels:
            message = await bot.send_video(chat_id=channel, caption=text, video=video_path)
            await create_cron_delete_message(message=message,
                                             type_time_auto_delete=type_time_auto_delete,
                                             interval_auto_delete=interval_auto_delete)

    msh.del_job(job_name=tag)
    post_db = PostDB()
    post_db.post_del(user_id=user_id, tag=tag)


async def send_album(tag: str, channels: list, posts: list, type_time_auto_delete: str, interval_auto_delete: str):
    media_group = MediaGroup()
    check_text = 0  # Текст добавляется лишь единожды, поэтому добавим такую переменную;)
    for attribute in posts:
        # tag = attribute[0]
        photo_id = attribute[1]
        video_id = attribute[2]
        text = attribute[3]

        if not check_text and text:
            if photo_id:
                media_group.attach_photo(photo=photo_id, caption=text)
            elif video_id:
                media_group.attach_video(video=video_id, caption=text)
            check_text += 1
        else:
            if photo_id:
                media_group.attach_photo(photo=photo_id)
            elif video_id:
                media_group.attach_video(video=video_id)

    for channel in channels:
        message = await bot.send_media_group(chat_id=channel, media=media_group)
        await create_cron_delete_message(message=message,
                                         type_time_auto_delete=type_time_auto_delete,
                                         interval_auto_delete=interval_auto_delete)

    msh.del_job(tag)
    individual_post_db = IndividualPostDB()
    if individual_post_db.exists_tag(tag=tag):
        individual_post_db.del_post_by_tag(tag=tag)


async def publication_post(tag: str,
                           user_id: int,
                           channels: list,
                           time: str,
                           day: int,
                           text_button: str | None = None,
                           url_button: str | None = None,
                           text: str | None = None,
                           photo=None,
                           video=None,
                           animation=None,
                           type_time_auto_delete=None,
                           interval_auto_delete=None) -> bool:
    """
    Задаем время и день вызова функции, которая опубликует пост в нужные каналы.
    :param interval_auto_delete:
    :param type_time_auto_delete:
    :param tag: Тег для отмены задачи
    :param user_id: ID пользователя
    :param channels: Список каналов.
    :param time: Время публикации.
    :param day: День публикации.
    :param text_button: Текст кнопки, если таковое имеется.
    :param url_button: Ссылка кнопки, если таковая имеется.
    :param text: Текст поста, если таковой имеется.
    :param photo: Фото поста, если таковое имеется.
    :param video: Видео поста, если таковое имеется.
    :param animation:
    :return: При возникновении ошибки ЛОЖЬ
    """
    try:
        if int(day) == 99:  # Сегодня
            if photo:
                job = CronJob(name=tag).day.at(time).go(send_photo, tag=tag, user_id=user_id,
                                                        channels=channels,
                                                        text=text, text_button=text_button,
                                                        url_button=url_button,
                                                        photo_path=photo,
                                                        interval_auto_delete=interval_auto_delete,
                                                        type_time_auto_delete=type_time_auto_delete)
            elif video:
                job = CronJob(name=tag).day.at(time).go(send_video, tag=tag, user_id=user_id,
                                                        channels=channels,
                                                        text=text, text_button=text_button,
                                                        url_button=url_button,
                                                        video_path=video,
                                                        interval_auto_delete=interval_auto_delete,
                                                        type_time_auto_delete=type_time_auto_delete)
            elif animation:
                job = CronJob(name=tag).day.at(time).go(send_animation, tag=tag, user_id=user_id,
                                                        channels=channels,
                                                        text=text, text_button=text_button,
                                                        url_button=url_button,
                                                        animation_path=animation,
                                                        interval_auto_delete=interval_auto_delete,
                                                        type_time_auto_delete=type_time_auto_delete)
            else:
                job = CronJob(name=tag).day.at(time).go(send_text, tag=tag, user_id=user_id, channels=channels,
                                                        text=text, text_button=text_button,
                                                        url_button=url_button,
                                                        interval_auto_delete=interval_auto_delete,
                                                        type_time_auto_delete=type_time_auto_delete)
        else:  # Понедельник, вторник и остальные дни.
            if photo:
                job = CronJob(name=tag).weekday(int(day)).at(time).go(send_photo, tag=tag, user_id=user_id,
                                                                      channels=channels,
                                                                      text=text, text_button=text_button,
                                                                      url_button=url_button,
                                                                      photo_path=photo,
                                                                      interval_auto_delete=interval_auto_delete,
                                                                      type_time_auto_delete=type_time_auto_delete)
            elif video:
                job = CronJob(name=tag).weekday(int(day)).at(time).go(send_video, tag=tag, user_id=user_id,
                                                                      channels=channels,
                                                                      text=text, text_button=text_button,
                                                                      url_button=url_button,
                                                                      video_path=video,
                                                                      interval_auto_delete=interval_auto_delete,
                                                                      type_time_auto_delete=type_time_auto_delete)
            elif animation:
                job = CronJob(name=tag).weekday(int(day)).at(time).go(send_animation, tag=tag, user_id=user_id,
                                                                      channels=channels,
                                                                      text=text, text_button=text_button,
                                                                      url_button=url_button,
                                                                      animation_path=animation,
                                                                      interval_auto_delete=interval_auto_delete,
                                                                      type_time_auto_delete=type_time_auto_delete)
            else:
                job = CronJob(name=tag).weekday(int(day)).at(time).go(send_text, tag=tag, user_id=user_id,
                                                                      channels=channels,
                                                                      text=text, text_button=text_button,
                                                                      url_button=url_button,
                                                                      interval_auto_delete=interval_auto_delete,
                                                                      type_time_auto_delete=type_time_auto_delete)
        msh.add_job(job)
        return True
    except Exception:
        traceback.print_exc()
        logger.warning(f'Возникла ошибка при publication post\n'
                       f'user id: {user_id}')
        return False
