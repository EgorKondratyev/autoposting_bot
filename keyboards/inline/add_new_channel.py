from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


confirm_add_channel_menu = InlineKeyboardMarkup(row_width=1)
confirm_add_channel_button = InlineKeyboardButton(text='Добавить канал✅', callback_data='add_channel_confirm')
cancel_add_channel_button = InlineKeyboardButton(text='Отмена❌', callback_data='add_channel_cancel')
confirm_add_channel_menu.insert(confirm_add_channel_button).insert(cancel_add_channel_button)
