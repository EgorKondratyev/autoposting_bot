from aiogram.dispatcher.filters.state import State, StatesGroup


class CancelPostChannelFSM(StatesGroup):
    get_id_channel = State()
    confirm = State()
