"""Inline keyboards for horoscope navigation."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.callbacks.menu import MenuAction, MenuCallback


def build_zodiac_keyboard(
    current_sign: str | None = None,
    is_premium: bool = False,
    has_natal_data: bool = False,
) -> InlineKeyboardMarkup:
    """Build keyboard for horoscope (without zodiac sign selection grid).

    Args:
        current_sign: Currently selected sign (not used anymore)
        is_premium: Whether user has premium subscription
        has_natal_data: Whether user has birth location data

    Returns:
        InlineKeyboardMarkup with action buttons (no zodiac grid)
    """
    builder = InlineKeyboardBuilder()

    # Add natal setup button for premium users without data
    if is_premium and not has_natal_data:
        builder.row(
            InlineKeyboardButton(
                text="Настроить натальную карту",
                callback_data=MenuCallback(action=MenuAction.SETUP_BIRTH_DATA).pack(),
            )
        )

    # Add premium button for free users
    if not is_premium:
        builder.row(
            InlineKeyboardButton(
                text="Получить премиум-гороскоп",
                callback_data=MenuCallback(action=MenuAction.MENU_SUBSCRIPTION).pack(),
            )
        )

    # Add "Back to main menu" button
    builder.row(
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data=MenuCallback(action=MenuAction.BACK_TO_MAIN_MENU).pack(),
        )
    )

    return builder.as_markup()


def build_home_menu_keyboard() -> InlineKeyboardMarkup:
    """Build minimal keyboard with only "Home menu" button.

    Used for personalized horoscope (premium user with natal data).
    No zodiac switching needed - it's their personal forecast.

    Returns:
        InlineKeyboardMarkup with single "🏠 Главное меню" button
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data=MenuCallback(action=MenuAction.BACK_TO_MAIN_MENU).pack(),
                )
            ]
        ]
    )
