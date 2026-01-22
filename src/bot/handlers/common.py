"""Common handlers (catch-all for unknown messages)."""

from aiogram import Router
from aiogram.types import Message

from src.bot.keyboards.main_menu import get_main_menu_keyboard

router = Router(name="common")


@router.message()
async def unknown_message(message: Message) -> None:
    """Handle unknown messages (catch-all)."""
    await message.answer(
        "Не понимаю. Используй меню или команду /start",
        reply_markup=get_main_menu_keyboard(),
    )
