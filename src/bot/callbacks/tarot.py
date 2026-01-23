"""Tarot callback data structures."""

from enum import Enum

from aiogram.filters.callback_data import CallbackData


class TarotAction(str, Enum):
    """Tarot menu actions."""

    CARD_OF_DAY = "cod"  # Карта дня
    THREE_CARD = "3c"  # Расклад 3 карты
    CELTIC_CROSS = "cc"  # Кельтский крест
    HISTORY = "hist"  # История раскладов
    DRAW_COD = "dcod"  # Вытянуть карту дня
    DRAW_THREE = "d3"  # Вытянуть 3 карты
    DRAW_CELTIC = "dcc"  # Вытянуть 10 карт
    BACK_TO_MENU = "back"  # Назад в главное меню


class TarotCallback(CallbackData, prefix="t"):
    """
    Tarot callback data.

    Short prefix "t" and field "a" (action) for Telegram 64-byte limit.
    """

    a: TarotAction  # action


class HistoryAction(str, Enum):
    """History actions."""

    LIST = "l"  # Список раскладов
    VIEW = "v"  # Просмотр расклада
    PAGE = "p"  # Пагинация


class HistoryCallback(CallbackData, prefix="h"):
    """
    History callback data.

    Short prefix "h" (history).
    Fields: a (action), i (spread_id), p (page).
    """

    a: HistoryAction  # action
    i: int | None = None  # spread_id (for VIEW)
    p: int | None = None  # page (for PAGE)
