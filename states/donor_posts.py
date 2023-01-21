from aiogram.dispatcher.filters.state import State, StatesGroup


class DonorPostsFSM(StatesGroup):
    get_channels = State()
    get_type_time = State()
    get_interval = State()
    get_arbitrary = State()
    get_schedule_day = State()
    get_schedule_time = State()
    get_posts = State()
    confirm = State()


class IntervalDeleteDonorPostFSM(StatesGroup):
    get_type_time = State()
    get_interval = State()


class CreateDonorButtonsFSM(StatesGroup):
    get_name = State()


class CreateDescriptionDonorFSM(StatesGroup):
    get_description = State()
