"""Subscription callback data."""

from aiogram.filters.callback_data import CallbackData


class SubscriptionCallback(CallbackData, prefix="sub"):
    """Callback for subscription actions."""

    action: str  # "plan", "cancel", "confirm_cancel", "keep"
    plan: str = ""  # "monthly", "yearly"
