import asyncio
import traceback

from aiogram.types import MediaGroup
from async_cron.job import CronJob
from aiogram.utils.exceptions import BadRequest

from create_bot.bot import bot
from databases.client import PostDB
from keyboards.inline.individual_post import create_button_for_post
from log.create_logger import logger
from utils.create_cron import msh


async def send_text(tag, user_id: int, channels: list, text: str, text_button: str | None = None,
                    url_button: str | None = None):
    """
    Отправка поста типа "текст" пользователю.
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
                await bot.send_message(chat_id=channel, text=text, reply_markup=button_link)
                await asyncio.sleep(1)
            except BadRequest:
                await bot.send_message(chat_id=user_id, text=f'Возникла ошибка с одним из постов, невалидный '
                                                             f'url: {url_button}')
                logger.warning(f'Возникла ошибка с текстовым постом, неверный url: {url_button}\n'
                               f'User id: {user_id}')
                traceback.print_exc()
    else:
        for channel in channels:
            await bot.send_message(chat_id=channel, text=text)
            await asyncio.sleep(1)

    msh.del_job(tag)
    post_db = PostDB()
    post_db.post_del(user_id=user_id, tag=tag)


async def send_photo(tag, user_id: int, channels: list, text, text_button: str | None = None,
                     url_button: str | None = None, photo_path: str | None = None):
    """
    Отправка поста типа "фото" пользователю.
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
                await bot.send_photo(chat_id=channel, caption=text, photo=photo_path, reply_markup=button_link)
                await asyncio.sleep(1)
            except BadRequest:
                await bot.send_message(chat_id=user_id, text=f'Возникла ошибка с одним из постов, невалидный '
                                                             f'url: {url_button}')
                logger.warning(f'Возникла ошибка с текстовым постом, неверный url: {url_button}\n'
                               f'User id: {user_id}')
                traceback.print_exc()
    else:
        for channel in channels:
            await bot.send_photo(chat_id=channel, caption=text, photo=photo_path)
            await asyncio.sleep(1)

    msh.del_job(job_name=tag)
    post_db = PostDB()
    post_db.post_del(user_id=user_id, tag=tag)


async def send_animation(tag, user_id: int, channels: list, text, text_button: str | None = None,
                         url_button: str | None = None, animation_path: str | None = None):
    """
    Отправка поста типа "GIF, animation" пользователю.
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
                await bot.send_animation(animation=animation_path, chat_id=channel, caption=text,
                                         reply_markup=button_link)
                await asyncio.sleep(1)
            except BadRequest:
                await bot.send_message(chat_id=user_id, text=f'Возникла ошибка с одним из постов, невалидный '
                                                             f'url: {url_button}')
                logger.warning(f'Возникла ошибка с текстовым постом, неверный url: {url_button}\n'
                               f'User id: {user_id}')
                traceback.print_exc()
    else:
        for channel in channels:
            await bot.send_animation(chat_id=channel, caption=text, animation=animation_path)
            await asyncio.sleep(1)

    msh.del_job(job_name=tag)
    post_db = PostDB()
    post_db.post_del(user_id=user_id, tag=tag)


async def send_video(tag, user_id: int, channels: list, text, text_button: str | None = None,
                     url_button: str | None = None, video_path: str | None = None):
    """
    Отправка поста типа "видео" пользователю.
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
                await bot.send_video(chat_id=channel, caption=text, video=video_path, reply_markup=button_link)
            except BadRequest:
                await bot.send_message(chat_id=user_id, text=f'Возникла ошибка с одним из постов, невалидный '
                                                             f'url: {url_button}')
                logger.warning(f'Возникла ошибка с текстовым постом, неверный url: {url_button}\n'
                               f'User id: {user_id}')
                traceback.print_exc()
    else:
        for channel in channels:
            await bot.send_video(chat_id=channel, caption=text, video=video_path)

    msh.del_job(job_name=tag)
    post_db = PostDB()
    post_db.post_del(user_id=user_id, tag=tag)


async def send_album(tag: str, channels: list, posts: list):
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

    msh.del_job(tag)


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
                           animation=None) -> bool:
    """
    Задаем время и день вызова функции, которая опубликует пост в нужные каналы.
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
                                                        photo_path=photo)
            elif video:
                job = CronJob(name=tag).day.at(time).go(send_video, tag=tag, user_id=user_id,
                                                        channels=channels,
                                                        text=text, text_button=text_button,
                                                        url_button=url_button,
                                                        video_path=video)
            elif animation:
                job = CronJob(name=tag).day.at(time).go(send_animation, tag=tag, user_id=user_id,
                                                        channels=channels,
                                                        text=text, text_button=text_button,
                                                        url_button=url_button,
                                                        animation_path=animation)
            else:
                job = CronJob(name=tag).day.at(time).go(send_text, tag=tag, user_id=user_id, channels=channels,
                                                        text=text, text_button=text_button,
                                                        url_button=url_button)
        else:  # Понедельник, вторник и остальные дни.
            if photo:
                job = CronJob(name=tag).weekday(int(day)).at(time).go(send_photo, tag=tag, user_id=user_id,
                                                                      channels=channels,
                                                                      text=text, text_button=text_button,
                                                                      url_button=url_button,
                                                                      photo_path=photo)
            elif video:
                job = CronJob(name=tag).weekday(int(day)).at(time).go(send_video, tag=tag, user_id=user_id,
                                                                      channels=channels,
                                                                      text=text, text_button=text_button,
                                                                      url_button=url_button,
                                                                      video_path=video)
            elif animation:
                job = CronJob(name=tag).weekday(int(day)).at(time).go(send_animation, tag=tag, user_id=user_id,
                                                                      channels=channels,
                                                                      text=text, text_button=text_button,
                                                                      url_button=url_button,
                                                                      animation_path=animation)
            else:
                job = CronJob(name=tag).weekday(int(day)).at(time).go(send_text, tag=tag, user_id=user_id,
                                                                      channels=channels,
                                                                      text=text, text_button=text_button,
                                                                      url_button=url_button)
        msh.add_job(job)
        return True
    except Exception:
        traceback.print_exc()
        logger.warning(f'Возникла ошибка при publication post\n'
                       f'user id: {user_id}')
        return False
