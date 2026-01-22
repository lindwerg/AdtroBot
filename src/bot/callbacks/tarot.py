"""Tarot callback data structures."""

from enum import Enum

from aiogram.filters.callback_data import CallbackData


class TarotAction(str, Enum):
    """Tarot menu actions."""

    CARD_OF_DAY = "cod"  # Карта дня
    THREE_CARD = "3c"  # Расклад 3 карты
    DRAW_COD = "dcod"  # Вытянуть карту дня
    DRAW_THREE = "d3"  # Вытянуть 3 карты
    BACK_TO_MENU = "back"  # Назад в главное меню


class TarotCallback(CallbackData, prefix="t"):
    """
    Tarot callback data.

    Short prefix "t" and field "a" (action) for Telegram 64-byte limit.
    """

    a: TarotAction  # action
