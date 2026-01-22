"""Callback data for profile settings."""

from aiogram.filters.callback_data import CallbackData


class TimezoneCallback(CallbackData, prefix="tz"):
    zone: str  # IANA timezone


class NotificationTimeCallback(CallbackData, prefix="nt"):
    hour: int  # 0-23


class NotificationToggleCallback(CallbackData, prefix="ntog"):
    enable: bool
