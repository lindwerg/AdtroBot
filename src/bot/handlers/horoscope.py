"""Horoscope handlers with zodiac navigation."""

from datetime import date

from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.utils.formatting import Bold, Text

from src.bot.callbacks.horoscope import ZodiacCallback
from src.bot.keyboards.horoscope import build_zodiac_keyboard
from src.bot.utils.horoscope import get_horoscope_text
from src.bot.utils.zodiac import ZODIAC_SIGNS

router = Router(name="horoscope")


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

    # Get AI-generated horoscope (with caching and fallback)
    text = await get_horoscope_text(sign_name, zodiac.name_ru)

    # Format message with header and AI text
    content = Text(
        Bold(f"{zodiac.emoji} Гороскоп для {zodiac.name_ru}"),
        "\n",
        f"на {date.today().strftime('%d.%m.%Y')}",
        "\n\n",
        text,
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
    """Send formatted horoscope message with inline keyboard.

    Args:
        message: Telegram message to reply to
        sign_name: English name of zodiac sign to show (e.g., "Aries")
        user_sign: User's own sign for highlighting in keyboard (optional)
    """
    zodiac = ZODIAC_SIGNS.get(sign_name)
    if not zodiac:
        await message.answer("Знак не найден")
        return

    # Get AI-generated horoscope (with caching and fallback)
    text = await get_horoscope_text(sign_name, zodiac.name_ru)

    # Format message with header and AI text
    content = Text(
        Bold(f"{zodiac.emoji} Гороскоп для {zodiac.name_ru}"),
        "\n",
        f"на {date.today().strftime('%d.%m.%Y')}",
        "\n\n",
        text,
    )

    await message.answer(
        **content.as_kwargs(),
        reply_markup=build_zodiac_keyboard(current_sign=user_sign or sign_name),
    )
