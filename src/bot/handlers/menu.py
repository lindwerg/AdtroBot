"""Menu button handlers."""

from aiogram import F, Router
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.handlers.horoscope import show_horoscope_message
from src.bot.handlers.subscription import show_plans
from src.bot.keyboards.main_menu import get_main_menu_keyboard
from src.bot.keyboards.tarot import get_tarot_menu_keyboard
from src.db.models.user import User

router = Router(name="menu")


@router.message(F.text == "Гороскоп")
async def menu_horoscope(message: Message, session: AsyncSession) -> None:
    """Handle 'Гороскоп' button press."""
    # Check if user has zodiac_sign
    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user and user.zodiac_sign:
        await show_horoscope_message(message, user.zodiac_sign, user.zodiac_sign)
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

    # Build inline keyboard with notifications settings button
    builder = InlineKeyboardBuilder()
    builder.button(text="Настройки уведомлений", callback_data="profile_notifications")

    await message.answer("\n".join(lines), reply_markup=builder.as_markup())
