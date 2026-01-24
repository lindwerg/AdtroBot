"""Start command and onboarding handlers."""

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.callbacks.menu import MenuAction, MenuCallback
from src.bot.keyboards.main_menu import (
    get_first_horoscope_keyboard,
    get_main_menu_keyboard,
    get_start_keyboard,
)
from src.bot.keyboards.profile import (
    build_notification_time_keyboard,
    build_onboarding_notifications_keyboard,
)
from src.bot.states.onboarding import OnboardingStates
from src.bot.utils.date_parser import parse_russian_date
from src.bot.utils.zodiac import get_zodiac_sign
from src.db.models.user import User
from src.bot.handlers.horoscope import show_horoscope_message

router = Router(name="start")

WELCOME_MESSAGE = """✨ Привет! Я твой персональный астролог и таролог.

🔮 Что я умею:
• Ежедневные гороскопы для твоего знака
• Расклады таро с AI-интерпретацией
• Карта дня — твой ежедневный ритуал

🌟 Базовые функции бесплатны!

С Premium подпиской получишь:
• Персональный гороскоп по натальной карте
• Детальные прогнозы: любовь, карьера, финансы
• 20 раскладов таро в день
• Кельтский крест (10 карт)

Готов начать? Нажми кнопку ниже 👇"""

ONBOARDING_EXPLANATION = """Теперь ты можешь получать гороскопы!

📊 Чем отличается общий гороскоп от персонального?

🆓 Общий гороскоп (бесплатно):
• Прогноз для всех представителей твоего знака
• Основан только на дате рождения
• Обновляется каждый день

⭐ Персональный гороскоп (Premium):
• Составлен по ТВОЕЙ натальной карте
• Учитывает дату, время и место рождения
• Детальные прогнозы: любовь, карьера, финансы, здоровье

Нажми кнопку, чтобы увидеть свой первый общий гороскоп 👇"""


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession, bot: Bot) -> None:
    """Handle /start command."""
    # Check if user exists and has birth_date
    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user and user.birth_date:
        # Returning user - show menu directly
        await message.answer(
            "Рад тебя видеть! Выбери раздел 👇",
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        # New user - show welcome + onboarding button
        await message.answer(
            WELCOME_MESSAGE,
            reply_markup=get_start_keyboard(),
        )


@router.callback_query(MenuCallback.filter(F.action == MenuAction.GET_FIRST_FORECAST))
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
    bot: Bot,
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
    await message.answer(f"✨ Отлично, ты {zodiac.emoji} {zodiac.name_ru}!")

    # Explain general vs premium BEFORE showing horoscope
    await message.answer(
        ONBOARDING_EXPLANATION,
        reply_markup=get_first_horoscope_keyboard(),
    )


@router.callback_query(MenuCallback.filter(F.action == MenuAction.GET_FIRST_HOROSCOPE))
async def show_first_horoscope(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """Show first general horoscope after onboarding."""
    # Get user from DB
    stmt = select(User).where(User.telegram_id == callback.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.zodiac_sign:
        await callback.answer("Ошибка: знак не найден", show_alert=True)
        return

    # Show general horoscope (no sections)
    await callback.message.delete()  # Remove button message
    await show_horoscope_message(
        message=callback.message,
        sign_name=user.zodiac_sign,
        user_sign=user.zodiac_sign,
        session=session,
        bot=bot,
        is_onboarding=True,  # NEW parameter
    )

    # Offer notifications AFTER horoscope
    await callback.message.answer(
        "Хочешь получать ежедневный гороскоп каждое утро?",
        reply_markup=build_onboarding_notifications_keyboard(),
    )

    await callback.answer()


@router.callback_query(MenuCallback.filter(F.action == MenuAction.ONBOARDING_NOTIF_YES))
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


@router.callback_query(MenuCallback.filter(F.action == MenuAction.ONBOARDING_NOTIF_NO))
async def onboarding_skip_notifications(callback: CallbackQuery) -> None:
    """User skips notifications - show main menu."""
    await callback.message.edit_text(
        "Хорошо! Вы всегда можете включить уведомления в меню Профиль."
    )
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()
