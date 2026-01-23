"""Birth data collection FSM states."""

from aiogram.fsm.state import State, StatesGroup


class BirthDataStates(StatesGroup):
    """States for collecting birth time and place."""

    waiting_birth_time = State()  # Ожидаем ввод времени (HH:MM или "не знаю")
    waiting_birth_city = State()  # Ожидаем ввод названия города
    selecting_city = State()  # Ожидаем выбор города из списка
