"""Subscription keyboards."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.callbacks.subscription import SubscriptionCallback


def get_plans_keyboard() -> InlineKeyboardMarkup:
    """Build subscription plans keyboard."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text="Месяц — 299 р.",
        callback_data=SubscriptionCallback(action="plan", plan="monthly"),
    )
    builder.button(
        text="Год — 2499 р. (-30%)",
        callback_data=SubscriptionCallback(action="plan", plan="yearly"),
    )
    builder.adjust(1)

    return builder.as_markup()


def get_cancel_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Build cancel confirmation keyboard with retention offer."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text="Да, отменить",
        callback_data=SubscriptionCallback(action="confirm_cancel"),
    )
    builder.button(
        text="Нет, остаюсь",
        callback_data=SubscriptionCallback(action="keep"),
    )
    builder.adjust(1)

    return builder.as_markup()


def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard to navigate to subscription page.

    Uses menu_subscription callback which is handled in subscription.py.
    """
    builder = InlineKeyboardBuilder()

    # Use raw callback_data that matches the existing handler
    builder.button(
        text="Оформить Premium",
        callback_data="menu_subscription",
    )

    return builder.as_markup()
