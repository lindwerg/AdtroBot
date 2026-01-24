"""Tarot handlers: card of the day, 3-card spread, Celtic Cross, history."""

import asyncio
from datetime import datetime

import pytz
import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)
from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.callbacks.tarot import (
    HistoryAction,
    HistoryCallback,
    TarotAction,
    TarotCallback,
)
from src.bot.keyboards.main_menu import get_main_menu_keyboard
from src.bot.keyboards.subscription import get_subscription_keyboard
from src.bot.keyboards.tarot import (
    get_draw_card_keyboard,
    get_draw_celtic_keyboard,
    get_draw_three_keyboard,
    get_history_keyboard,
    get_spread_detail_keyboard,
    get_tarot_menu_keyboard,
)
from src.bot.states.tarot import TarotStates
from src.bot.utils.progress import generate_with_feedback
from src.bot.utils.tarot_cards import (
    get_card_by_id,
    get_card_image,
    get_deck,
    get_random_card,
    get_ten_cards,
    get_three_cards,
)
from src.bot.utils.tarot_formatting import (
    format_card_of_day_with_ai,
    format_limit_exceeded,
    format_limit_message,
    format_spread_detail,
    format_three_card_spread_with_ai,
)
from src.db.models.tarot_spread import TarotSpread
from src.db.models.user import User
from src.services.ai import get_ai_service
from src.services.telegraph import get_telegraph_service

logger = structlog.get_logger()

router = Router(name="tarot")

# Spread limits
DAILY_SPREAD_LIMIT_FREE = 1
DAILY_SPREAD_LIMIT_PREMIUM = 20

# History settings
HISTORY_PAGE_SIZE = 5
MAX_HISTORY_SPREADS = 100

# Telegraph timeout (seconds)
TELEGRAPH_TIMEOUT = 10.0

# Celtic Cross positions
CELTIC_CROSS_POSITIONS = [
    "Настоящее",
    "Препятствие",
    "Прошлое",
    "Будущее",
    "Сознательное",
    "Подсознательное",
    "Я",
    "Окружение",
    "Надежды/Страхи",
    "Исход",
]


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


def get_daily_limit(user: User) -> int:
    """Get daily spread limit based on premium status."""
    return DAILY_SPREAD_LIMIT_PREMIUM if user.is_premium else DAILY_SPREAD_LIMIT_FREE


async def check_and_use_tarot_limit(
    user: User, session: AsyncSession
) -> tuple[bool, int]:
    """
    Check if user can do tarot spread today (atomic increment).

    NOTE: Лимиты применяются к 3-card spread и Celtic Cross.
    Карта дня бесплатная и неограниченная.

    Uses premium status to determine limit (1 free, 20 premium).
    Atomic update prevents race conditions.

    Returns:
        (allowed, remaining_count)
    """
    today = get_user_today(user)
    daily_limit = get_daily_limit(user)

    # Reset if new day (separate update to avoid race)
    if user.spread_reset_date != today:
        user.tarot_spread_count = 0
        user.spread_reset_date = today
        await session.commit()
        await session.refresh(user)

    # Atomic increment with limit check
    stmt = (
        update(User)
        .where(
            User.id == user.id,
            User.tarot_spread_count < daily_limit,
        )
        .values(tarot_spread_count=User.tarot_spread_count + 1)
        .returning(User.tarot_spread_count)
    )
    result = await session.execute(stmt)
    new_count = result.scalar_one_or_none()

    if new_count is None:
        # Limit exceeded (race condition protection)
        return False, 0

    await session.commit()
    remaining = daily_limit - new_count
    return True, remaining


async def save_spread_to_history(
    session: AsyncSession,
    user_id: int,
    spread_type: str,
    question: str,
    cards: list[tuple[dict, bool]],
    interpretation: str | None,
) -> None:
    """Save spread to history table.

    Args:
        session: Database session
        user_id: User's internal ID (not telegram_id)
        spread_type: "three_card" or "celtic_cross"
        question: User's question
        cards: List of (card_dict, reversed_flag) tuples
        interpretation: AI interpretation text (nullable)
    """
    cards_json = [
        {
            "card_id": card["name_short"],
            "reversed": reversed_flag,
            "position": i + 1,
        }
        for i, (card, reversed_flag) in enumerate(cards)
    ]

    spread = TarotSpread(
        user_id=user_id,
        spread_type=spread_type,
        question=question,
        cards=cards_json,
        interpretation=interpretation,
    )
    session.add(spread)
    await session.commit()


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
# Лимиты НЕ применяются к карте дня.


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
            await send_card_of_day(
                callback.message, card, reversed_flag, callback.from_user.id
            )
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
            await send_card_of_day(
                callback.message, card, reversed_flag, callback.from_user.id
            )
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
    await send_card_of_day(
        callback.message, card, reversed_flag, callback.from_user.id
    )
    await callback.answer()


async def send_card_of_day(
    message: Message, card: dict, reversed_flag: bool, user_id: int
) -> None:
    """Send card of the day with image and AI interpretation.

    NOTE: НЕ показываем лимиты после карты дня - она бесплатная и неограниченная.

    Args:
        message: Telegram message
        card: Card dict from deck
        reversed_flag: Whether card is reversed
        user_id: Telegram user ID for caching AI response
    """
    # Send image
    photo = get_card_image(card["name_short"], reversed_flag)
    await message.answer_photo(photo)

    # Get AI interpretation (with caching and progress indicator)
    ai = get_ai_service()
    interpretation = await generate_with_feedback(
        message=message,
        operation_type="card_of_day",
        ai_coro=ai.generate_card_of_day(user_id, card, reversed_flag),
    )

    # Send formatted message (AI or fallback to static meaning)
    content = format_card_of_day_with_ai(card, reversed_flag, interpretation)
    await message.answer(**content.as_kwargs(), reply_markup=get_tarot_menu_keyboard())


# ============== Three Card Spread ==============
# NOTE: Лимиты применяются к 3-card spread и Celtic Cross.
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
    daily_limit = get_daily_limit(user)

    if user.spread_reset_date != today:
        # Will be reset, so remaining = full limit
        remaining = daily_limit
    else:
        remaining = daily_limit - user.tarot_spread_count

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

    # Save question and user_id for history
    await state.update_data(
        question=message.text,
        remaining=remaining,
        user_db_id=user.id,
        is_premium=user.is_premium,
    )

    # Show ritual
    await message.answer("Тасую колоду...")
    await asyncio.sleep(1.5)

    await message.answer(
        "Три карты перед вами...",
        reply_markup=get_draw_three_keyboard(),
    )


@router.callback_query(TarotCallback.filter(F.a == TarotAction.DRAW_THREE))
async def tarot_draw_three_cards(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Draw and show 3 cards."""
    data = await state.get_data()
    question = data.get("question")
    remaining = data.get("remaining", 0)
    user_db_id = data.get("user_db_id")
    is_premium = data.get("is_premium", False)

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

    # Get AI interpretation with typing indicator
    ai = get_ai_service()
    cards_data = [card for card, _ in cards]
    is_reversed_list = [reversed_flag for _, reversed_flag in cards]
    interpretation = await generate_with_feedback(
        message=callback.message,
        operation_type="tarot",
        ai_coro=ai.generate_tarot_interpretation(question, cards_data, is_reversed_list),
    )

    # Save to history
    if user_db_id:
        await save_spread_to_history(
            session=session,
            user_id=user_db_id,
            spread_type="three_card",
            question=question,
            cards=cards,
            interpretation=interpretation,
        )

    # Send interpretation (AI or fallback to static meanings)
    content = format_three_card_spread_with_ai(cards, question, interpretation)
    limit_text = format_limit_message(remaining, is_premium)

    await callback.message.answer(
        **content.as_kwargs(),
    )
    # Показываем лимиты после расклада
    await callback.message.answer(
        limit_text,
        reply_markup=get_tarot_menu_keyboard(),
    )
    await callback.answer()


# ============== Celtic Cross (Premium) ==============


@router.callback_query(TarotCallback.filter(F.a == TarotAction.CELTIC_CROSS))
async def tarot_celtic_cross_start(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Start Celtic Cross - check premium and ask for question."""
    user = await get_user(session, callback.from_user.id)
    if not user:
        await callback.answer("Пройдите регистрацию через /start", show_alert=True)
        return

    # Check premium status
    if not user.is_premium:
        # Show premium teaser
        await callback.message.edit_text(
            "Кельтский крест — это глубокий расклад из 10 карт.\n\n"
            "Он раскрывает:\n"
            "- Корень ситуации и препятствия\n"
            "- Прошлое и возможное будущее\n"
            "- Сознательные и подсознательные влияния\n"
            "- Окружение и внутренние страхи\n"
            "- Итоговый исход\n\n"
            "Этот расклад доступен только с Premium подпиской.",
            reply_markup=get_subscription_keyboard(),
        )
        await callback.answer()
        return

    # Check limit (same as 3-card spread)
    today = get_user_today(user)
    daily_limit = get_daily_limit(user)

    if user.spread_reset_date != today:
        remaining = daily_limit
    else:
        remaining = daily_limit - user.tarot_spread_count

    if remaining <= 0:
        content = format_limit_exceeded()
        await callback.message.edit_text(
            **content.as_kwargs(),
            reply_markup=get_tarot_menu_keyboard(),
        )
        await callback.answer()
        return

    # Ask for question (more serious ritual for Celtic Cross)
    await callback.message.edit_text(
        "Кельтский крест — древний расклад, раскрывающий глубину ситуации.\n\n"
        "Сосредоточьтесь на своем вопросе.\n"
        "Он должен быть важным и значимым для вас.\n\n"
        "Задайте вопрос:"
    )
    await state.set_state(TarotStates.waiting_celtic_question)
    await callback.answer()


@router.message(TarotStates.waiting_celtic_question)
async def tarot_celtic_question_received(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Receive Celtic Cross question and show ritual."""
    user = await get_user(session, message.from_user.id)
    if not user:
        await message.answer("Пройдите регистрацию через /start")
        await state.clear()
        return

    # Double-check premium (in case subscription expired)
    if not user.is_premium:
        await message.answer(
            "Кельтский крест доступен только с Premium подпиской.",
            reply_markup=get_subscription_keyboard(),
        )
        await state.clear()
        return

    # Check and consume limit
    allowed, remaining = await check_and_use_tarot_limit(user, session)
    if not allowed:
        content = format_limit_exceeded()
        await message.answer(**content.as_kwargs(), reply_markup=get_tarot_menu_keyboard())
        await state.clear()
        return

    # Save question and user info
    await state.update_data(
        question=message.text,
        remaining=remaining,
        user_db_id=user.id,
        is_premium=user.is_premium,
    )

    # Show more elaborate ritual for Celtic Cross
    await message.answer("Перетасовываю колоду...")
    await asyncio.sleep(1.5)
    await message.answer("Раскладываю Кельтский крест...")
    await asyncio.sleep(1.5)

    await message.answer(
        "Десять карт перед вами...",
        reply_markup=get_draw_celtic_keyboard(),
    )


@router.callback_query(TarotCallback.filter(F.a == TarotAction.DRAW_CELTIC))
async def tarot_draw_celtic_cards(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Draw and show 10 cards as album."""
    data = await state.get_data()
    question = data.get("question")
    remaining = data.get("remaining", 0)
    user_db_id = data.get("user_db_id")
    is_premium = data.get("is_premium", False)

    # Handle expired session
    if not question:
        await callback.answer("Сессия истекла. Начните заново.", show_alert=True)
        await callback.message.delete()
        await state.clear()
        return

    await state.clear()

    # Draw 10 cards
    cards = get_ten_cards()

    await callback.message.delete()

    # Send as media group (album) - max 10 photos
    media_group = []
    for i, (card, reversed_flag) in enumerate(cards):
        photo = get_card_image(card["name_short"], reversed_flag)
        reversed_text = " (перевернутая)" if reversed_flag else ""
        position = CELTIC_CROSS_POSITIONS[i]
        caption = f"{i + 1}. {position}: {card['name']}{reversed_text}"

        media_group.append(InputMediaPhoto(media=photo, caption=caption))

    await callback.message.answer_media_group(media_group)

    # Get AI interpretation with typing indicator (returns tuple)
    ai = get_ai_service()
    cards_data = [card for card, _ in cards]
    is_reversed_list = [reversed_flag for _, reversed_flag in cards]
    result = await generate_with_feedback(
        message=callback.message,
        operation_type="tarot",
        ai_coro=ai.generate_celtic_cross(question, cards_data, is_reversed_list),
    )

    if not result:
        await callback.message.answer(
            "Не удалось создать интерпретацию. Попробуй позже.",
            reply_markup=get_tarot_menu_keyboard(),
        )
        return

    short_summary, full_interpretation = result  # Unpack tuple

    # Save FULL interpretation to history
    if user_db_id:
        await save_spread_to_history(
            session=session,
            user_id=user_db_id,
            spread_type="celtic_cross",
            question=question,
            cards=cards,
            interpretation=full_interpretation,  # Сохраняем полную версию
        )

    # Publish FULL interpretation to Telegraph (always, not fallback)
    telegraph_url = None
    try:
        telegraph_service = get_telegraph_service()
        # Truncate question for title if too long
        question_short = question[:50] + "..." if len(question) > 50 else question
        title = f"Кельтский крест — {question_short}"

        telegraph_url = await asyncio.wait_for(
            telegraph_service.publish_article(title, full_interpretation),
            timeout=TELEGRAPH_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("telegraph_celtic_timeout", question=question[:30])
    except Exception as e:
        logger.error("telegraph_celtic_error", error=str(e))

    # Show SHORT summary in Telegram + Telegraph link
    if telegraph_url:
        # Success: show short summary + button to full interpretation
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📖 Открыть полное толкование",
                        url=telegraph_url,
                    )
                ]
            ]
        )
        await callback.message.answer(
            short_summary,  # Краткое резюме вместо generic сообщения
            reply_markup=keyboard,
        )
    else:
        # Telegraph failed - show short summary + full in chunks
        await callback.message.answer(short_summary)

        # Send full interpretation in chunks (Telegram 4096 char limit)
        chunks = [
            full_interpretation[i : i + 4000]
            for i in range(0, len(full_interpretation), 4000)
        ]
        for chunk in chunks:
            await callback.message.answer(chunk)

    # Show limit
    limit_text = format_limit_message(remaining, is_premium)
    await callback.message.answer(
        limit_text,
        reply_markup=get_tarot_menu_keyboard(),
    )
    await callback.answer()


# ============== History ==============


@router.callback_query(TarotCallback.filter(F.a == TarotAction.HISTORY))
async def tarot_history_start(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """Show spread history list."""
    user = await get_user(session, callback.from_user.id)
    if not user:
        await callback.answer("Пройдите регистрацию через /start", show_alert=True)
        return

    await show_history_page(callback, session, user.id, page=0)
    await callback.answer()


@router.callback_query(HistoryCallback.filter(F.a == HistoryAction.LIST))
async def tarot_history_list(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """Return to history list."""
    user = await get_user(session, callback.from_user.id)
    if not user:
        await callback.answer("Пройдите регистрацию через /start", show_alert=True)
        return

    await show_history_page(callback, session, user.id, page=0)
    await callback.answer()


@router.callback_query(HistoryCallback.filter(F.a == HistoryAction.PAGE))
async def tarot_history_page(
    callback: CallbackQuery,
    callback_data: HistoryCallback,
    session: AsyncSession,
) -> None:
    """Handle history pagination."""
    user = await get_user(session, callback.from_user.id)
    if not user:
        await callback.answer("Пройдите регистрацию через /start", show_alert=True)
        return

    page = callback_data.p or 0
    await show_history_page(callback, session, user.id, page=page)
    await callback.answer()


async def show_history_page(
    callback: CallbackQuery,
    session: AsyncSession,
    user_id: int,
    page: int,
) -> None:
    """Show history page with spreads list.

    Args:
        callback: Callback query
        session: Database session
        user_id: User's internal ID
        page: Page number (0-indexed)
    """
    # Count total spreads
    count_stmt = (
        select(func.count())
        .select_from(TarotSpread)
        .where(TarotSpread.user_id == user_id)
    )
    total_result = await session.execute(count_stmt)
    total_count = min(total_result.scalar_one(), MAX_HISTORY_SPREADS)

    if total_count == 0:
        await callback.message.edit_text(
            "У вас пока нет сохраненных раскладов.\n\n"
            "Сделайте расклад на 3 карты или Кельтский крест,\n"
            "и он появится здесь.",
            reply_markup=get_tarot_menu_keyboard(),
        )
        return

    total_pages = (total_count + HISTORY_PAGE_SIZE - 1) // HISTORY_PAGE_SIZE

    # Get spreads for current page
    offset = page * HISTORY_PAGE_SIZE
    stmt = (
        select(TarotSpread)
        .where(TarotSpread.user_id == user_id)
        .order_by(desc(TarotSpread.created_at))
        .limit(HISTORY_PAGE_SIZE)
        .offset(offset)
    )
    result = await session.execute(stmt)
    spreads = result.scalars().all()

    await callback.message.edit_text(
        f"История раскладов ({total_count} всего)\n"
        f"Страница {page + 1}/{total_pages}",
        reply_markup=get_history_keyboard(list(spreads), page, total_pages, offset),
    )


@router.callback_query(HistoryCallback.filter(F.a == HistoryAction.VIEW))
async def tarot_history_view(
    callback: CallbackQuery,
    callback_data: HistoryCallback,
    session: AsyncSession,
) -> None:
    """View spread detail from history."""
    user = await get_user(session, callback.from_user.id)
    if not user:
        await callback.answer("Пройдите регистрацию через /start", show_alert=True)
        return

    spread_id = callback_data.i
    if not spread_id:
        await callback.answer("Расклад не найден", show_alert=True)
        return

    # Get spread (verify ownership)
    stmt = select(TarotSpread).where(
        TarotSpread.id == spread_id,
        TarotSpread.user_id == user.id,
    )
    result = await session.execute(stmt)
    spread = result.scalar_one_or_none()

    if not spread:
        await callback.answer("Расклад не найден", show_alert=True)
        return

    # Get deck for card names
    deck = get_deck()

    # Format and show
    content = format_spread_detail(spread, deck)
    await callback.message.edit_text(
        **content.as_kwargs(),
        reply_markup=get_spread_detail_keyboard(),
    )
    await callback.answer()
