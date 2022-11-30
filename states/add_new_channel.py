from aiogram.dispatcher.filters.state import State, StatesGroup


class AddNewChannelFSM(StatesGroup):
    get_group_id = State()
    confirm = State()
