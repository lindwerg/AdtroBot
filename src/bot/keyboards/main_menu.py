"""Main menu and start keyboards."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from src.bot.callbacks.menu import MenuAction, MenuCallback


def get_main_menu_keyboard():
    """
    Build main menu reply keyboard.

    Returns 2x3 grid:
        Гороскоп       | Таро
        Натальная карта | Подписка
        Профиль
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text="Гороскоп")
    builder.button(text="Таро")
    builder.button(text="Натальная карта")
    builder.button(text="Подписка")
    builder.button(text="Профиль")
    builder.adjust(2, 2, 1)  # 2+2+1 = 5 buttons in 3 rows
    return builder.as_markup(resize_keyboard=True)


def get_start_keyboard() -> InlineKeyboardMarkup:
    """
    Build start keyboard for new users.

    Returns inline keyboard with "Получить первый прогноз" button.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Получить первый прогноз",
                    callback_data=MenuCallback(action=MenuAction.GET_FIRST_FORECAST).pack(),
                )
            ]
        ]
    )


def get_first_horoscope_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for first horoscope after onboarding.

    Returns inline keyboard with "Получить первый гороскоп ✨" button.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Получить первый гороскоп ✨",
                    callback_data=MenuCallback(action=MenuAction.GET_FIRST_HOROSCOPE).pack(),
                )
            ]
        ]
    )
