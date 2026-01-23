"""Horoscope handlers with zodiac navigation and premium support."""

from datetime import date

from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.utils.formatting import Bold, Text
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.callbacks.horoscope import ZodiacCallback
from src.bot.keyboards.horoscope import build_zodiac_keyboard
from src.bot.utils.horoscope import get_horoscope_text
from src.bot.utils.zodiac import ZODIAC_SIGNS
from src.db.models.user import User
from src.services.ai.client import get_ai_service
from src.services.astrology import calculate_natal_chart

router = Router(name="horoscope")

# Premium teaser for free users
PREMIUM_TEASER = """
━━━━━━━━━━━━━━━━━━━━━━━━
⭐ ПРЕМИУМ-ГОРОСКОП

Это был краткий прогноз. С подпиской получишь:

• Детальный гороскоп по сферам: любовь, карьера, здоровье, финансы
• Персональный прогноз на основе твоей натальной карты
• 20 раскладов таро в день вместо 1
• Кельтский крест (расклад на 10 карт)

Всего 299 ₽/мес — нажми кнопку ниже ↓
━━━━━━━━━━━━━━━━━━━━━━━━"""

# Prompt for premium users without natal data
SETUP_NATAL_PROMPT = """
Для полного персонального прогноза укажи место и время рождения в настройках профиля.
Нажми кнопку ниже."""


@router.callback_query(ZodiacCallback.filter())
async def show_zodiac_horoscope(
    callback: CallbackQuery,
    callback_data: ZodiacCallback,
    session: AsyncSession,
) -> None:
    """Show horoscope for selected zodiac sign."""
    sign_name = callback_data.s
    zodiac = ZODIAC_SIGNS.get(sign_name)

    if not zodiac:
        await callback.answer("Знак не найден", show_alert=True)
        return

    # Get user for premium check
    stmt = select(User).where(User.telegram_id == callback.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    today = date.today()
    date_str = today.strftime("%d.%m.%Y")

    # Determine horoscope type based on user status
    if user and user.is_premium:
        if user.birth_lat and user.birth_lon and user.birth_date:
            # Premium with natal data - personalized horoscope
            natal_data = calculate_natal_chart(
                birth_date=user.birth_date,
                birth_time=user.birth_time,
                latitude=user.birth_lat,
                longitude=user.birth_lon,
            )
            ai_service = get_ai_service()
            text = await ai_service.generate_premium_horoscope(
                user_id=callback.from_user.id,
                zodiac_sign=sign_name,
                zodiac_sign_ru=zodiac.name_ru,
                date_str=date_str,
                natal_data=natal_data,
            )
            if text is None:
                # Fallback to basic horoscope on error
                text = await get_horoscope_text(sign_name, zodiac.name_ru)
            header = f"{zodiac.emoji} Персональный гороскоп для {zodiac.name_ru}"
        else:
            # Premium without natal data - basic + setup prompt
            text = await get_horoscope_text(sign_name, zodiac.name_ru)
            text = f"{text}\n\n{SETUP_NATAL_PROMPT}"
            header = f"{zodiac.emoji} Гороскоп для {zodiac.name_ru}"
    else:
        # Free user - basic + teaser
        text = await get_horoscope_text(sign_name, zodiac.name_ru)
        text = f"{text}\n\n{PREMIUM_TEASER}"
        header = f"{zodiac.emoji} Гороскоп для {zodiac.name_ru}"

    # Format message
    content = Text(
        Bold(header),
        "\n",
        f"на {date_str}",
        "\n\n",
        text,
    )

    # Build keyboard based on user status
    is_premium = user.is_premium if user else False
    has_natal = bool(user and user.birth_lat and user.birth_lon) if user else False

    await callback.message.edit_text(
        **content.as_kwargs(),
        reply_markup=build_zodiac_keyboard(
            current_sign=sign_name,
            is_premium=is_premium,
            has_natal_data=has_natal,
        ),
    )
    await callback.answer()


async def show_horoscope_message(
    message: Message,
    sign_name: str,
    user_sign: str | None = None,
    session: AsyncSession | None = None,
) -> None:
    """Send formatted horoscope message with inline keyboard.

    Args:
        message: Telegram message to reply to
        sign_name: English name of zodiac sign to show (e.g., "Aries")
        user_sign: User's own sign for highlighting in keyboard (optional)
        session: Database session for premium check (optional)
    """
    zodiac = ZODIAC_SIGNS.get(sign_name)
    if not zodiac:
        await message.answer("Знак не найден")
        return

    today = date.today()
    date_str = today.strftime("%d.%m.%Y")

    # Default values
    is_premium = False
    has_natal = False
    header = f"{zodiac.emoji} Гороскоп для {zodiac.name_ru}"

    # Check premium status if session provided
    user = None
    if session and message.from_user:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

    if user and user.is_premium:
        is_premium = True
        has_natal = bool(user.birth_lat and user.birth_lon)

        if has_natal and user.birth_date:
            # Premium with natal data - personalized horoscope
            natal_data = calculate_natal_chart(
                birth_date=user.birth_date,
                birth_time=user.birth_time,
                latitude=user.birth_lat,
                longitude=user.birth_lon,
            )
            ai_service = get_ai_service()
            text = await ai_service.generate_premium_horoscope(
                user_id=message.from_user.id,
                zodiac_sign=sign_name,
                zodiac_sign_ru=zodiac.name_ru,
                date_str=date_str,
                natal_data=natal_data,
            )
            if text is None:
                # Fallback to basic horoscope on error
                text = await get_horoscope_text(sign_name, zodiac.name_ru)
            header = f"{zodiac.emoji} Персональный гороскоп для {zodiac.name_ru}"
        else:
            # Premium without natal data - basic + setup prompt
            text = await get_horoscope_text(sign_name, zodiac.name_ru)
            text = f"{text}\n\n{SETUP_NATAL_PROMPT}"
    else:
        # Free user or no session - basic + teaser
        text = await get_horoscope_text(sign_name, zodiac.name_ru)
        if session:  # Only add teaser if we checked user status
            text = f"{text}\n\n{PREMIUM_TEASER}"

    # Format message with header and AI text
    content = Text(
        Bold(header),
        "\n",
        f"на {date_str}",
        "\n\n",
        text,
    )

    await message.answer(
        **content.as_kwargs(),
        reply_markup=build_zodiac_keyboard(
            current_sign=user_sign or sign_name,
            is_premium=is_premium,
            has_natal_data=has_natal,
        ),
    )
