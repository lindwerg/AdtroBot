"""Tarot keyboards."""

from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.callbacks.tarot import TarotAction, TarotCallback


def get_tarot_menu_keyboard():
    """
    Build tarot menu keyboard.

    Buttons:
        Карта дня
        Расклад на 3 карты
        Назад
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Карта дня",
        callback_data=TarotCallback(a=TarotAction.CARD_OF_DAY),
    )
    builder.button(
        text="Расклад на 3 карты",
        callback_data=TarotCallback(a=TarotAction.THREE_CARD),
    )
    builder.button(
        text="Назад",
        callback_data=TarotCallback(a=TarotAction.BACK_TO_MENU),
    )
    builder.adjust(1)  # 1 button per row
    return builder.as_markup()


def get_draw_card_keyboard():
    """Keyboard for drawing card of the day."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Вытянуть карту",
        callback_data=TarotCallback(a=TarotAction.DRAW_COD),
    )
    return builder.as_markup()


def get_draw_three_keyboard():
    """Keyboard for drawing 3 cards."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Вытянуть карты",
        callback_data=TarotCallback(a=TarotAction.DRAW_THREE),
    )
    return builder.as_markup()
