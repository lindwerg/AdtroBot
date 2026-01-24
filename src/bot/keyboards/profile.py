"""Profile settings keyboards."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.callbacks.menu import MenuAction, MenuCallback
from src.bot.callbacks.profile import (
    NotificationTimeCallback,
    NotificationToggleCallback,
    TimezoneCallback,
)

# Popular Russian timezones (shortened for better mobile UX)
TIMEZONES = [
    ("Europe/Kaliningrad", "Калининград UTC+2"),
    ("Europe/Moscow", "Москва UTC+3"),
    ("Europe/Samara", "Самара UTC+4"),
    ("Asia/Yekaterinburg", "Екатеринбург UTC+5"),
    ("Asia/Omsk", "Омск UTC+6"),
    ("Asia/Krasnoyarsk", "Красноярск UTC+7"),
    ("Asia/Irkutsk", "Иркутск UTC+8"),
    ("Asia/Vladivostok", "Владивосток UTC+10"),
]


def build_timezone_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard with popular Russian timezones."""
    builder = InlineKeyboardBuilder()
    for zone, label in TIMEZONES:
        builder.button(text=label, callback_data=TimezoneCallback(zone=zone).pack())
    builder.adjust(2)  # Two buttons per row for better mobile UX
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
    builder.button(
        text="Да, включить",
        callback_data=MenuCallback(action=MenuAction.ONBOARDING_NOTIF_YES).pack(),
    )
    builder.button(
        text="Нет, спасибо",
        callback_data=MenuCallback(action=MenuAction.ONBOARDING_NOTIF_NO).pack(),
    )
    builder.adjust(2)
    return builder.as_markup()


def build_profile_actions_keyboard(
    is_premium: bool,
    has_birth_data: bool,
    has_subscription: bool = False,
    subscription_status: str | None = None,
) -> InlineKeyboardMarkup:
    """Build keyboard with profile action buttons.

    Args:
        is_premium: Whether user has premium subscription
        has_birth_data: Whether user has set birth time/city
        has_subscription: Whether user has active subscription
        subscription_status: Subscription status (active, trial, canceled)

    Returns:
        Keyboard with notification settings + premium-only birth data button
    """
    builder = InlineKeyboardBuilder()

    # Notification settings always available
    builder.button(
        text="Настройки уведомлений",
        callback_data=MenuCallback(action=MenuAction.PROFILE_NOTIFICATIONS).pack(),
    )

    # Birth data setup for premium users
    if is_premium:
        if has_birth_data:
            builder.button(
                text="Изменить данные рождения",
                callback_data=MenuCallback(action=MenuAction.SETUP_BIRTH_DATA).pack(),
            )
        else:
            builder.button(
                text="Настроить натальную карту",
                callback_data=MenuCallback(action=MenuAction.SETUP_BIRTH_DATA).pack(),
            )

    # Cancel subscription button if active
    if has_subscription and subscription_status in ("active", "trial"):
        from src.bot.callbacks.subscription import SubscriptionCallback

        builder.button(
            text="Отменить подписку",
            callback_data=SubscriptionCallback(action="cancel").pack(),
        )

    builder.adjust(1)
    return builder.as_markup()
