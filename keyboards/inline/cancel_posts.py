from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def create_cancel_posts_keyboard(posts: list) -> InlineKeyboardMarkup:
    posts_menu = InlineKeyboardMarkup(row_width=2)
    for attribute in posts:
        post = attribute[0]
        post_button = InlineKeyboardButton(text=post, callback_data=f'cancel_job_{post}')
        posts_menu.insert(post_button)
    stop_button = InlineKeyboardButton('🛑STOP🛑', callback_data='stop_fsm')
    posts_menu.add(stop_button)
    return posts_menu
