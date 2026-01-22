"""Telegram bot handlers."""

from src.bot.handlers.start import router as start_router
from src.bot.handlers.menu import router as menu_router
from src.bot.handlers.horoscope import router as horoscope_router
from src.bot.handlers.common import router as common_router

__all__ = ["start_router", "menu_router", "horoscope_router", "common_router"]
