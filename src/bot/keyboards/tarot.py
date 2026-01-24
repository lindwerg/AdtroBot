"""Tarot keyboards."""

from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.callbacks.menu import MenuAction, MenuCallback
from src.bot.callbacks.tarot import (
    HistoryAction,
    HistoryCallback,
    TarotAction,
    TarotCallback,
)


def get_tarot_menu_keyboard():
    """
    Build tarot menu keyboard.

    Buttons:
        Row 1: Карта дня
        Row 2: Расклад на 3 карты
        Row 3: Кельтский крест, История
        Row 4: 🏠 Главное меню
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
        text="Кельтский крест",
        callback_data=TarotCallback(a=TarotAction.CELTIC_CROSS),
    )
    builder.button(
        text="История",
        callback_data=TarotCallback(a=TarotAction.HISTORY),
    )
    builder.button(
        text="🏠 Главное меню",
        callback_data=MenuCallback(action=MenuAction.BACK_TO_MAIN_MENU).pack(),
    )
    builder.adjust(1, 1, 2, 1)  # 1, 1, 2 side by side, 1
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


def get_draw_celtic_keyboard():
    """Keyboard for drawing Celtic Cross (10 cards)."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Открыть карты",
        callback_data=TarotCallback(a=TarotAction.DRAW_CELTIC),
    )
    return builder.as_markup()


def get_history_keyboard(spreads: list, page: int, total_pages: int, offset: int = 0):
    """
    Keyboard for spread history list.

    Args:
        spreads: List of TarotSpread objects for current page
        page: Current page number (0-indexed)
        total_pages: Total number of pages
        offset: Offset for numbering (page * page_size)
    """
    builder = InlineKeyboardBuilder()

    # Add spread buttons
    for idx, spread in enumerate(spreads):
        # Format: [index] date + type + question preview (shortened for better UX)
        date_str = spread.created_at.strftime("%d.%m")
        type_label = "CC" if spread.spread_type == "celtic_cross" else "3K"
        question_preview = spread.question[:15] + "..." if len(spread.question) > 15 else spread.question
        text = f"[{offset + idx + 1}] {date_str} [{type_label}] {question_preview}"

        builder.button(
            text=text,
            callback_data=HistoryCallback(a=HistoryAction.VIEW, i=spread.id),
        )

    # Add pagination if needed
    if total_pages > 1:
        if page > 0:
            builder.button(
                text="<< Назад",
                callback_data=HistoryCallback(a=HistoryAction.PAGE, p=page - 1),
            )
        if page < total_pages - 1:
            builder.button(
                text="Вперед >>",
                callback_data=HistoryCallback(a=HistoryAction.PAGE, p=page + 1),
            )

    # Back to tarot menu
    builder.button(
        text="В меню Таро",
        callback_data=TarotCallback(a=TarotAction.BACK_TO_MENU),
    )

    # Adjust: spreads in single column, pagination row, back button
    rows = [1] * len(spreads)  # Each spread on its own row
    if total_pages > 1:
        # Pagination buttons in one row
        nav_buttons = 0
        if page > 0:
            nav_buttons += 1
        if page < total_pages - 1:
            nav_buttons += 1
        if nav_buttons > 0:
            rows.append(nav_buttons)
    rows.append(1)  # Back button
    builder.adjust(*rows)

    return builder.as_markup()


def get_spread_detail_keyboard():
    """Keyboard for viewing spread detail - back to history."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="К истории",
        callback_data=HistoryCallback(a=HistoryAction.LIST),
    )
    builder.button(
        text="В меню Таро",
        callback_data=TarotCallback(a=TarotAction.BACK_TO_MENU),
    )
    builder.adjust(2)
    return builder.as_markup()
