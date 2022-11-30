from async_cron.job import CronJob

from create_bot.bot import bot
from databases.client import DonorPostDB
from utils.create_cron import msh


async def send_message(tag: str, channels: list):
    post_donor_db = DonorPostDB()
    posts = post_donor_db.get_posts_by_tag(tag=tag)
    if posts:
        for attribute_post in posts:
            # attribute_post[1] - tag

            # get data
            pk = attribute_post[0]
            photo_id = attribute_post[2]
            video_id = attribute_post[3]
            animation_id = attribute_post[4]
            text = attribute_post[5]
            video_note = attribute_post[6]

            # del post
            post_donor_db.del_post_by_pk(pk)

            # send message in channels
            if photo_id:
                for channel in channels:
                    await bot.send_photo(chat_id=channel, photo=photo_id, caption=text)
            elif video_id:
                for channel in channels:
                    await bot.send_video(chat_id=channel, video=video_id, caption=text)
            elif animation_id:
                for channel in channels:
                    await bot.send_animation(chat_id=channel, animation=animation_id, caption=text)
            elif video_note:
                for channel in channels:
                    await bot.send_video_note(chat_id=channel, video_note=video_note)
            else:
                for channel in channels:
                    await bot.send_message(chat_id=channel, text=text)
            break
    else:
        msh.del_job(job_name=tag)


async def publication_post_donor(tag: str,
                                 user_id: int,
                                 channels: list,
                                 type_time: str,
                                 interval: str):
    """
    Публикация постов из канала донора в каналы, которые указал пользователь.
    :param tag:
    :param user_id: ID пользователя.
    :param channels: Каналы которые указал пользователь.
    :param type_time: Тип времени (минуты, часы, день).
    :param interval: Интервал, с которым будут опубликовываться в каналы посты.
    :return:
    """
    if type_time == 'Минуты':
        job = CronJob(name=tag).every(int(interval)).minute.go(send_message, tag=tag, channels=channels)
    elif type_time == 'Часы':
        job = CronJob(name=tag).every(int(interval)).hour.go(send_message, tag=tag, channels=channels)
    else:
        job = CronJob(name=tag).every(int(interval)).day.go(send_message, tag=tag, channels=channels)
    msh.add_job(job)
