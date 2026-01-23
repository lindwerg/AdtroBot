"""Keyboards for natal chart feature."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.bot.callbacks.natal import NatalAction, NatalCallback


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
                    callback_data="setup_birth_data",
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
                    callback_data="menu_subscription",
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
