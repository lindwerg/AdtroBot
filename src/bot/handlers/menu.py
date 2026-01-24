"""Menu button handlers."""

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.callbacks.menu import MenuAction, MenuCallback
from src.bot.handlers.horoscope import show_horoscope_message
from src.bot.handlers.main_menu import show_main_menu
from src.bot.handlers.subscription import show_plans
from src.bot.keyboards.main_menu import get_main_menu_keyboard
from src.bot.keyboards.profile import build_profile_actions_keyboard
from src.bot.keyboards.tarot import get_tarot_menu_keyboard
from src.db.models.user import User
from src.services.payment import get_user_subscription

router = Router(name="menu")


@router.message(F.text == "Гороскоп")
async def menu_horoscope(message: Message, session: AsyncSession) -> None:
    """Handle 'Гороскоп' button press."""
    # Check if user has zodiac_sign
    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user and user.zodiac_sign:
        await show_horoscope_message(message, user.zodiac_sign, user.zodiac_sign, session)
    else:
        await message.answer(
            "Для получения гороскопа нужно указать дату рождения. "
            "Нажми /start и пройди регистрацию."
        )


@router.message(F.text == "Таро")
async def menu_tarot(message: Message) -> None:
    """Handle 'Таро' button press - show tarot menu."""
    await message.answer(
        "Выберите тип расклада:",
        reply_markup=get_tarot_menu_keyboard(),
    )


@router.message(F.text == "Подписка")
async def menu_subscription(message: Message, session: AsyncSession) -> None:
    """Handle 'Подписка' button press."""
    await show_plans(message, session)


@router.message(F.text == "Профиль")
async def menu_profile(message: Message, session: AsyncSession) -> None:
    """Handle 'Профиль' button press."""
    # Get user info
    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await message.answer(
            "Профиль не найден. Нажми /start для регистрации.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    # Build profile text
    lines = [f"Telegram ID: {user.telegram_id}"]

    if user.zodiac_sign:
        lines.append(f"Знак зодиака: {user.zodiac_sign}")
    else:
        lines.append("Знак зодиака: не указан")

    if user.birth_date:
        lines.append(f"Дата рождения: {user.birth_date.strftime('%d.%m.%Y')}")
    else:
        lines.append("Дата рождения: не указана")

    # Show birth data for premium users
    if user.is_premium and user.birth_city:
        lines.append(f"Город рождения: {user.birth_city}")
        if user.birth_time:
            lines.append(f"Время рождения: {user.birth_time.strftime('%H:%M')}")
        else:
            lines.append("Время рождения: не указано (12:00)")

    # Subscription status
    subscription = await get_user_subscription(session, message.from_user.id)
    if subscription and user.is_premium:
        until_str = user.premium_until.strftime("%d.%m.%Y") if user.premium_until else "N/A"
        if subscription.status == "active":
            lines.append(f"\nПодписка: Премиум до {until_str}")
        elif subscription.status == "canceled":
            lines.append(f"\nПодписка: Отменена (доступ до {until_str})")
        elif subscription.status == "trial":
            lines.append(f"\nПодписка: Пробный период до {until_str}")
    else:
        lines.append("\nПодписка: Бесплатный тариф")
        lines.append(f"Раскладов сегодня: {user.tarot_spread_count}/{user.daily_spread_limit}")

    # Build keyboard with profile actions
    has_birth_data = user.birth_city is not None
    keyboard = build_profile_actions_keyboard(
        is_premium=user.is_premium,
        has_birth_data=has_birth_data,
        has_subscription=subscription is not None,
        subscription_status=subscription.status if subscription else None,
    )

    await message.answer("\n".join(lines), reply_markup=keyboard)


@router.message(F.text == "Главное меню")
async def menu_main(message: Message, session: AsyncSession) -> None:
    """Handle 'Главное меню' reply button press."""
    await show_main_menu(message, session)


@router.callback_query(MenuCallback.filter(F.action == MenuAction.BACK_TO_MAIN_MENU))
async def callback_main_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    """Handle '🏠 Главное меню' inline button press."""
    await callback.message.delete()  # Remove previous message
    await show_main_menu(callback.message, session)
    await callback.answer()
