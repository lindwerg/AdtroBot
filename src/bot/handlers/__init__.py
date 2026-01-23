"""Telegram bot handlers."""

from src.bot.handlers.birth_data import router as birth_data_router
from src.bot.handlers.common import router as common_router
from src.bot.handlers.horoscope import router as horoscope_router
from src.bot.handlers.menu import router as menu_router
from src.bot.handlers.natal import router as natal_router
from src.bot.handlers.profile import router as profile_settings_router
from src.bot.handlers.start import router as start_router
from src.bot.handlers.subscription import router as subscription_router
from src.bot.handlers.tarot import router as tarot_router

__all__ = [
    "start_router",
    "menu_router",
    "subscription_router",
    "horoscope_router",
    "natal_router",
    "profile_settings_router",
    "birth_data_router",
    "tarot_router",
    "common_router",
]
