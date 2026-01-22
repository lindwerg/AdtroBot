"""Profile settings FSM states."""

from aiogram.fsm.state import State, StatesGroup


class ProfileSettings(StatesGroup):
    """States for profile settings flow."""

    choosing_timezone = State()
    choosing_notification_time = State()
