"""Keyboards for birth data collection."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.callbacks.birth_data import CitySelectCallback, SkipTimeCallback
from src.services.astrology.geocoding import CityResult


def build_skip_time_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard with 'I don't know' button for birth time."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Не знаю время рождения",
            callback_data=SkipTimeCallback().pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Отмена",
            callback_data="cancel_birth_data",
        )
    )
    return builder.as_markup()


def build_city_selection_keyboard(
    cities: list[CityResult],
) -> InlineKeyboardMarkup:
    """Build keyboard for selecting city from search results.

    Args:
        cities: List of CityResult from geocoding

    Returns:
        Keyboard with city buttons + retry/cancel
    """
    builder = InlineKeyboardBuilder()

    for idx, city in enumerate(cities[:5]):  # Max 5 results
        # Truncate long names
        display_name = city.name[:40] + "..." if len(city.name) > 40 else city.name
        builder.row(
            InlineKeyboardButton(
                text=display_name,
                callback_data=CitySelectCallback(idx=idx).pack(),
            )
        )

    # Retry and cancel buttons
    builder.row(
        InlineKeyboardButton(
            text="Ввести другой город",
            callback_data="retry_city_search",
        ),
        InlineKeyboardButton(
            text="Отмена",
            callback_data="cancel_birth_data",
        ),
    )

    return builder.as_markup()


def build_birth_data_complete_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard after successful birth data save."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Посмотреть гороскоп",
            callback_data="menu_horoscope",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Главное меню",
            callback_data="main_menu",
        )
    )
    return builder.as_markup()
