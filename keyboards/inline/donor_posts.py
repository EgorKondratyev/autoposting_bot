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
            channel_button = InlineKeyboardButton(text=f'{channel_name}🔮',
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
    # В последующем определяется в utilis -> publication_post_donor.py
    types_times = ('Минуты', 'Часы', 'Дни')
    for type_time in types_times:
        time_button = InlineKeyboardButton(text=type_time, callback_data=f'type_time_{type_time}')
        type_time_menu.insert(time_button)
    arbitrary_type_button = InlineKeyboardButton(text='Произвольный интервал', callback_data='type_time_arbitrary')
    schedule_interval_button = InlineKeyboardButton(text='Интервал с расписанием', callback_data='type_time_schedule')
    stop_button = InlineKeyboardButton('🛑STOP🛑', callback_data='stop_fsm')
    type_time_menu.add(arbitrary_type_button).add(schedule_interval_button).add(stop_button)
    return type_time_menu


async def create_interval_keyboard(type_time: str) -> InlineKeyboardMarkup:
    interval_menu = InlineKeyboardMarkup(row_width=4)
    snow = '🧃'
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


async def create_schedule_day_keyboard() -> InlineKeyboardMarkup:
    schedule_day_menu = InlineKeyboardMarkup(row_width=5)
    days = ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
            '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30')
    for day in days:
        day_button = InlineKeyboardButton(text=day, callback_data=f'schedule_day_{day}')
        schedule_day_menu.insert(day_button)

    return schedule_day_menu


async def delete_post_keyboard() -> InlineKeyboardMarkup:
    delete_post_menu = InlineKeyboardMarkup(row_width=1)
    delete_post_button = InlineKeyboardButton(text='Удалить пост', callback_data=f'delete_post')
    delete_post_menu.insert(delete_post_button)
    return delete_post_menu


async def create_confirm_keyboards(**kwargs) -> InlineKeyboardMarkup:
    confirm_menu = InlineKeyboardMarkup(row_width=1)
    if kwargs.get('delete_text'):
        add_delete_text_post_button = InlineKeyboardButton('Удалить текст доноров✅',
                                                           callback_data='confirm_donor_delete_text_yes')
    else:
        add_delete_text_post_button = InlineKeyboardButton('Удалить текст доноров',
                                                           callback_data='confirm_donor_delete_text')
    if kwargs.get('add_description'):
        add_description_button = InlineKeyboardButton('Добавить описание всем постам✅',
                                                      callback_data='confirm_donor_add_description_yes')
    else:
        add_description_button = InlineKeyboardButton('Добавить описание всем постам',
                                                      callback_data='confirm_donor_add_description')
    if kwargs.get('mix_post'):
        mix_posts_button = InlineKeyboardButton('Перемешать посты✅', callback_data='confirm_donor_mix_post_yes')
    else:
        mix_posts_button = InlineKeyboardButton('Перемешать посты', callback_data='confirm_donor_mix_post')
    if kwargs.get('buttons'):
        add_urls_button = InlineKeyboardButton('Добавить кнопки к постам✅',
                                               callback_data='confirm_donor_add_urls_yes')
    else:
        add_urls_button = InlineKeyboardButton('Добавить кнопки к постам', callback_data='confirm_donor_add_urls')
    if kwargs.get('auto_delete'):
        auto_delete_posts_button = InlineKeyboardButton('Добавить авто удаление постов✅',
                                                        callback_data='confirm_donor_auto_delete_posts_yes')
    else:
        auto_delete_posts_button = InlineKeyboardButton('Добавить авто удаление постов',
                                                        callback_data='confirm_donor_auto_delete_posts')
    if kwargs.get('preview_link'):
        preview_link = InlineKeyboardButton('Добавить предпросмотр ссылки✅',
                                            callback_data='confirm_donor_preview_link_yes')
    else:
        preview_link = InlineKeyboardButton('Добавить предпросмотр ссылки',
                                            callback_data='confirm_donor_preview_link')
    confirm_button = InlineKeyboardButton('Начать публикацию🏄‍♂️', callback_data='confirm_donor_start_pub')
    stop_button = InlineKeyboardButton('🛑STOP🛑', callback_data='stop_fsm')
    confirm_menu.insert(add_delete_text_post_button).insert(add_description_button).insert(mix_posts_button).\
        insert(add_urls_button).insert(auto_delete_posts_button).insert(preview_link).insert(confirm_button).\
        add(stop_button)
    return confirm_menu


async def create_buttons_url(buttons: list[dict]) -> InlineKeyboardMarkup:
    """
    Создает InlineKeyboardMarkup из buttons (buttons формируем на этапе дополнительного меню).
    :param buttons: [{name_button: url_button}, ..., {name_button: url_button}]
    :return:
    """
    menu_buttons = InlineKeyboardMarkup(row_width=1)
    for button in buttons:
        for name_button, url in button.items():
            url_button = InlineKeyboardButton(text=name_button, url=url)
            menu_buttons.insert(url_button)

    return menu_buttons


async def create_type_time_keyboard_for_delete_posts():
    type_time_menu = InlineKeyboardMarkup(row_width=3)
    types_times = ('Минуты', 'Часы', 'Дни')
    for type_time in types_times:
        time_button = InlineKeyboardButton(text=type_time, callback_data=f'autodelete_donor_type_time_{type_time}')
        type_time_menu.insert(time_button)
    return type_time_menu


async def create_interval_keyboard_for_delete_post(type_time: str) -> InlineKeyboardMarkup:
    interval_menu = InlineKeyboardMarkup(row_width=4)
    snow = '🍑'
    if type_time == 'Минуты':
        minutes = ('5', '10', '15', '20', '25', '30', '35', '40', '45', '55')
        number_snow = random.randint(0, len(minutes) - 1)
        for i, minute in enumerate(minutes, 0):
            if i == number_snow:
                minute += snow
            minute_button = InlineKeyboardButton(text=minute + ' мин',
                                                 callback_data=f'autodelete_donor_interval_{minute}')
            interval_menu.insert(minute_button)
    elif type_time == 'Часы':
        hours = ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18',
                 '19', '20', '21', '22', '23')
        for hour in hours:
            hour_button = InlineKeyboardButton(text=hour + ' ч', callback_data=f'autodelete_donor_interval_{hour}')
            interval_menu.insert(hour_button)
    else:  # Дни
        days = ('1', '2', '3', '4', '5')
        for day in days:
            day_button = InlineKeyboardButton(text=day + ' дня(-ень, -ней)',
                                              callback_data=f'autodelete_donor_interval_{day}')
            interval_menu.add(day_button)
    return interval_menu
