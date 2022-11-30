import random

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def create_keyboard_channels(channels: list | tuple) -> InlineKeyboardMarkup:
    """
    Формирование InlineKeyboardMarkup из полученных channels конкретного user_id
    :param channels:
    :return:
    """
    channels_menu = InlineKeyboardMarkup(row_width=4)
    for attribute in channels:
        channel_id = str(attribute[0])
        channel_name = attribute[1]
        channel_button = InlineKeyboardButton(text=channel_name, callback_data=f'channels_donor_{channel_id}')
        channels_menu.insert(channel_button)
    stop_button = InlineKeyboardButton('🛑STOP🛑', callback_data='stop_fsm')
    channels_menu.add(stop_button)
    return channels_menu


async def create_keyboard_tagged_channels(channels: list | tuple, channels_tagged: list):
    """
    Формирование InlineKeyboardMarkup помеченных каналов из channels_tagged на основе channels конкретного user_id
    :param channels:
    :param user_id:
    :param channels_tagged: Помеченные каналы
    :return:
    """
    channels_menu = InlineKeyboardMarkup(row_width=4)
    i = 0
    for attribute in channels:
        channel_id = str(attribute[0])
        channel_name = attribute[1]
        if channel_id not in channels_tagged:
            channel_button = InlineKeyboardButton(text=channel_name, callback_data=f'channels_donor_{channel_id}')
            channels_menu.insert(channel_button)
        else:
            i += 1
            channel_button = InlineKeyboardButton(text=f'{channel_name}🥂',
                                                  callback_data=f'channels_donor_{channel_id}')
            channels_menu.insert(channel_button)
    if i != 0:
        next_button = InlineKeyboardButton(text='Далее', callback_data='channels_tagged_next_for_donor')
        channels_menu.add(next_button)

    stop_button = InlineKeyboardButton('🛑STOP🛑', callback_data='stop_fsm')
    channels_menu.add(stop_button)

    return channels_menu


async def create_type_time_keyboard() -> InlineKeyboardMarkup:
    type_time_menu = InlineKeyboardMarkup(row_width=3)
    types_times = ('Минуты', 'Часы', 'Дни')  # В последующем определяется в utilis -> publication_post_donor.py
    for type_time in types_times:
        time_button = InlineKeyboardButton(text=type_time, callback_data=f'type_time_{type_time}')
        type_time_menu.insert(time_button)
    stop_button = InlineKeyboardButton('🛑STOP🛑', callback_data='stop_fsm')
    type_time_menu.add(stop_button)
    return type_time_menu


async def create_interval_keyboard(type_time: str) -> InlineKeyboardMarkup:
    interval_menu = InlineKeyboardMarkup(row_width=4)
    snow = '🎅'
    if type_time == 'Минуты':
        minutes = ('5', '10', '15', '20', '25', '30', '35', '40', '45', '55')
        number_snow = random.randint(0, len(minutes) - 1)
        for i, minute in enumerate(minutes, 0):
            if i == number_snow:
                minute += snow
            minute_button = InlineKeyboardButton(text=minute + ' мин', callback_data=f'interval_{minute}')
            interval_menu.insert(minute_button)
    elif type_time == 'Часы':
        hours = ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18',
                 '19', '20', '21', '22', '23')
        for hour in hours:
            hour_button = InlineKeyboardButton(text=hour + ' ч', callback_data=f'interval_{hour}')
            interval_menu.insert(hour_button)
    else:  # Дни
        days = ('1', '2', '3', '4', '5')
        for day in days:
            day_button = InlineKeyboardButton(text=day + ' дня(-ень, -ней)', callback_data=f'interval_{day}')
            interval_menu.add(day_button)
    return interval_menu


async def delete_post_keyboard() -> InlineKeyboardMarkup:
    delete_post_menu = InlineKeyboardMarkup(row_width=1)
    delete_post_button = InlineKeyboardButton(text='Удалить пост', callback_data=f'delete_post')
    delete_post_menu.insert(delete_post_button)
    return delete_post_menu
