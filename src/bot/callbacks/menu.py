"""Menu callback data factories."""

from enum import Enum

from aiogram.filters.callback_data import CallbackData


class MenuAction(str, Enum):
    """Menu action types."""

    # Profile actions
    PROFILE_NOTIFICATIONS = "notif"
    SETUP_BIRTH_DATA = "setup"

    # Subscription actions
    MENU_SUBSCRIPTION = "sub"

    # Onboarding actions
    GET_FIRST_FORECAST = "first"
    GET_FIRST_HOROSCOPE = "first_horo"
    ONBOARDING_NOTIF_YES = "n_yes"
    ONBOARDING_NOTIF_NO = "n_no"

    # Navigation actions
    BACK_TO_MAIN_MENU = "back_to_main"


class MenuCallback(CallbackData, prefix="menu"):
    """Callback data for menu actions."""

    action: MenuAction
