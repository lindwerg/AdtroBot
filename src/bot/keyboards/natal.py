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
                    text="🏠 Главное меню",
                    callback_data=MenuCallback(action=MenuAction.BACK_TO_MAIN_MENU).pack(),
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
                    text="🏠 Главное меню",
                    callback_data=MenuCallback(action=MenuAction.BACK_TO_MAIN_MENU).pack(),
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
                    text="🏠 Главное меню",
                    callback_data=MenuCallback(action=MenuAction.BACK_TO_MAIN_MENU).pack(),
                )
            ],
        ]
    )


def get_natal_with_buy_keyboard(telegraph_url: str | None = None) -> InlineKeyboardMarkup:
    """Get keyboard for premium users who haven't purchased detailed."""
    buttons = []

    # 1️⃣ Кнопка "Открыть прогноз" (если есть)
    if telegraph_url:
        buttons.append([
            InlineKeyboardButton(
                text="📖 Открыть прогноз",
                url=telegraph_url,
            )
        ])

    # 2️⃣ Кнопка "Поговорить с астрологом" (NEW!)
    buttons.append([
        InlineKeyboardButton(
            text="💬 Поговорить с астрологом",
            callback_data=NatalCallback(action=NatalAction.START_CHAT).pack(),
        )
    ])

    # 3️⃣ Кнопка "Детальный разбор"
    price = PLAN_PRICES_STR[PaymentPlan.DETAILED_NATAL]
    buttons.append([
        InlineKeyboardButton(
            text=f"Детальный разбор личности - {price} руб.",
            callback_data=NatalCallback(action=NatalAction.BUY_DETAILED).pack(),
        )
    ])

    # 4️⃣ Кнопка "Главное меню"
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data=MenuCallback(action=MenuAction.BACK_TO_MAIN_MENU).pack(),
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_natal_with_open_keyboard(telegraph_url: str | None = None) -> InlineKeyboardMarkup:
    """Get keyboard for users who purchased detailed interpretation."""
    buttons = []

    # 1️⃣ Кнопка "Открыть прогноз"
    if telegraph_url:
        buttons.append([
            InlineKeyboardButton(
                text="📖 Открыть прогноз",
                url=telegraph_url,
            )
        ])

    # 2️⃣ Кнопка "Поговорить с астрологом" (NEW!)
    buttons.append([
        InlineKeyboardButton(
            text="💬 Поговорить с астрологом",
            callback_data=NatalCallback(action=NatalAction.START_CHAT).pack(),
        )
    ])

    # 3️⃣ Кнопка "Открыть детальный разбор"
    buttons.append([
        InlineKeyboardButton(
            text="Открыть детальный разбор",
            callback_data=NatalCallback(action=NatalAction.SHOW_DETAILED).pack(),
        )
    ])

    # 4️⃣ Кнопка "Главное меню"
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data=MenuCallback(action=MenuAction.BACK_TO_MAIN_MENU).pack(),
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_free_natal_keyboard(telegraph_url: str | None = None) -> InlineKeyboardMarkup:
    """Get keyboard for free users viewing natal chart."""
    buttons = []

    # 1️⃣ Кнопка "Открыть прогноз"
    if telegraph_url:
        buttons.append([
            InlineKeyboardButton(
                text="📖 Открыть прогноз",
                url=telegraph_url,
            )
        ])

    # 2️⃣ Кнопка "Поговорить с астрологом" (NEW!)
    buttons.append([
        InlineKeyboardButton(
            text="💬 Поговорить с астрологом",
            callback_data=NatalCallback(action=NatalAction.START_CHAT).pack(),
        )
    ])

    # 3️⃣ Кнопка "Получить полный разбор"
    buttons.append([
        InlineKeyboardButton(
            text="Получить полный разбор",
            callback_data=MenuCallback(action=MenuAction.MENU_SUBSCRIPTION).pack(),
        )
    ])

    # 4️⃣ Кнопка "Главное меню"
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data=MenuCallback(action=MenuAction.BACK_TO_MAIN_MENU).pack(),
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_astrologer_chat_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for active astrologer chat conversation."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Завершить диалог",
                    callback_data=NatalCallback(action=NatalAction.END_CHAT).pack(),
                )
            ]
        ]
    )
