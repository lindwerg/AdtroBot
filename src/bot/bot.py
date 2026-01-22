"""Bot and Dispatcher instances."""

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot.handlers import (
    common_router,
    horoscope_router,
    menu_router,
    profile_settings_router,
    start_router,
    tarot_router,
)
from src.config import settings

# Bot created lazily - token validated only when token is present
# Empty token is allowed for local development without Telegram
bot: Bot | None = None
dp = Dispatcher(storage=MemoryStorage())

# Register routers (order matters: start -> menu -> horoscope -> tarot -> profile_settings -> common)
dp.include_routers(
    start_router, menu_router, horoscope_router, tarot_router, profile_settings_router, common_router
)


def get_bot() -> Bot:
    """Get or create Bot instance. Raises if token not configured."""
    global bot
    if bot is None:
        if not settings.telegram_bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN not configured")
        bot = Bot(token=settings.telegram_bot_token)
    return bot
