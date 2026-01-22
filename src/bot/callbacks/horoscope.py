"""Callback data for horoscope handlers."""

from aiogram.filters.callback_data import CallbackData


class ZodiacCallback(CallbackData, prefix="z"):
    """
    Callback data for zodiac sign selection.

    Short field name 's' keeps callback_data under 64 byte limit.

    Usage:
        button(text="♈️", callback_data=ZodiacCallback(s="Aries").pack())

        @router.callback_query(ZodiacCallback.filter())
        async def handler(callback: CallbackQuery, callback_data: ZodiacCallback):
            sign = callback_data.s  # "Aries"
    """

    s: str  # English sign name (e.g., "Aries")
