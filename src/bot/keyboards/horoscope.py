"""Inline keyboards for horoscope navigation."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.callbacks.horoscope import ZodiacCallback
from src.bot.callbacks.menu import MenuAction, MenuCallback
from src.bot.utils.zodiac import ZODIAC_SIGNS

# Classical zodiac order: Aries -> Pisces
ZODIAC_ORDER = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


def build_zodiac_keyboard(
    current_sign: str | None = None,
    is_premium: bool = False,
    has_natal_data: bool = False,
) -> InlineKeyboardMarkup:
    """Build 4x3 inline keyboard for zodiac sign selection.

    Args:
        current_sign: Currently selected sign (will be highlighted)
        is_premium: Whether user has premium subscription
        has_natal_data: Whether user has birth location data

    Returns:
        InlineKeyboardMarkup with zodiac buttons + optional natal setup
    """
    builder = InlineKeyboardBuilder()

    for name in ZODIAC_ORDER:
        zodiac = ZODIAC_SIGNS[name]
        # Format: "♈ Овен" or "✓ ♈ Овен" for current sign
        text = f"{zodiac.emoji} {zodiac.name_ru}"
        if name == current_sign:
            text = f"✓ {text}"
        builder.button(
            text=text,
            callback_data=ZodiacCallback(s=name).pack(),
        )

    # 3 rows of 4 buttons
    builder.adjust(4, 4, 4)

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
