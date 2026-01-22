"""Horoscope handlers with zodiac navigation."""

from datetime import date

from aiogram import Router
from aiogram.types import CallbackQuery, Message

from src.bot.callbacks.horoscope import ZodiacCallback
from src.bot.keyboards.horoscope import build_zodiac_keyboard
from src.bot.utils.formatting import format_daily_horoscope
from src.bot.utils.horoscope import get_mock_horoscope
from src.bot.utils.zodiac import ZODIAC_SIGNS

router = Router(name="horoscope")


def _parse_mock_horoscope(text: str) -> tuple[str, str]:
    """
    Split mock horoscope into forecast and tip.

    Mock horoscopes are single paragraphs. Split roughly 70/30 for forecast/tip.

    Args:
        text: Full horoscope text (may start with emoji)

    Returns:
        Tuple of (general_forecast, daily_tip)
    """
    # Remove emoji prefix (zodiac symbol + space)
    clean = text.lstrip()
    if clean and clean[0] in "♈♉♊♋♌♍♎♏♐♑♒♓":
        clean = clean[2:].lstrip()

    sentences = clean.split(". ")
    if len(sentences) <= 2:
        return clean, "Доверяйте интуиции."

    # Take all but last sentence for forecast, last for tip
    forecast = ". ".join(sentences[:-1]) + "."
    tip = sentences[-1]
    if not tip.endswith("."):
        tip += "."
    return forecast, tip


@router.callback_query(ZodiacCallback.filter())
async def show_zodiac_horoscope(
    callback: CallbackQuery, callback_data: ZodiacCallback
) -> None:
    """Show horoscope for selected zodiac sign."""
    sign_name = callback_data.s
    zodiac = ZODIAC_SIGNS.get(sign_name)

    if not zodiac:
        await callback.answer("Знак не найден", show_alert=True)
        return

    # Get mock horoscope and split
    raw = get_mock_horoscope(sign_name)
    forecast, tip = _parse_mock_horoscope(raw)

    # Format message
    content = format_daily_horoscope(
        sign_emoji=zodiac.emoji,
        sign_name_ru=zodiac.name_ru,
        forecast_date=date.today(),
        general_forecast=forecast,
        daily_tip=tip,
    )

    # Edit message with new horoscope and keyboard (highlight current sign)
    await callback.message.edit_text(
        **content.as_kwargs(),
        reply_markup=build_zodiac_keyboard(current_sign=sign_name),
    )
    await callback.answer()


async def show_horoscope_message(
    message: Message, sign_name: str, user_sign: str | None = None
) -> None:
    """
    Send formatted horoscope message with inline keyboard.

    Args:
        message: Telegram message to reply to
        sign_name: English name of zodiac sign to show (e.g., "Aries")
        user_sign: User's own sign for highlighting in keyboard (optional)
    """
    zodiac = ZODIAC_SIGNS.get(sign_name)
    if not zodiac:
        await message.answer("Знак не найден")
        return

    raw = get_mock_horoscope(sign_name)
    forecast, tip = _parse_mock_horoscope(raw)

    content = format_daily_horoscope(
        sign_emoji=zodiac.emoji,
        sign_name_ru=zodiac.name_ru,
        forecast_date=date.today(),
        general_forecast=forecast,
        daily_tip=tip,
    )

    await message.answer(
        **content.as_kwargs(),
        reply_markup=build_zodiac_keyboard(current_sign=user_sign or sign_name),
    )
