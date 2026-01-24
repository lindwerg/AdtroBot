"""Handlers for astrologer chat feature."""

import asyncio
from datetime import date

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.callbacks.natal import NatalAction, NatalCallback
from src.bot.keyboards.natal import get_astrologer_chat_keyboard
from src.bot.keyboards.main_menu import get_main_menu_keyboard
from src.bot.states.astrologer_chat import AstrologerChatStates
from src.db.models.user import User
from src.services.ai import get_ai_service
from src.services.ai.astrologer_cache import (
    add_message,
    check_question_limit,
    create_conversation,
    end_conversation,
    get_conversation,
    get_remaining_questions,
    increment_question_count,
)
from src.services.astrology.natal_chart import calculate_full_natal_chart
from src.services.astrology.transits import calculate_daily_transits

logger = structlog.get_logger()

router = Router(name="astrologer_chat")

# Cooldown between questions (10 seconds for all users)
QUESTION_COOLDOWN = 10.0

# Track last question time per user (in-memory)
_last_question_time: dict[int, float] = {}


@router.callback_query(NatalCallback.filter(F.action == NatalAction.START_CHAT))
async def start_astrologer_chat(
    callback: CallbackQuery,
    callback_data: NatalCallback,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Start astrologer chat conversation.

    Args:
        callback: Callback query
        callback_data: Parsed callback data
        state: FSM context
        session: Database session
    """
    if not callback.message or not callback.from_user:
        await callback.answer("Ошибка обработки запроса")
        return

    user_id = callback.from_user.id

    # Get user from DB
    result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Пользователь не найден")
        return

    # Check birth data
    if not user.birth_date or not user.birth_lat or not user.birth_lon:
        await callback.answer(
            "Сначала настрой данные рождения в натальной карте",
            show_alert=True,
        )
        return

    # Check question limit (freemium)
    can_ask = await check_question_limit(user_id, user.is_premium)
    if not can_ask:
        remaining = await get_remaining_questions(user_id, user.is_premium)
        await callback.message.answer(
            f"⚠️ Ты использовал свои {3 - (remaining or 0)} бесплатных вопроса астрологу на сегодня.\n\n"
            "Оформи Premium для безлимитного диалога!",
            reply_markup=get_main_menu_keyboard(),
        )
        await callback.answer()
        return

    # Calculate natal chart and today's transits
    timezone_str = user.timezone or "Europe/Moscow"

    try:
        # Show "typing..." indicator
        await callback.message.bot.send_chat_action(
            chat_id=callback.message.chat.id,
            action="typing",
        )

        natal_data = calculate_full_natal_chart(
            birth_date=user.birth_date,
            birth_time=user.birth_time,
            latitude=user.birth_lat,
            longitude=user.birth_lon,
            timezone_str=timezone_str,
        )

        transit_data = calculate_daily_transits(
            natal_data=natal_data,
            forecast_date=date.today(),
            timezone_str=timezone_str,
        )

        # Create conversation context
        await create_conversation(
            user_id=user_id,
            natal_data=natal_data,
            transit_data=transit_data,
        )

        # Set FSM state
        await state.set_state(AstrologerChatStates.in_conversation)

        # Get remaining questions info
        remaining = await get_remaining_questions(user_id, user.is_premium)
        limit_text = ""
        if remaining is not None:
            limit_text = f"\n\nУ тебя осталось {remaining} бесплатных вопроса на сегодня."

        # Send welcome message
        await callback.message.answer(
            f"Привет! Я твой личный астролог.\n\n"
            f"Задай мне любой вопрос о твоей натальной карте:\n"
            f"• Что означают позиции планет?\n"
            f"• Как аспекты влияют на твою жизнь?\n"
            f"• Что сегодняшние транзиты значат для тебя?{limit_text}",
            reply_markup=get_astrologer_chat_keyboard(),
        )

        await callback.answer()

        logger.info(
            "astrologer_chat_started",
            user_id=user_id,
            is_premium=user.is_premium,
            remaining_questions=remaining,
        )

    except Exception as e:
        logger.error(
            "astrologer_chat_start_error",
            user_id=user_id,
            error=str(e),
        )
        await callback.message.answer(
            "Произошла ошибка при запуске диалога. Попробуй позже.",
            reply_markup=get_main_menu_keyboard(),
        )
        await callback.answer()


@router.callback_query(NatalCallback.filter(F.action == NatalAction.END_CHAT))
async def end_astrologer_chat(
    callback: CallbackQuery,
    callback_data: NatalCallback,
    state: FSMContext,
) -> None:
    """End astrologer chat conversation.

    Args:
        callback: Callback query
        callback_data: Parsed callback data
        state: FSM context
    """
    if not callback.message or not callback.from_user:
        await callback.answer("Ошибка обработки запроса")
        return

    user_id = callback.from_user.id

    # End conversation
    await end_conversation(user_id)

    # Clear FSM state
    await state.clear()

    # Send goodbye message
    await callback.message.answer(
        "Диалог завершён. Приходи ещё!",
        reply_markup=get_main_menu_keyboard(),
    )

    await callback.answer()

    logger.info("astrologer_chat_ended", user_id=user_id)


@router.message(AstrologerChatStates.in_conversation)
async def handle_astrologer_question(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle user question in astrologer chat.

    Args:
        message: User message with question
        state: FSM context
        session: Database session
    """
    if not message.text or not message.from_user:
        return

    user_id = message.from_user.id
    question = message.text.strip()

    # Validate question length
    if len(question) > 500:
        await message.answer(
            "Вопрос слишком длинный. Пожалуйста, сформулируй его короче (до 500 символов).",
            reply_markup=get_astrologer_chat_keyboard(),
        )
        return

    if len(question) < 5:
        await message.answer(
            "Вопрос слишком короткий. Опиши подробнее, что тебя интересует.",
            reply_markup=get_astrologer_chat_keyboard(),
        )
        return

    # Check cooldown
    import time

    now = time.time()
    if user_id in _last_question_time:
        elapsed = now - _last_question_time[user_id]
        if elapsed < QUESTION_COOLDOWN:
            remaining = int(QUESTION_COOLDOWN - elapsed)
            await message.answer(
                f"Подожди ещё {remaining} секунд перед следующим вопросом.",
                reply_markup=get_astrologer_chat_keyboard(),
            )
            return

    # Get user from DB
    result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        await message.answer("Пользователь не найден")
        await state.clear()
        return

    # Check question limit
    can_ask = await check_question_limit(user_id, user.is_premium)
    if not can_ask:
        await end_conversation(user_id)
        await state.clear()

        remaining = await get_remaining_questions(user_id, user.is_premium)
        await message.answer(
            f"⚠️ Ты использовал свои {3 - (remaining or 0)} бесплатных вопроса астрологу на сегодня.\n\n"
            "Оформи Premium для безлимитного диалога!",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    # Get conversation context
    conv = await get_conversation(user_id)
    if not conv:
        await message.answer(
            "Диалог истёк (30 минут неактивности). Начни новый диалог.",
            reply_markup=get_main_menu_keyboard(),
        )
        await state.clear()
        return

    # Update last question time
    _last_question_time[user_id] = now

    # Add user question to history
    await add_message(user_id, "user", question)

    # Increment question count for free users
    if not user.is_premium:
        await increment_question_count(user_id)

    # Show typing indicator
    try:
        await message.bot.send_chat_action(
            chat_id=message.chat.id,
            action="typing",
        )

        # Generate AI response
        ai_service = get_ai_service()
        response = await ai_service.chat_with_astrologer(
            user_id=user_id,
            question=question,
            natal_data=conv["natal_data"],
            conversation_history=conv["messages"],
            transit_data=conv["transit_data"],
        )

        if not response:
            await message.answer(
                "Произошла ошибка при генерации ответа. Попробуй переформулировать вопрос.",
                reply_markup=get_astrologer_chat_keyboard(),
            )
            logger.error(
                "astrologer_response_failed",
                user_id=user_id,
                question_length=len(question),
            )
            return

        # Add AI response to history
        await add_message(user_id, "assistant", response)

        # Send response
        await message.answer(
            response,
            reply_markup=get_astrologer_chat_keyboard(),
        )

        # Log success
        remaining = await get_remaining_questions(user_id, user.is_premium)
        logger.info(
            "astrologer_question_answered",
            user_id=user_id,
            question_length=len(question),
            response_length=len(response),
            remaining_questions=remaining,
        )

    except asyncio.CancelledError:
        # Task was cancelled (user stopped bot, etc.)
        logger.warning("astrologer_question_cancelled", user_id=user_id)
        raise
    except Exception as e:
        logger.error(
            "astrologer_question_error",
            user_id=user_id,
            error=str(e),
        )
        await message.answer(
            "Произошла ошибка. Попробуй задать вопрос ещё раз.",
            reply_markup=get_astrologer_chat_keyboard(),
        )
