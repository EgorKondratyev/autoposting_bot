from aiogram.dispatcher.filters.state import State, StatesGroup


class CancelPostFSM(StatesGroup):
    get_post = State()
    confirm = State()
