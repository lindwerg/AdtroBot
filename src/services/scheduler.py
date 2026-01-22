"""APScheduler setup for daily horoscope notifications."""

from datetime import date

import structlog
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import utc

from src.config import settings

logger = structlog.get_logger()

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the scheduler instance."""
    global _scheduler
    if _scheduler is None:
        # SQLAlchemyJobStore needs sync URL
        sync_url = settings.sync_database_url

        jobstores = {"default": SQLAlchemyJobStore(url=sync_url)}
        _scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            timezone=utc,
        )
    return _scheduler


async def send_daily_horoscope(user_id: int, zodiac_sign: str) -> None:
    """Job function: send horoscope notification to user.

    NOTE: Bot instance fetched inside function - cannot serialize Bot in jobstore.
    """
    from src.bot.bot import get_bot
    from src.bot.utils.formatting import format_daily_horoscope
    from src.bot.utils.horoscope import get_mock_horoscope
    from src.bot.utils.zodiac import ZODIAC_SIGNS

    bot = get_bot()
    zodiac = ZODIAC_SIGNS.get(zodiac_sign)
    if not zodiac:
        await logger.awarning(
            "Unknown zodiac sign for notification", user_id=user_id, sign=zodiac_sign
        )
        return

    # Get and format horoscope
    raw = get_mock_horoscope(zodiac_sign)
    # Simple split for notification (first sentence as tip)
    clean = raw.lstrip()
    if clean and clean[0] in "\u2648\u2649\u264a\u264b\u264c\u264d\u264e\u264f\u2650\u2651\u2652\u2653":
        clean = clean[2:].lstrip()

    sentences = clean.split(". ")
    if len(sentences) > 1:
        forecast = ". ".join(sentences[:-1]) + "."
        tip = sentences[-1].rstrip(".") + "."
    else:
        forecast = raw
        tip = "Хорошего дня!"

    content = format_daily_horoscope(
        sign_emoji=zodiac.emoji,
        sign_name_ru=zodiac.name_ru,
        forecast_date=date.today(),
        general_forecast=forecast,
        daily_tip=tip,
    )

    try:
        await bot.send_message(chat_id=user_id, **content.as_kwargs())
        await logger.ainfo("Sent daily horoscope", user_id=user_id, sign=zodiac_sign)
    except Exception as e:
        await logger.aerror("Failed to send horoscope notification", user_id=user_id, error=str(e))


def schedule_user_notification(
    user_id: int, hour: int, timezone: str, zodiac_sign: str
) -> None:
    """Schedule daily horoscope notification for user.

    Args:
        user_id: Telegram user ID
        hour: Hour in user's local time (0-23)
        timezone: IANA timezone string (e.g., "Europe/Moscow")
        zodiac_sign: English zodiac sign name
    """
    scheduler = get_scheduler()
    job_id = f"horoscope_{user_id}"

    scheduler.add_job(
        send_daily_horoscope,
        CronTrigger(hour=hour, minute=0, timezone=timezone),
        args=[user_id, zodiac_sign],
        id=job_id,
        replace_existing=True,  # Avoid duplicates on reschedule
        misfire_grace_time=3600,  # 1 hour grace for misfires
    )
    logger.info("Scheduled notification", user_id=user_id, hour=hour, timezone=timezone)


def remove_user_notification(user_id: int) -> None:
    """Remove scheduled notification for user."""
    scheduler = get_scheduler()
    job_id = f"horoscope_{user_id}"

    try:
        scheduler.remove_job(job_id)
        logger.info("Removed notification", user_id=user_id)
    except Exception:
        # Job might not exist
        pass
