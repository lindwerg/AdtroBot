"""Profile settings keyboards."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.callbacks.profile import (
    NotificationTimeCallback,
    NotificationToggleCallback,
    TimezoneCallback,
)

# Popular Russian timezones
TIMEZONES = [
    ("Europe/Kaliningrad", "Калининград (UTC+2)"),
    ("Europe/Moscow", "Москва (UTC+3)"),
    ("Europe/Samara", "Самара (UTC+4)"),
    ("Asia/Yekaterinburg", "Екатеринбург (UTC+5)"),
    ("Asia/Omsk", "Омск (UTC+6)"),
    ("Asia/Krasnoyarsk", "Красноярск (UTC+7)"),
    ("Asia/Irkutsk", "Иркутск (UTC+8)"),
    ("Asia/Vladivostok", "Владивосток (UTC+10)"),
]


def build_timezone_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard with popular Russian timezones."""
    builder = InlineKeyboardBuilder()
    for zone, label in TIMEZONES:
        builder.button(text=label, callback_data=TimezoneCallback(zone=zone).pack())
    builder.adjust(1)  # One button per row
    return builder.as_markup()


def build_notification_time_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard with notification time options."""
    builder = InlineKeyboardBuilder()
    for hour in [7, 8, 9, 10, 11, 12]:
        builder.button(
            text=f"{hour:02d}:00", callback_data=NotificationTimeCallback(hour=hour).pack()
        )
    builder.adjust(3, 3)  # 2 rows of 3
    return builder.as_markup()


def build_notifications_toggle_keyboard(currently_enabled: bool) -> InlineKeyboardMarkup:
    """Build keyboard to toggle notifications."""
    builder = InlineKeyboardBuilder()
    if currently_enabled:
        builder.button(
            text="Выключить уведомления",
            callback_data=NotificationToggleCallback(enable=False).pack(),
        )
    else:
        builder.button(
            text="Включить уведомления",
            callback_data=NotificationToggleCallback(enable=True).pack(),
        )
    return builder.as_markup()


def build_onboarding_notifications_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for onboarding notification prompt (Yes/No)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Да, включить", callback_data="onboarding_notif_yes")
    builder.button(text="Нет, спасибо", callback_data="onboarding_notif_no")
    builder.adjust(2)
    return builder.as_markup()
