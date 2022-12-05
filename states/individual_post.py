from aiogram.dispatcher.filters.state import State, StatesGroup


class IndividualPostFSM(StatesGroup):
    get_channel = State()
    get_time = State()
    get_day = State()
    get_button = State()
    get_text_for_button = State()
    get_url_for_button = State()
    get_post = State()
    confirm = State()
    # For auto delete
    get_type_time = State()
    get_interval = State()
