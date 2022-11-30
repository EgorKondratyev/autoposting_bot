from aiogram.dispatcher.filters.state import State, StatesGroup


class DonorPostsFSM(StatesGroup):
    get_channels = State()
    get_type_time = State()
    get_interval = State()
    get_posts = State()
    confirm = State()
