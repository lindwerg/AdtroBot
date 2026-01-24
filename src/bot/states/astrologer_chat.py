"""FSM states for astrologer chat dialog."""

from aiogram.fsm.state import State, StatesGroup


class AstrologerChatStates(StatesGroup):
    """FSM states for astrologer chat conversation."""

    in_conversation = State()  # Active conversation with AI astrologer
