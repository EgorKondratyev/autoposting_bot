import asyncio
import random
import traceback

from aiogram.types import MediaGroup, InlineKeyboardMarkup
from async_cron.job import CronJob

from create_bot.bot import bot
from databases.client import DonorPostDB
from utils.create_cron import msh
from utils.generate_random_tag import generate_random_tag_md5
from log.create_logger import logger


async def delete_messages(tag, message, type_time_auto_delete, interval_auto_delete):
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
    """
    # Задаем время авто удаления сообщения, если таковое имеется
    :param message: Пост.
    :param type_time_auto_delete: Тип времени.
    :param interval_auto_delete: Интервал времени.
    :return:
    """
    # at в async cron сломан, чтобы не юзать доп крон, воспользовался костылем (в кроне sleep):
    if type_time_auto_delete and interval_auto_delete:
        tag = await generate_random_tag_md5()
        job = CronJob(tag, run_total=1).every(1).second.go(delete_messages, tag=tag, message=message,
                                                           type_time_auto_delete=type_time_auto_delete,
                                                           interval_auto_delete=interval_auto_delete)
        msh.add_job(job)


async def send_message(tag: str, channels: list, type_time_auto_delete: str, interval_auto_delete: str,
                       buttons: InlineKeyboardMarkup | None, description: str | None, mix_post: bool | None,
                       delete_text: bool | None):
    post_donor_db = DonorPostDB()
    posts = post_donor_db.get_posts_by_tag(tag=tag)
    if posts:
        if mix_post:
            random.shuffle(posts)
        for attribute_post in posts:
            # attribute_post[1] - tag

            # get data
            pk = attribute_post[0]
            photo_id = attribute_post[2]
            video_id = attribute_post[3]
            animation_id = attribute_post[4]
            text = attribute_post[5]
            if description and not delete_text:
                text += f'\n\n{description}'
            elif delete_text:
                text = description
            video_note = attribute_post[6]
            group_media_id = attribute_post[9]
            # Отправка альбома
            if group_media_id:
                posts_group = post_donor_db.get_posts_by_grop_media_id(group_media_id=group_media_id)
                # del media group
                post_donor_db.del_post_by_group_media_id(group_media_id=group_media_id)
                media_group = MediaGroup()
                check_text = 0  # Текст добавляется лишь единожды, поэтому добавим такую переменную;)
                for attribute_post_group in posts_group:
                    photo_id = attribute_post_group[2]
                    video_id = attribute_post_group[3]
                    text = attribute_post_group[5]
                    if description and not delete_text:
                        text += f'\n\n{description}'
                    elif delete_text:
                        text = description
                    # Добавляем текст к альбому, если таковой есть
                    if not check_text and text:
                        if photo_id:
                            media_group.attach_photo(photo=photo_id, caption=text, parse_mode='html')
                        elif video_id:
                            media_group.attach_video(video=video_id, caption=text, parse_mode='html')
                        check_text += 1
                    else:
                        if photo_id:
                            media_group.attach_photo(photo=photo_id)
                        elif video_id:
                            media_group.attach_video(video=video_id)
                try:
                    for channel in channels:
                        message = await bot.send_media_group(chat_id=channel, media=media_group)
                        logger.debug('Успешная отправка альбмного донора-поста')
                        await create_cron_delete_message(message=message,
                                                         type_time_auto_delete=type_time_auto_delete,
                                                         interval_auto_delete=interval_auto_delete)
                except Exception as ex:
                    traceback.print_exc()
                    logger.warning(f'Возникла ошибка при отправке сообщения-альбома в доноре постов\n\n'
                                   f'{ex}')
            # Отправка обычного сообщения
            else:
                # del post
                post_donor_db.del_post_by_pk(pk)

                if photo_id:
                    for channel in channels:
                        if buttons:
                            message = await bot.send_photo(chat_id=channel, photo=photo_id, caption=text,
                                                           reply_markup=buttons, parse_mode='html')
                        else:
                            message = await bot.send_photo(chat_id=channel, photo=photo_id, caption=text,
                                                           parse_mode='html')

                        await create_cron_delete_message(message=message,
                                                         type_time_auto_delete=type_time_auto_delete,
                                                         interval_auto_delete=interval_auto_delete)
                elif video_id:
                    for channel in channels:
                        if buttons:
                            message = await bot.send_video(chat_id=channel, video=video_id, caption=text,
                                                           reply_markup=buttons, parse_mode='html')
                        else:
                            message = await bot.send_video(chat_id=channel, video=video_id, caption=text,
                                                           parse_mode='html')

                        await create_cron_delete_message(message=message,
                                                         type_time_auto_delete=type_time_auto_delete,
                                                         interval_auto_delete=interval_auto_delete)
                elif animation_id:
                    for channel in channels:
                        if buttons:
                            message = await bot.send_animation(chat_id=channel, animation=animation_id, caption=text,
                                                               reply_markup=buttons, parse_mode='html')
                        else:
                            message = await bot.send_animation(chat_id=channel, animation=animation_id, caption=text,
                                                               parse_mode='html')
                        await create_cron_delete_message(message=message,
                                                         type_time_auto_delete=type_time_auto_delete,
                                                         interval_auto_delete=interval_auto_delete)
                elif video_note:
                    for channel in channels:
                        if buttons:
                            message = await bot.send_video_note(chat_id=channel, video_note=video_note,
                                                                reply_markup=buttons)
                        else:
                            message = await bot.send_video_note(chat_id=channel, video_note=video_note)
                        await create_cron_delete_message(message=message,
                                                         type_time_auto_delete=type_time_auto_delete,
                                                         interval_auto_delete=interval_auto_delete)
                else:  # text
                    for channel in channels:
                        if buttons:
                            message = await bot.send_message(chat_id=channel, text=text, reply_markup=buttons,
                                                             parse_mode='html')
                        else:
                            message = await bot.send_message(chat_id=channel, text=text, parse_mode='html')
                        await create_cron_delete_message(message=message,
                                                         type_time_auto_delete=type_time_auto_delete,
                                                         interval_auto_delete=interval_auto_delete)
            break
    else:
        msh.del_job(job_name=tag)


async def create_cron_for_schedule(schedule_times: list, tag: str, channels: list, type_time_auto_delete: str,
                                   interval_auto_delete: str,
                                   buttons: InlineKeyboardMarkup | None, description: str | None, mix_post: bool | None,
                                   delete_text: bool | None):
    try:
        for time in schedule_times:
            # Несколько задач не могут иметь один и тот же тег, поэтому формируем для каждого тайминга свой тег
            tag_schedule = await generate_random_tag_md5()
            job = CronJob(name=tag_schedule).every().day.at(time).go(send_message, tag=tag, channels=channels,
                                                                     type_time_auto_delete=type_time_auto_delete,
                                                                     interval_auto_delete=interval_auto_delete,
                                                                     buttons=buttons,
                                                                     description=description, mix_post=mix_post,
                                                                     delete_text=delete_text)
            msh.add_job(job)
    except Exception as ex:
        logger.warning(f'Возникла ошибка при формировании расписания в функции "create_cron_for_schedule"\n'
                       f'{ex}')
        msh.del_job(tag)
        post_donor_db = DonorPostDB()
        post_donor_db.del_post_by_tag(tag=tag)


async def publication_post_donor(tag: str,
                                 channels: list,
                                 type_time: str,
                                 interval: str,
                                 type_time_auto_delete: str,
                                 interval_auto_delete: str,
                                 first_type_time: str,
                                 first_interval: str,
                                 second_type_time: str,
                                 second_interval: str,
                                 buttons: InlineKeyboardMarkup | None,
                                 description: str | None,
                                 mix_post: bool | None,
                                 delete_text: bool | None,
                                 schedule_day: str | None,
                                 schedule_times: list | None):
    """
    Публикация постов из канала донора в каналы, которые указал пользователь.
    :param schedule_day: День начала постинга по расписанию
    :param schedule_times: Время постинга по расписанию
    :param delete_text:
    :param mix_post:
    :param description:
    :param buttons: Кнопки, прикрепляемые к постам.
    :param second_interval: Произвольный интервал 2
    :param second_type_time: Тип времени, которым будет заканчиваться произвольный интервал
    :param first_interval: Произвольный интервал 1
    :param first_type_time: Тип времени, с которого будет начинаться произвольный интервал
    :param interval_auto_delete:
    :param type_time_auto_delete:
    :param tag:
    :param channels: Каналы которые указал пользователь.
    :param type_time: Тип времени (минуты, часы, день).
    :param interval: Интервал, с которым будут опубликовываться в каналы посты.
    :return:
    """
    if type_time == 'Минуты':
        if '🎅' in interval:
            interval = interval[:-1]
        job = CronJob(name=tag).every(int(interval)).minute.go(send_message, tag=tag, channels=channels,
                                                               type_time_auto_delete=type_time_auto_delete,
                                                               interval_auto_delete=interval_auto_delete,
                                                               buttons=buttons,
                                                               description=description, mix_post=mix_post,
                                                               delete_text=delete_text)
    elif type_time == 'Часы':
        job = CronJob(name=tag).every(int(interval)).hour.go(send_message, tag=tag, channels=channels,
                                                             type_time_auto_delete=type_time_auto_delete,
                                                             interval_auto_delete=interval_auto_delete, buttons=buttons,
                                                             description=description, mix_post=mix_post,
                                                             delete_text=delete_text)
    elif type_time == 'Дни':
        job = CronJob(name=tag).every(int(interval)).day.go(send_message, tag=tag, channels=channels,
                                                            type_time_auto_delete=type_time_auto_delete,
                                                            interval_auto_delete=interval_auto_delete, buttons=buttons,
                                                            description=description, mix_post=mix_post,
                                                            delete_text=delete_text)
    elif type_time == 'schedule':
        job = CronJob(name=tag, run_total=1).monthday(int(schedule_day)).go(create_cron_for_schedule, tag=tag,
                                                                            channels=channels,
                                                                            type_time_auto_delete=type_time_auto_delete,
                                                                            interval_auto_delete=interval_auto_delete,
                                                                            buttons=buttons,
                                                                            description=description, mix_post=mix_post,
                                                                            delete_text=delete_text,
                                                                            schedule_times=schedule_times)
    else:  # Произвольный интервал, формирование
        if first_type_time == 'м' and second_type_time == 'м':  # 1
            interval = random.randint(int(first_interval), int(second_interval))
            job = CronJob(name=tag).every(interval).minute.go(send_message, tag=tag, channels=channels,
                                                              type_time_auto_delete=type_time_auto_delete,
                                                              interval_auto_delete=interval_auto_delete,
                                                              buttons=buttons, description=description,
                                                              mix_post=mix_post, delete_text=delete_text)
        elif first_type_time == 'ч' and second_type_time == 'ч':  # 2
            interval = random.randint(int(first_interval), int(second_interval))
            job = CronJob(name=tag).every(int(interval)).hour.go(send_message, tag=tag, channels=channels,
                                                                 type_time_auto_delete=type_time_auto_delete,
                                                                 interval_auto_delete=interval_auto_delete,
                                                                 buttons=buttons, description=description,
                                                                 mix_post=mix_post, delete_text=delete_text)
        elif first_type_time == 'д' and second_type_time == 'д':  # 3
            interval = random.randint(int(first_interval), int(second_interval))
            job = CronJob(name=tag).every(int(interval)).day.go(send_message, tag=tag, channels=channels,
                                                                type_time_auto_delete=type_time_auto_delete,
                                                                interval_auto_delete=interval_auto_delete,
                                                                buttons=buttons, description=description,
                                                                mix_post=mix_post, delete_text=delete_text)
        elif first_type_time == 'м' and second_type_time == 'д':  # 4
            days_in_minutes = int(second_interval) * 1440
            interval = random.randint(int(first_interval), days_in_minutes)
            job = CronJob(name=tag).every(interval).minute.go(send_message, tag=tag, channels=channels,
                                                              type_time_auto_delete=type_time_auto_delete,
                                                              interval_auto_delete=interval_auto_delete,
                                                              buttons=buttons, description=description,
                                                              mix_post=mix_post, delete_text=delete_text)
        elif first_type_time == 'м' and second_type_time == 'ч':  # 5
            hours_in_minutes = int(second_interval) * 60
            interval = random.randint(int(first_interval), hours_in_minutes)
            job = CronJob(name=tag).every(interval).minute.go(send_message, tag=tag, channels=channels,
                                                              type_time_auto_delete=type_time_auto_delete,
                                                              interval_auto_delete=interval_auto_delete,
                                                              buttons=buttons, description=description,
                                                              mix_post=mix_post, delete_text=delete_text)
        elif first_type_time == 'ч' and second_type_time == 'д':  # 6
            days_in_hours = int(second_interval) * 24
            interval = random.randint(int(first_interval), days_in_hours)
            job = CronJob(name=tag).every(int(interval)).hour.go(send_message, tag=tag, channels=channels,
                                                                 type_time_auto_delete=type_time_auto_delete,
                                                                 interval_auto_delete=interval_auto_delete,
                                                                 buttons=buttons, description=description,
                                                                 mix_post=mix_post, delete_text=delete_text)
        else:
            return 2
    msh.add_job(job)
