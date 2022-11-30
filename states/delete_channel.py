from aiogram.dispatcher.filters.state import State, StatesGroup


class DeleteChannelFSM(StatesGroup):
    get_id_channel = State()
