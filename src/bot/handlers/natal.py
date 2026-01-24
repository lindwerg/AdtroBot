"""Natal chart handlers for premium users."""

import asyncio

import structlog
from aiogram import F, Router
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.callbacks.natal import NatalAction, NatalCallback
from src.bot.keyboards.main_menu import get_main_menu_keyboard
from src.bot.keyboards.natal import (
    get_free_natal_keyboard,
    get_natal_setup_keyboard,
    get_natal_teaser_keyboard,
    get_natal_with_buy_keyboard,
    get_natal_with_open_keyboard,
)
from src.db.models.detailed_natal import DetailedNatal
from src.db.models.user import User
from src.bot.utils.progress import generate_with_feedback
from src.services.ai import get_ai_service
from src.services.payment.client import create_payment
from src.services.payment.schemas import PLAN_PRICES_STR, PaymentPlan
from src.services.astrology.natal_chart import calculate_full_natal_chart
from src.services.astrology.natal_svg import generate_natal_png
from src.services.telegraph import get_telegraph_service

logger = structlog.get_logger()

router = Router(name="natal")

# Telegram message character limit
MAX_MESSAGE_LENGTH = 4096

# Telegraph timeout (seconds)
TELEGRAPH_TIMEOUT = 10.0

# Track users currently generating natal chart (prevent duplicate requests)
_generating_natal: set[int] = set()


async def show_natal_chart(
    message: Message,
    user: User,
    session: AsyncSession,
) -> None:
    """Generate and display full natal chart for premium user.

    Args:
        message: Message to reply to
        user: User with birth data
        session: Database session
    """
    # Get timezone (use saved or default to Europe/Moscow)
    timezone_str = user.timezone or "Europe/Moscow"

    async def _generate_natal() -> tuple[dict, bytes, tuple[str, str | None]]:
        """Inner function to generate all natal data with typing indicator."""
        from datetime import date

        # Calculate full natal chart
        natal_data = calculate_full_natal_chart(
            birth_date=user.birth_date,
            birth_time=user.birth_time,
            latitude=user.birth_lat,
            longitude=user.birth_lon,
            timezone_str=timezone_str,
        )

        # Generate PNG visualization
        png_bytes = await generate_natal_png(natal_data)

        # Generate DAILY TRANSIT FORECAST (not static interpretation)
        today = date.today()
        ai_service = get_ai_service()
        forecast_result = await ai_service.generate_daily_transit_forecast(
            user_id=user.telegram_id,
            natal_data=natal_data,
            forecast_date=today,
            timezone_str=timezone_str,
        )

        return natal_data, png_bytes, forecast_result

    try:
        # Generate natal data with typing indicator and progress message
        natal_data, png_bytes, forecast_result = await generate_with_feedback(
            message=message,
            operation_type="transit_forecast",
            ai_coro=_generate_natal(),
        )

        forecast_text, telegraph_url = forecast_result
        from datetime import date

        today = date.today()
        date_str = today.strftime("%d.%m.%Y")

        # Determine keyboard based on user status
        if user.detailed_natal_purchased_at:
            # Already purchased - show "Open detailed" button
            keyboard = get_natal_with_open_keyboard()
        elif user.is_premium:
            # Premium but not purchased - show "Buy detailed" button
            keyboard = get_natal_with_buy_keyboard()
        else:
            # Free user - show subscription teaser
            keyboard = get_free_natal_keyboard()

        # Send chart image WITH KEYBOARD (button under photo)
        photo = BufferedInputFile(png_bytes, filename="natal_chart.png")
        caption = f"Твой ежедневный прогноз на {date_str}"

        await message.answer_photo(
            photo=photo,
            caption=caption,
            reply_markup=keyboard,
        )

        # Send Telegraph link (NO text chunks)
        if telegraph_url:
            await message.answer(
                "📖 Полный прогноз опубликован в Telegraph:",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Открыть прогноз",
                                url=telegraph_url,
                            )
                        ]
                    ]
                ),
            )
        else:
            # Fallback ONLY if Telegraph failed
            await message.answer("Не удалось опубликовать прогноз. Попробуй позже.")

        logger.info(
            "natal_chart_shown",
            user_id=user.telegram_id,
            time_known=user.birth_time is not None,
        )

    except Exception as e:
        logger.error(
            "natal_chart_error",
            user_id=user.telegram_id,
            error=str(e),
        )
        await message.answer(
            "Произошла ошибка при построении натальной карты. "
            "Попробуйте позже."
        )


def _split_text(text: str, max_length: int) -> list[str]:
    """Split text into chunks respecting paragraph boundaries.

    Args:
        text: Text to split
        max_length: Maximum length of each chunk

    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    paragraphs = text.split("\n\n")

    for para in paragraphs:
        # If single paragraph is too long, split by sentences
        if len(para) > max_length:
            sentences = para.replace(". ", ".|").split("|")
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 2 <= max_length:
                    current_chunk += sentence + " "
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + " "
        elif len(current_chunk) + len(para) + 2 <= max_length:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


@router.message(F.text == "Натальная карта")
async def menu_natal_chart(message: Message, session: AsyncSession) -> None:
    """Handle 'Натальная карта' button press from main menu."""
    # Check if already processing for this user
    user_id = message.from_user.id
    if user_id in _generating_natal:
        await message.answer("Уже создаю твою натальную карту, подожди...")
        return

    # Show immediate response to prevent multiple clicks
    loading_msg = await message.answer("Проверяю доступ...")

    # Get user
    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await loading_msg.delete()
        await message.answer(
            "Профиль не найден. Нажми /start для регистрации.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    # Check premium status
    if not user.is_premium:
        await loading_msg.delete()
        await message.answer(
            "Натальная карта доступна только премиум-пользователям.\n\n"
            "Натальная карта — это уникальный астрологический портрет, "
            "который рассчитывается по точному времени и месту рождения.\n\n"
            "Она показывает:\n"
            "- Позиции всех 11 планет\n"
            "- 12 астрологических домов\n"
            "- Аспекты между планетами\n"
            "- Детальную интерпретацию (1000+ слов)\n\n"
            "Оформите подписку, чтобы получить свою натальную карту!",
            reply_markup=get_natal_teaser_keyboard(),
        )
        return

    # Check if birth data is set
    if not user.birth_lat or not user.birth_lon:
        await loading_msg.delete()
        await message.answer(
            "Для построения натальной карты нужно указать место и время рождения.\n\n"
            "Без этих данных невозможно рассчитать точные позиции планет и домов.",
            reply_markup=get_natal_setup_keyboard(),
        )
        return

    # Check if birth_date is set
    if not user.birth_date:
        await loading_msg.delete()
        await message.answer(
            "Для построения натальной карты нужна дата рождения.\n\n"
            "Пройдите регистрацию заново через /start.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    # Delete check message and show natal chart
    await loading_msg.delete()

    # Mark as processing
    _generating_natal.add(user_id)
    try:
        await show_natal_chart(message, user, session)
    finally:
        # Always remove from set when done
        _generating_natal.discard(user_id)


@router.callback_query(NatalCallback.filter(F.action == NatalAction.SHOW_CHART))
async def callback_show_natal_chart(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Handle 'Show natal chart' callback."""
    await callback.answer()

    # Get user
    stmt = select(User).where(User.telegram_id == callback.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_premium:
        await callback.message.edit_text(
            "Натальная карта доступна только премиум-пользователям.",
            reply_markup=get_natal_teaser_keyboard(),
        )
        return

    if not user.birth_lat or not user.birth_lon or not user.birth_date:
        await callback.message.edit_text(
            "Сначала настройте данные рождения.",
            reply_markup=get_natal_setup_keyboard(),
        )
        return

    await show_natal_chart(callback.message, user, session)


@router.callback_query(NatalCallback.filter(F.action == NatalAction.BACK_TO_MENU))
async def callback_back_to_menu(callback: CallbackQuery) -> None:
    """Return to main menu."""
    await callback.answer()

    await callback.message.edit_text("Выберите раздел:")
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard(),
    )


@router.callback_query(NatalCallback.filter(F.action == NatalAction.BUY_DETAILED))
async def buy_detailed_natal(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Handle buy detailed natal interpretation button."""
    await callback.answer()

    # Get user
    stmt = select(User).where(User.telegram_id == callback.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await callback.message.answer("Ошибка. Попробуй /start")
        return

    # Check if already purchased (double-buy protection)
    if user.detailed_natal_purchased_at:
        await callback.message.answer(
            "Ты уже приобрел детальный разбор!",
            reply_markup=get_natal_with_open_keyboard(),
        )
        return

    # Check premium (required for purchase)
    if not user.is_premium:
        await callback.message.answer(
            "Детальный разбор доступен только премиум-пользователям.",
            reply_markup=get_natal_teaser_keyboard(),
        )
        return

    # Create payment
    try:
        payment = await create_payment(
            user_id=user.telegram_id,
            amount=PLAN_PRICES_STR[PaymentPlan.DETAILED_NATAL],
            description="Детальный разбор натальной карты",
            save_payment_method=False,
            metadata={
                "plan_type": PaymentPlan.DETAILED_NATAL.value,
                "type": "one_time",
            },
        )

        await callback.message.answer(
            "Детальный разбор личности (3000-5000 слов):\n\n"
            "- Ядро личности: Солнце, Луна, Асцендент\n"
            "- Мышление и коммуникация\n"
            "- Любовь и отношения\n"
            "- Энергия и действие\n"
            "- Рост и возможности\n"
            "- Уроки и ответственность\n"
            "- Трансформация и духовность\n"
            "- Персональные рекомендации\n\n"
            f"Цена: {PLAN_PRICES_STR[PaymentPlan.DETAILED_NATAL]} руб.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text="Оплатить",
                        url=payment.confirmation.confirmation_url,
                    )]
                ]
            ),
        )
    except Exception as e:
        logger.error("buy_detailed_natal_error", error=str(e))
        await callback.message.answer(
            "Ошибка при создании платежа. Попробуй позже."
        )


@router.callback_query(NatalCallback.filter(F.action == NatalAction.SHOW_DETAILED))
async def show_detailed_natal(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Show purchased detailed natal interpretation."""
    await callback.answer()

    # Get user
    stmt = select(User).where(User.telegram_id == callback.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.detailed_natal_purchased_at:
        await callback.message.answer(
            "Детальный разбор не куплен.",
            reply_markup=get_natal_with_buy_keyboard() if user and user.is_premium else get_natal_teaser_keyboard(),
        )
        return

    # Check for cached interpretation
    stmt = select(DetailedNatal).where(
        DetailedNatal.user_id == user.id
    ).order_by(DetailedNatal.created_at.desc())
    result = await session.execute(stmt)
    cached = result.scalar_one_or_none()

    if cached and cached.telegraph_url:
        # Use cached Telegraph URL (no loading needed)
        await callback.message.answer(
            "Твой детальный разбор личности готов!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text="Открыть разбор",
                        url=cached.telegraph_url,
                    )],
                    [InlineKeyboardButton(
                        text="Назад в меню",
                        callback_data=NatalCallback(action=NatalAction.BACK_TO_MENU).pack(),
                    )],
                ]
            ),
        )
        return

    # Check birth data before generation
    if not user.birth_lat or not user.birth_lon or not user.birth_date:
        await callback.message.answer(
            "Для детального разбора нужны данные рождения.",
            reply_markup=get_natal_setup_keyboard(),
        )
        return

    # Generate or regenerate with typing indicator
    async def _generate_detailed() -> str | None:
        """Inner function to generate detailed natal interpretation."""
        # Calculate natal chart
        natal_data = calculate_full_natal_chart(
            birth_date=user.birth_date,
            birth_time=user.birth_time,
            latitude=user.birth_lat,
            longitude=user.birth_lon,
            timezone_str=user.timezone or "Europe/Moscow",
        )

        # Generate detailed interpretation
        ai_service = get_ai_service()
        return await ai_service.generate_detailed_natal_interpretation(
            user_id=user.telegram_id,
            natal_data=natal_data,
        )

    try:
        interpretation = await generate_with_feedback(
            message=callback.message,
            operation_type="natal",
            ai_coro=_generate_detailed(),
        )

        if not interpretation:
            await callback.message.answer("Ошибка генерации. Попробуй позже.")
            return

        # Publish to Telegraph
        telegraph_url = None
        try:
            telegraph_service = get_telegraph_service()
            title = f"Детальный разбор - {user.birth_date.strftime('%d.%m.%Y')}"
            if user.birth_city:
                title += f", {user.birth_city}"

            telegraph_url = await asyncio.wait_for(
                telegraph_service.publish_article(title, interpretation),
                timeout=15.0,  # Longer timeout for long content
            )
        except Exception as e:
            logger.error("detailed_telegraph_error", error=str(e))

        # Save to cache
        detailed = DetailedNatal(
            user_id=user.id,
            interpretation=interpretation,
            telegraph_url=telegraph_url,
        )
        session.add(detailed)
        await session.commit()

        if telegraph_url:
            await callback.message.answer(
                "Твой детальный разбор личности готов!",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Открыть разбор", url=telegraph_url)],
                        [InlineKeyboardButton(
                            text="Назад в меню",
                            callback_data=NatalCallback(action=NatalAction.BACK_TO_MENU).pack(),
                        )],
                    ]
                ),
            )
        else:
            # Fallback: send as text chunks
            chunks = _split_text(interpretation, MAX_MESSAGE_LENGTH)
            for chunk in chunks:
                await callback.message.answer(chunk)

    except Exception as e:
        logger.error("show_detailed_natal_error", error=str(e))
        await callback.message.answer("Ошибка. Попробуй позже.")
