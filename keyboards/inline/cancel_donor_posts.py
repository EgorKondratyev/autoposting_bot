from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def create_cancel_donor_posts_keyboard(posts: list) -> InlineKeyboardMarkup:
    cancel_donor_posts_menu = InlineKeyboardMarkup(row_width=2)
    for attribute in posts:
        tag = attribute[0]
        cancel_donor_post_button = InlineKeyboardButton(text=tag, callback_data=f'cancel_donor_{tag}')
        cancel_donor_posts_menu.insert(cancel_donor_post_button)
    stop_button = InlineKeyboardButton('🛑STOP🛑', callback_data='stop_fsm')
    cancel_donor_posts_menu.add(stop_button)
    return cancel_donor_posts_menu
