from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


create_start_menu = InlineKeyboardMarkup(row_width=1)
add_channel_button = InlineKeyboardButton(text='Добавить канал', callback_data='start_add_channel')
delete_channel_button = InlineKeyboardButton(text='Удалить канал', callback_data='start_delete_channel')
create_post_button = InlineKeyboardButton(text='Создать пост', callback_data='start_create_post')
post_in_turn = InlineKeyboardButton(text='Посты из донора', callback_data='start_post_in_turn')
cancel_posts = InlineKeyboardButton(text='Отмена постов', callback_data='start_cancel_posts')
cancel_donor_posts = InlineKeyboardButton(text='Отмена постов-доноров', callback_data='start_cancel_donor_posts')
create_start_menu.insert(add_channel_button).insert(delete_channel_button).insert(create_post_button).\
    insert(post_in_turn).insert(cancel_posts).insert(cancel_donor_posts)
