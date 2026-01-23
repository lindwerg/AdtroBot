"""Callback data for natal chart handlers."""

from enum import Enum

from aiogram.filters.callback_data import CallbackData


class NatalAction(str, Enum):
    """Actions for natal chart callbacks."""

    SHOW_CHART = "show"
    SETUP_BIRTH_DATA = "setup"
    BACK_TO_MENU = "back"
    BUY_DETAILED = "buy"       # Buy detailed interpretation
    SHOW_DETAILED = "detailed"  # Show purchased interpretation


class NatalCallback(CallbackData, prefix="n"):
    """Natal chart callback data.

    Short prefix "n" for 64-byte Telegram limit.
    """

    action: NatalAction
