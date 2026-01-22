"""Inline keyboards for horoscope navigation."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.callbacks.horoscope import ZodiacCallback
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


def build_zodiac_keyboard(current_sign: str | None = None) -> InlineKeyboardMarkup:
    """
    Build 4x3 grid of zodiac signs with optional checkmark for current sign.

    Args:
        current_sign: English name of sign to highlight (e.g., "Aries")

    Returns:
        InlineKeyboardMarkup with 12 zodiac emoji buttons in 3 rows of 4
    """
    builder = InlineKeyboardBuilder()

    for name in ZODIAC_ORDER:
        zodiac = ZODIAC_SIGNS[name]
        # Add checkmark if this is user's sign
        text = f"{'✓ ' if name == current_sign else ''}{zodiac.emoji}"
        builder.button(
            text=text,
            callback_data=ZodiacCallback(s=name).pack(),
        )

    # 3 rows of 4 buttons
    builder.adjust(4, 4, 4)
    return builder.as_markup()
