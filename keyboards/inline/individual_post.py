import random

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Хочет ли пользователь добавить кнопку к своему посту:
create_url_menu = InlineKeyboardMarkup(row_width=2)
yes_button = InlineKeyboardButton(text='Да', callback_data='create_url_yes')
no_button = InlineKeyboardButton(text='Нет', callback_data='create_url_no')
create_url_menu.insert(yes_button).insert(no_button)


async def create_keyboard_channels(channels: list | tuple, user_id: int) -> InlineKeyboardMarkup:
    """
    Формирование InlineKeyboardMarkup из полученных channels конкретного user_id
    :param channels:
    :param user_id:
    :return:
    """
    channels_menu = InlineKeyboardMarkup(row_width=4)
    for attribute in channels:
        channel_id = str(attribute[0])
        channel_name = attribute[1]
        channel_button = InlineKeyboardButton(text=channel_name, callback_data=f'channels_{channel_id}_{user_id}')
        channels_menu.insert(channel_button)
    stop_button = InlineKeyboardButton('🛑STOP🛑', callback_data='stop_fsm')
    channels_menu.add(stop_button)
    return channels_menu


async def create_keyboard_tagged_channels(channels: list | tuple, user_id: int, channels_tagged: list):
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
            channel_button = InlineKeyboardButton(text=channel_name, callback_data=f'channels_{channel_id}_{user_id}')
            channels_menu.insert(channel_button)
        else:
            i += 1
            channel_button = InlineKeyboardButton(text=f'{channel_name}☃️',
                                                  callback_data=f'channels_{channel_id}_{user_id}')
            channels_menu.insert(channel_button)
    if i != 0:
        next_button = InlineKeyboardButton(text='Далее', callback_data='channels_tagged_next')
        channels_menu.add(next_button)

    stop_button = InlineKeyboardButton('🛑STOP🛑', callback_data='stop_fsm')
    channels_menu.add(stop_button)

    return channels_menu


async def create_keyboard_time_24_hours() -> InlineKeyboardMarkup:
    """
    Формирование InlineKeyboardMarkup, которая состоит из 24 временных промежутков.
    :return:
    """
    time_menu = InlineKeyboardMarkup(row_width=4)
    hours = [
        '00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
        '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00',
    ]
    snow = '❄️'
    random_snow = random.randint(0, len(hours))
    for i, hour in enumerate(hours):
        if random_snow != i:
            hour_button = InlineKeyboardButton(text=hour, callback_data=f'time_{hour}')
        else:
            hour_button = InlineKeyboardButton(text=hour + snow, callback_data=f'time_{hour}')
        time_menu.insert(hour_button)
    return time_menu


async def create_keyboard_day() -> InlineKeyboardMarkup:
    """
    Формирование дней, в которые будет опубликован пост.
    :return:
    """
    day_menu = InlineKeyboardMarkup(row_width=1)
    days = {99: 'Сегодня', 0: 'Понедельник', 1: 'Вторник', 2: 'Среда', 3: 'Четверг', 4: 'Пятница', 5: 'Суббота',
            6: 'Воскресенье'}
    for index_day, day in days.items():
        day_button = InlineKeyboardButton(text=f'{day}', callback_data=f'day_{index_day}')
        day_menu.insert(day_button)
    return day_menu


async def create_confirm_post() -> InlineKeyboardMarkup:
    """
    Создание InlineKeyboardMarkup, который будет отвечать за последний шаг подтверждения, перед публикацией поста.
    :return:
    """
    confirm_menu = InlineKeyboardMarkup(row_width=1)
    preview_button = InlineKeyboardButton(text='Предпросмотр', callback_data='confirm_individual_preview')
    get_time_button = InlineKeyboardButton(text='Просмотр времени', callback_data='confirm_individual_time')
    get_channels_button = InlineKeyboardButton(text='Просмотр каналов', callback_data='confirm_individual_channels')
    next_button = InlineKeyboardButton(text='Подтвердить публикацию', callback_data='confirm_individual_next')
    stop_button = InlineKeyboardButton('🛑STOP🛑', callback_data='stop_fsm')
    confirm_menu.insert(preview_button).insert(get_time_button).insert(get_channels_button).\
        insert(next_button).insert(stop_button)
    return confirm_menu


async def create_button_for_post(text_button, url_button) -> InlineKeyboardMarkup:
    """
    Создание InlineKeyboardMarkup для конечного поста пользователя
    :param text_button:
    :param url_button:
    :return:
    """
    button_for_post_menu = InlineKeyboardMarkup(row_width=1)
    button = InlineKeyboardButton(text=text_button, url=url_button)
    button_for_post_menu.insert(button)
    return button_for_post_menu
