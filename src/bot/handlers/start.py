"""Start command and onboarding handlers."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.main_menu import get_main_menu_keyboard, get_start_keyboard
from src.bot.keyboards.profile import (
    build_notification_time_keyboard,
    build_onboarding_notifications_keyboard,
    build_timezone_keyboard,
)
from src.bot.states.onboarding import OnboardingStates
from src.bot.utils.date_parser import parse_russian_date
from src.bot.utils.horoscope import get_mock_horoscope
from src.bot.utils.zodiac import get_zodiac_sign
from src.db.models.user import User
from src.services.scheduler import schedule_user_notification

router = Router(name="start")

WELCOME_MESSAGE = """Привет! Я астробот - твой персональный проводник в мир астрологии и таро.

Что я умею:
- Ежедневные гороскопы для твоего знака
- Расклады таро с AI-интерпретацией
- Персональные прогнозы

Базовые функции бесплатны. Подписка открывает детальные гороскопы по сферам жизни и расширенные расклады."""


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession) -> None:
    """Handle /start command."""
    # Check if user exists and has birth_date
    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user and user.birth_date:
        # Returning user - show menu directly
        await message.answer(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        # New user - show welcome + onboarding button
        await message.answer(
            WELCOME_MESSAGE,
            reply_markup=get_start_keyboard(),
        )


@router.callback_query(F.data == "get_first_forecast")
async def start_onboarding(callback: CallbackQuery, state: FSMContext) -> None:
    """Start birthdate collection."""
    await callback.message.answer(
        "Введи дату рождения (например, 15.03.1990 или 15 марта 1990):"
    )
    await state.set_state(OnboardingStates.waiting_birthdate)
    await callback.answer()


@router.message(OnboardingStates.waiting_birthdate)
async def process_birthdate(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Process birthdate input."""
    parsed_date = parse_russian_date(message.text)

    if not parsed_date:
        await message.answer("Неверный формат. Попробуй ещё раз")
        return

    zodiac = get_zodiac_sign(parsed_date)

    # Update or create user
    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        session.add(user)

    user.birth_date = parsed_date
    user.zodiac_sign = zodiac.name

    # CRITICAL: DbSessionMiddleware does NOT auto-commit
    await session.commit()

    # Clear FSM state
    await state.clear()

    # Show zodiac
    await message.answer(f"Твой знак: {zodiac.emoji} {zodiac.name_ru}")

    # Show mock horoscope (immediate value)
    horoscope = get_mock_horoscope(zodiac.name)
    await message.answer(horoscope)

    # Offer to enable notifications (onboarding step)
    await message.answer(
        "Хотите получать ежедневный гороскоп каждое утро?",
        reply_markup=build_onboarding_notifications_keyboard(),
    )


@router.callback_query(F.data == "onboarding_notif_yes")
async def onboarding_enable_notifications(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """User wants notifications - show time selection."""
    stmt = select(User).where(User.telegram_id == callback.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        user.notifications_enabled = True
        await session.commit()

    await callback.message.edit_text(
        "Отлично! Выберите время для уведомлений:",
        reply_markup=build_notification_time_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "onboarding_notif_no")
async def onboarding_skip_notifications(callback: CallbackQuery) -> None:
    """User skips notifications - show main menu."""
    await callback.message.edit_text(
        "Хорошо! Вы всегда можете включить уведомления в меню Профиль."
    )
    await callback.message.answer(
        "Хочешь карту дня? Нажми 'Таро'",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()
