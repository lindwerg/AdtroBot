"""Onboarding FSM states."""

from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    """States for user onboarding flow."""

    waiting_birthdate = State()
