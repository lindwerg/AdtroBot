"""Bot and Dispatcher instances."""

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot.handlers import (
    astrologer_chat_router,
    birth_data_router,
    common_router,
    horoscope_router,
    menu_router,
    natal_router,
    profile_settings_router,
    start_router,
    subscription_router,
    tarot_router,
)
from src.config import settings

# Bot created lazily - token validated only when token is present
# Empty token is allowed for local development without Telegram
bot: Bot | None = None
dp = Dispatcher(storage=MemoryStorage())

# Register routers (order matters: start -> menu -> subscription -> horoscope -> natal -> astrologer_chat -> tarot -> birth_data -> profile_settings -> common)
dp.include_routers(
    start_router,
    menu_router,
    subscription_router,
    horoscope_router,
    natal_router,
    astrologer_chat_router,  # NEW: AI astrologer chat (after natal)
    tarot_router,
    birth_data_router,
    profile_settings_router,
    common_router,
)


def get_bot() -> Bot:
    """Get or create Bot instance. Raises if token not configured."""
    global bot
    if bot is None:
        if not settings.telegram_bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN not configured")
        bot = Bot(token=settings.telegram_bot_token)
    return bot
