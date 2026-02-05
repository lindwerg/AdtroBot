"""Subscription keyboards."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.callbacks.menu import MenuAction, MenuCallback
from src.bot.callbacks.subscription import SubscriptionCallback
from src.services.payment import PaymentPlan, format_button_price, get_active_discount


async def get_plans_keyboard(session: AsyncSession) -> InlineKeyboardMarkup:
    """Build subscription plans keyboard with discounts."""
    builder = InlineKeyboardBuilder()

    monthly_discount = await get_active_discount(session, PaymentPlan.MONTHLY)
    monthly_price = format_button_price(PaymentPlan.MONTHLY, monthly_discount)

    builder.button(
        text=f"Месяц — {monthly_price}",
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

    Uses MenuCallback for consistency with other menu actions.
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="Оформить Premium",
        callback_data=MenuCallback(action=MenuAction.MENU_SUBSCRIPTION).pack(),
    )

    return builder.as_markup()
