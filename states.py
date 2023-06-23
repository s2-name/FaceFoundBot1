from aiogram.dispatcher.filters.state import StatesGroup, State


class RegUserStates(StatesGroup):
    choosing_date_of_birth = State()
    choosing_confirmation_acceptance = State()
