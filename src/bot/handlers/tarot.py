"""Tarot handlers: card of the day, 3-card spread."""

import asyncio
from datetime import datetime

import pytz
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.callbacks.tarot import TarotAction, TarotCallback
from src.bot.keyboards.main_menu import get_main_menu_keyboard
from src.bot.keyboards.tarot import (
    get_draw_card_keyboard,
    get_draw_three_keyboard,
    get_tarot_menu_keyboard,
)
from src.bot.states.tarot import TarotStates
from src.bot.utils.tarot_cards import (
    get_card_by_id,
    get_card_image,
    get_random_card,
    get_three_cards,
)
from src.bot.utils.tarot_formatting import (
    format_card_of_day,
    format_limit_exceeded,
    format_limit_message,
    format_three_card_spread,
)
from src.db.models.user import User

router = Router(name="tarot")


# ============== Helper functions ==============


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    """Get user by telegram_id."""
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def get_user_today(user: User) -> datetime.date:
    """Get today's date in user's timezone."""
    user_tz = pytz.timezone(user.timezone or "Europe/Moscow")
    return datetime.now(user_tz).date()


async def check_and_use_tarot_limit(
    user: User, session: AsyncSession
) -> tuple[bool, int]:
    """
    Check if user can do tarot spread today.

    NOTE: Лимиты применяются ТОЛЬКО к 3-card spread.
    Карта дня бесплатная и неограниченная.

    Returns:
        (allowed, remaining_count)
    """
    today = get_user_today(user)

    # Reset if new day
    if user.spread_reset_date != today:
        user.tarot_spread_count = 0
        user.spread_reset_date = today

    # Limits: free=1, premium=20 (premium check placeholder)
    is_premium = False  # TODO: add is_premium field in Phase 6
    limit = 20 if is_premium else 1
    remaining = limit - user.tarot_spread_count

    if remaining > 0:
        user.tarot_spread_count += 1
        await session.commit()
        return True, remaining - 1

    return False, 0


# ============== Tarot Menu ==============


@router.callback_query(TarotCallback.filter(F.a == TarotAction.BACK_TO_MENU))
async def tarot_back_to_menu(callback: CallbackQuery) -> None:
    """Handle 'Back' button - return to main menu."""
    await callback.message.delete()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()


# ============== Card of the Day ==============
# NOTE: Карта дня БЕСПЛАТНАЯ и НЕОГРАНИЧЕННАЯ.
# Лимиты НЕ применяются к карте дня, только к 3-card spread.


@router.callback_query(TarotCallback.filter(F.a == TarotAction.CARD_OF_DAY))
async def tarot_card_of_day_start(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """Start card of the day ritual."""
    user = await get_user(session, callback.from_user.id)
    if not user:
        await callback.answer("Пройдите регистрацию через /start", show_alert=True)
        return

    today = get_user_today(user)

    # Check cache - if already drawn today, show immediately
    if user.card_of_day_date == today and user.card_of_day_id:
        card = get_card_by_id(user.card_of_day_id)
        if card:
            reversed_flag = user.card_of_day_reversed or False
            await send_card_of_day(callback.message, card, reversed_flag)
            await callback.answer()
            return

    # Show ritual
    await callback.message.edit_text("Тасую колоду...")
    await asyncio.sleep(1.5)

    await callback.message.edit_text(
        "Карта перед вами...",
        reply_markup=get_draw_card_keyboard(),
    )
    await callback.answer()


@router.callback_query(TarotCallback.filter(F.a == TarotAction.DRAW_COD))
async def tarot_draw_card_of_day(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """Draw and show card of the day."""
    user = await get_user(session, callback.from_user.id)
    if not user:
        await callback.answer("Пройдите регистрацию через /start", show_alert=True)
        return

    today = get_user_today(user)

    # Check cache again (in case of race condition)
    if user.card_of_day_date == today and user.card_of_day_id:
        card = get_card_by_id(user.card_of_day_id)
        if card:
            reversed_flag = user.card_of_day_reversed or False
            await callback.message.delete()
            await send_card_of_day(callback.message, card, reversed_flag)
            await callback.answer()
            return

    # Draw new card
    card, reversed_flag = get_random_card()

    # Save to cache
    user.card_of_day_id = card["name_short"]
    user.card_of_day_date = today
    user.card_of_day_reversed = reversed_flag
    await session.commit()

    await callback.message.delete()
    await send_card_of_day(callback.message, card, reversed_flag)
    await callback.answer()


async def send_card_of_day(message: Message, card: dict, reversed_flag: bool) -> None:
    """
    Send card of the day with image and interpretation.

    NOTE: НЕ показываем лимиты после карты дня - она бесплатная и неограниченная.
    """
    # Send image
    photo = get_card_image(card["name_short"], reversed_flag)
    await message.answer_photo(photo)

    # Send interpretation (без информации о лимитах!)
    content = format_card_of_day(card, reversed_flag)
    await message.answer(**content.as_kwargs(), reply_markup=get_tarot_menu_keyboard())


# ============== Three Card Spread ==============
# NOTE: Лимиты применяются ТОЛЬКО к 3-card spread.
# Бесплатно: 1 расклад в день. Premium: 20 раскладов в день.


@router.callback_query(TarotCallback.filter(F.a == TarotAction.THREE_CARD))
async def tarot_three_card_start(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Start 3-card spread - check limit and ask for question."""
    user = await get_user(session, callback.from_user.id)
    if not user:
        await callback.answer("Пройдите регистрацию через /start", show_alert=True)
        return

    # Check limit (preview, don't consume yet)
    today = get_user_today(user)
    if user.spread_reset_date != today:
        # Will be reset, so remaining = 1
        remaining = 1
    else:
        is_premium = False  # TODO: Phase 6
        limit = 20 if is_premium else 1
        remaining = limit - user.tarot_spread_count

    if remaining <= 0:
        content = format_limit_exceeded()
        await callback.message.edit_text(
            **content.as_kwargs(),
            reply_markup=get_tarot_menu_keyboard(),
        )
        await callback.answer()
        return

    # Ask for question
    await callback.message.edit_text(
        "Задайте свой вопрос:\n\n" "(Напишите вопрос в чат)"
    )
    await state.set_state(TarotStates.waiting_question)
    await callback.answer()


@router.message(TarotStates.waiting_question)
async def tarot_question_received(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Receive question and show ritual."""
    user = await get_user(session, message.from_user.id)
    if not user:
        await message.answer("Пройдите регистрацию через /start")
        await state.clear()
        return

    # Check and consume limit
    allowed, remaining = await check_and_use_tarot_limit(user, session)
    if not allowed:
        content = format_limit_exceeded()
        await message.answer(**content.as_kwargs(), reply_markup=get_tarot_menu_keyboard())
        await state.clear()
        return

    # Save question
    await state.update_data(question=message.text, remaining=remaining)

    # Show ritual
    await message.answer("Тасую колоду...")
    await asyncio.sleep(1.5)

    await message.answer(
        "Три карты перед вами...",
        reply_markup=get_draw_three_keyboard(),
    )


@router.callback_query(TarotCallback.filter(F.a == TarotAction.DRAW_THREE))
async def tarot_draw_three_cards(callback: CallbackQuery, state: FSMContext) -> None:
    """Draw and show 3 cards."""
    data = await state.get_data()
    question = data.get("question")
    remaining = data.get("remaining", 0)

    # Handle expired session - question not found in FSM state
    if not question:
        await callback.answer("Сессия истекла. Начните заново.", show_alert=True)
        await callback.message.delete()
        await state.clear()
        return

    await state.clear()

    # Draw 3 cards
    cards = get_three_cards()

    await callback.message.delete()

    # Send cards one by one with delay (dramatic effect)
    positions = ["Прошлое", "Настоящее", "Будущее"]
    for i, (card, reversed_flag) in enumerate(cards):
        photo = get_card_image(card["name_short"], reversed_flag)
        reversed_text = " (перевернутая)" if reversed_flag else ""
        caption = f"{positions[i]}: {card['name']}{reversed_text}"
        await callback.message.answer_photo(photo, caption=caption)
        if i < 2:  # Don't sleep after last card
            await asyncio.sleep(1)

    # Send interpretation
    content = format_three_card_spread(cards, question)
    limit_text = format_limit_message(remaining)

    await callback.message.answer(
        **content.as_kwargs(),
    )
    # Показываем лимиты ТОЛЬКО после 3-card spread (не после карты дня!)
    await callback.message.answer(
        limit_text,
        reply_markup=get_tarot_menu_keyboard(),
    )
    await callback.answer()
