from aiogram.dispatcher.filters.state import State, StatesGroup


class CancelDonorFSM(StatesGroup):
    get_post = State()
    confirm = State()
