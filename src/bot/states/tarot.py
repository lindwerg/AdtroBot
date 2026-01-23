"""Tarot FSM states."""

from aiogram.fsm.state import State, StatesGroup


class TarotStates(StatesGroup):
    """States for tarot reading flow."""

    waiting_question = State()  # Ожидание вопроса для расклада 3 карты
    waiting_celtic_question = State()  # Ожидание вопроса для Кельтского креста
