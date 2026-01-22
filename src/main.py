from contextlib import asynccontextmanager

import structlog
from aiogram.types import Update
from fastapi import FastAPI, Request, Response

from src.bot.bot import dp, get_bot
from src.bot.middlewares.db import DbSessionMiddleware
from src.config import settings
from src.core.logging import configure_logging
from src.db.engine import engine
from src.services.scheduler import get_scheduler

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup: configure logging
    configure_logging(
        log_level=settings.log_level,
        json_logs=settings.railway_environment is not None,
    )

    # Register bot middlewares
    dp.update.middleware(DbSessionMiddleware())

    # Start scheduler
    scheduler = get_scheduler()
    scheduler.start()
    await logger.ainfo("Scheduler started")

    # Set webhook (only if token configured)
    bot = None
    if settings.telegram_bot_token and settings.webhook_base_url:
        bot = get_bot()
        webhook_url = f"{settings.webhook_base_url}/webhook"
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.webhook_secret,
            drop_pending_updates=True,
        )
        await logger.ainfo("Webhook set", url=webhook_url)

    yield

    # Shutdown: cleanup scheduler
    scheduler.shutdown(wait=False)
    await logger.ainfo("Scheduler shutdown")

    # Shutdown: cleanup bot
    if bot is not None:
        await bot.delete_webhook()
        await bot.session.close()
        await logger.ainfo("Bot webhook deleted and session closed")

    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(request: Request) -> Response:
    """Handle Telegram webhook updates."""
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != settings.webhook_secret:
        return Response(status_code=401)

    bot = get_bot()
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return Response(status_code=200)
