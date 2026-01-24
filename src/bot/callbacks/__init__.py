"""Callback data factories for Telegram bot."""

from src.bot.callbacks.horoscope import ZodiacCallback
from src.bot.callbacks.menu import MenuAction, MenuCallback
from src.bot.callbacks.profile import (
    NotificationTimeCallback,
    NotificationToggleCallback,
    TimezoneCallback,
)

__all__ = [
    "ZodiacCallback",
    "MenuAction",
    "MenuCallback",
    "NotificationTimeCallback",
    "NotificationToggleCallback",
    "TimezoneCallback",
]
