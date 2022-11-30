from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


confirmation_donor_posts_menu = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
stop_button = KeyboardButton(text='Остановить❌')
confirmation_button = KeyboardButton(text='Продолжить🚀')
confirmation_donor_posts_menu.insert(confirmation_button).insert(stop_button)
