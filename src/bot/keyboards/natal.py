"""Keyboards for natal chart feature."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.bot.callbacks.menu import MenuAction, MenuCallback
from src.bot.callbacks.natal import NatalAction, NatalCallback
from src.services.payment.schemas import PLAN_PRICES_STR, PaymentPlan


def get_natal_menu_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard after showing natal chart (back to main menu)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Назад в меню",
                    callback_data=NatalCallback(action=NatalAction.BACK_TO_MENU).pack(),
                )
            ]
        ]
    )


def get_natal_setup_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for users without birth data."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Настроить данные рождения",
                    # Use the same callback as birth_data handler
                    callback_data=MenuCallback(action=MenuAction.SETUP_BIRTH_DATA).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Назад в меню",
                    callback_data=NatalCallback(action=NatalAction.BACK_TO_MENU).pack(),
                )
            ],
        ]
    )


def get_natal_teaser_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for free users (premium teaser)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Оформить подписку",
                    callback_data=MenuCallback(action=MenuAction.MENU_SUBSCRIPTION).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Назад в меню",
                    callback_data=NatalCallback(action=NatalAction.BACK_TO_MENU).pack(),
                )
            ],
        ]
    )


def get_natal_with_buy_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for premium users who haven't purchased detailed."""
    price = PLAN_PRICES_STR[PaymentPlan.DETAILED_NATAL]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Детальный разбор личности - {price} руб.",
                    callback_data=NatalCallback(action=NatalAction.BUY_DETAILED).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Назад в меню",
                    callback_data=NatalCallback(action=NatalAction.BACK_TO_MENU).pack(),
                )
            ],
        ]
    )


def get_natal_with_open_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for users who purchased detailed interpretation."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть детальный разбор",
                    callback_data=NatalCallback(action=NatalAction.SHOW_DETAILED).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Назад в меню",
                    callback_data=NatalCallback(action=NatalAction.BACK_TO_MENU).pack(),
                )
            ],
        ]
    )


def get_free_natal_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for free users viewing natal chart."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Получить полный разбор",
                    callback_data=MenuCallback(action=MenuAction.MENU_SUBSCRIPTION).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Назад в меню",
                    callback_data=NatalCallback(action=NatalAction.BACK_TO_MENU).pack(),
                )
            ],
        ]
    )
