"""APScheduler setup for daily horoscope notifications and subscription management."""

from datetime import date, datetime, timedelta, timezone as tz

import structlog
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import utc
from sqlalchemy import and_, delete, select

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

        # Add subscription management jobs
        _scheduler.add_job(
            auto_renew_subscriptions,
            CronTrigger(hour=9, minute=0, timezone="Europe/Moscow"),
            id="auto_renew_subscriptions",
            replace_existing=True,
            misfire_grace_time=3600,
        )

        _scheduler.add_job(
            check_expiring_subscriptions,
            CronTrigger(hour=10, minute=0, timezone="Europe/Moscow"),
            id="check_expiring_subscriptions",
            replace_existing=True,
            misfire_grace_time=3600,
        )

        # Add daily horoscope generation job at 00:00 Moscow time
        _scheduler.add_job(
            generate_daily_horoscopes,
            CronTrigger(hour='0', minute=0, timezone="Europe/Moscow"),
            id="generate_daily_horoscopes",
            replace_existing=True,
            misfire_grace_time=3600,  # 1 hour grace
        )

        # Add daily transit forecast generation job at 01:00 Moscow time
        _scheduler.add_job(
            generate_transit_forecasts_for_premium,
            CronTrigger(hour=1, minute=0, timezone="Europe/Moscow"),
            id="generate_transit_forecasts",
            replace_existing=True,
            misfire_grace_time=3600,  # 1 hour grace
        )

    return _scheduler


async def send_daily_horoscope(user_id: int, zodiac_sign: str) -> None:
    """Job function: send horoscope notification to user.

    Sends personalized horoscope for premium users with natal data,
    or general horoscope for others.

    NOTE: Bot instance fetched inside function - cannot serialize Bot in jobstore.
    """
    from src.bot.bot import get_bot
    from src.bot.utils.formatting import format_daily_horoscope
    from src.bot.utils.horoscope import get_mock_horoscope
    from src.bot.utils.zodiac import ZODIAC_SIGNS
    from src.db.engine import AsyncSessionLocal
    from src.db.models.user import User
    from src.services.ai import get_ai_service
    from src.services.astrology.natal_chart import calculate_full_natal_chart
    from sqlalchemy import select

    bot = get_bot()
    zodiac = ZODIAC_SIGNS.get(zodiac_sign)
    if not zodiac:
        await logger.awarning(
            "Unknown zodiac sign for notification", user_id=user_id, sign=zodiac_sign
        )
        return

    # Get user from DB to check premium status
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

    if not user:
        await logger.awarning("User not found for notification", user_id=user_id)
        return

    # Determine horoscope type
    is_premium = False
    forecast_text = None

    if user.is_premium and user.birth_lat and user.birth_lon and user.birth_date:
        # Premium with natal data → personalized horoscope
        is_premium = True

        try:
            natal_data = calculate_full_natal_chart(
                birth_date=user.birth_date,
                birth_time=user.birth_time,
                latitude=user.birth_lat,
                longitude=user.birth_lon,
                timezone_str=user.timezone or "Europe/Moscow",
            )

            ai_service = get_ai_service()
            forecast_text = await ai_service.generate_premium_horoscope(
                user_id=user_id,
                zodiac_sign=zodiac_sign,
                zodiac_sign_ru=zodiac.name_ru,
                date_str=date.today().strftime("%d.%m.%Y"),
                natal_data=natal_data,
            )
        except Exception as e:
            await logger.aerror(
                "Failed to generate premium horoscope, falling back to general",
                user_id=user_id,
                error=str(e),
            )
            # Fallback to general on error
            forecast_text = None

    # Fallback to general horoscope if not premium or generation failed
    if not forecast_text:
        is_premium = False
        raw = get_mock_horoscope(zodiac_sign)

        # Parse general horoscope (remove emoji, split into forecast + tip)
        clean = raw.lstrip()
        if clean and clean[0] in "\u2648\u2649\u264a\u264b\u264c\u264d\u264e\u264f\u2650\u2651\u2652\u2653":
            clean = clean[2:].lstrip()

        sentences = clean.split(". ")
        if len(sentences) > 1:
            forecast_text = ". ".join(sentences[:-1]) + "."
            tip = sentences[-1].rstrip(".") + "."
        else:
            forecast_text = raw
            tip = "Хорошего дня!"
    else:
        # Premium horoscope doesn't have separate tip
        # Use first sentence as tip (or generic)
        sentences = forecast_text.split(". ")
        if len(sentences) > 2:
            tip = sentences[0] + "."
        else:
            tip = "Используй энергию дня себе во благо!"

    # Format message
    content = format_daily_horoscope(
        sign_emoji=zodiac.emoji,
        sign_name_ru=zodiac.name_ru,
        forecast_date=date.today(),
        forecast_text=forecast_text,
        daily_tip=tip,
        is_premium=is_premium,
    )

    try:
        await bot.send_message(chat_id=user_id, **content.as_kwargs())
        horoscope_type = "personalized" if is_premium else "general"
        await logger.ainfo(
            "Sent daily horoscope",
            user_id=user_id,
            sign=zodiac_sign,
            type=horoscope_type,
        )
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


# ============== Subscription Management Jobs ==============


async def check_expiring_subscriptions() -> None:
    """
    Check for subscriptions expiring in 3 days and send notifications.
    Runs daily at 10:00 Moscow time.
    """
    from src.bot.bot import get_bot
    from src.db.engine import async_session_maker
    from src.db.models.subscription import Subscription
    from src.db.models.user import User

    async with async_session_maker() as session:
        # Find subscriptions expiring in 3 days
        now = datetime.now(tz.utc)
        three_days = now + timedelta(days=3)
        four_days = now + timedelta(days=4)

        stmt = (
            select(Subscription, User)
            .join(User, User.id == Subscription.user_id)
            .where(
                and_(
                    Subscription.status.in_(["active", "trial"]),
                    Subscription.current_period_end >= three_days,
                    Subscription.current_period_end < four_days,
                )
            )
        )

        result = await session.execute(stmt)
        expiring = result.all()

        if not expiring:
            return

        bot = get_bot()

        for subscription, user in expiring:
            try:
                end_date = subscription.current_period_end.strftime("%d.%m.%Y")
                await bot.send_message(
                    user.telegram_id,
                    f"Напоминаем: ваша подписка истекает {end_date}.\n\n"
                    "Продлите сейчас, чтобы не потерять премиум-функции!",
                )
                await logger.ainfo(
                    "Sent expiry notification",
                    user_id=user.telegram_id,
                    expires=end_date,
                )
            except Exception as e:
                await logger.aerror(
                    "Failed to send expiry notification",
                    user_id=user.telegram_id,
                    error=str(e),
                )


async def auto_renew_subscriptions() -> None:
    """
    Auto-renew subscriptions expiring in 1 day using saved payment method.
    Runs daily at 09:00 Moscow time (before expiry notification).
    """
    from src.bot.bot import get_bot
    from src.db.engine import async_session_maker
    from src.db.models.subscription import Subscription, SubscriptionStatus
    from src.db.models.user import User
    from src.services.payment import create_recurring_payment
    from src.services.payment.schemas import PLAN_DURATION_DAYS, PLAN_PRICES_STR, PaymentPlan

    async with async_session_maker() as session:
        # Find active subscriptions expiring in 1-2 days with payment_method_id
        now = datetime.now(tz.utc)
        one_day = now + timedelta(days=1)
        two_days = now + timedelta(days=2)

        stmt = (
            select(Subscription, User)
            .join(User, User.id == Subscription.user_id)
            .where(
                and_(
                    Subscription.status == SubscriptionStatus.ACTIVE.value,
                    Subscription.payment_method_id.isnot(None),
                    Subscription.current_period_end >= one_day,
                    Subscription.current_period_end < two_days,
                )
            )
        )

        result = await session.execute(stmt)
        to_renew = result.all()

        if not to_renew:
            return

        bot = get_bot()

        for subscription, user in to_renew:
            try:
                plan = PaymentPlan(subscription.plan)
                amount = PLAN_PRICES_STR[plan]

                # Create recurring payment
                payment = await create_recurring_payment(
                    payment_method_id=subscription.payment_method_id,
                    user_id=user.telegram_id,
                    subscription_id=subscription.id,
                    amount=amount,
                    description="Продление подписки AdtroBot",
                )

                # If payment succeeded immediately (some cards do this)
                if payment.status == "succeeded":
                    # Extend subscription period
                    subscription.current_period_start = subscription.current_period_end
                    subscription.current_period_end = (
                        subscription.current_period_end + timedelta(days=PLAN_DURATION_DAYS[plan])
                    )
                    user.premium_until = subscription.current_period_end
                    await session.commit()

                    await bot.send_message(
                        user.telegram_id,
                        f"Подписка продлена до {subscription.current_period_end.strftime('%d.%m.%Y')}!",
                    )
                    await logger.ainfo(
                        "Auto-renewed subscription",
                        user_id=user.telegram_id,
                        until=subscription.current_period_end.isoformat(),
                    )
                # Otherwise webhook will handle the result

            except Exception as e:
                # Payment failed - mark as past_due
                subscription.status = SubscriptionStatus.PAST_DUE.value
                await session.commit()

                await logger.aerror(
                    "Auto-renewal failed",
                    user_id=user.telegram_id,
                    error=str(e),
                )

                try:
                    await bot.send_message(
                        user.telegram_id,
                        "Не удалось продлить подписку автоматически.\n"
                        "Проверьте карту и оплатите вручную, чтобы сохранить премиум-доступ.",
                    )
                except Exception:
                    pass  # User might have blocked bot


# ============== Horoscope Generation Jobs ==============


async def generate_daily_horoscopes() -> None:
    """
    Background job: generate horoscopes for all 12 zodiac signs.
    Runs daily at 00:00 Moscow time.

    Steps:
    1. Delete old horoscopes (date < today)
    2. Generate horoscopes for all 12 signs via HoroscopeCacheService
    """
    from src.bot.utils.zodiac import ZODIAC_SIGNS
    from src.db.engine import async_session_maker
    from src.db.models.horoscope_cache import HoroscopeCache
    from src.services.horoscope_cache import get_horoscope_cache_service

    today = date.today()

    # FIRST: Delete old horoscopes (explicit cleanup)
    async with async_session_maker() as session:
        await session.execute(
            delete(HoroscopeCache).where(HoroscopeCache.horoscope_date < today)
        )
        await session.commit()
        logger.info("Cleaned up old horoscopes", before_date=str(today))

    # THEN: Generate horoscopes for all 12 signs
    cache_service = get_horoscope_cache_service()

    async with async_session_maker() as session:
        for sign_en, zodiac in ZODIAC_SIGNS.items():
            result = await cache_service.get_horoscope(sign_en, session)
            if result:
                logger.info("Horoscope generated", sign=sign_en)
            else:
                logger.error("Failed to generate horoscope", sign=sign_en)


# ============== Transit Forecast Generation Jobs ==============


async def generate_transit_forecasts_for_premium() -> None:
    """
    Background job: pre-generate transit forecasts for all premium users.
    Runs daily at 01:00 Moscow time (after horoscopes at 00:00).

    Uses asyncio.gather() for PARALLEL generation (much faster than sequential).
    Semaphore limits concurrent API requests to avoid rate limits.

    Steps:
    1. Find all premium users with birth data (birth_lat, birth_lon, birth_date)
    2. Generate ALL forecasts in parallel (with semaphore for rate limiting)
    3. Cache results with 24-hour TTL
    4. Log success/failure for monitoring
    """
    import asyncio

    from src.db.engine import async_session_maker
    from src.db.models.user import User
    from src.services.ai import get_ai_service
    from src.services.astrology.natal_chart import calculate_full_natal_chart

    today = date.today()
    ai_service = get_ai_service()

    # Semaphore to limit concurrent API requests (avoid rate limits)
    # 20 concurrent requests = good balance between speed and API limits
    semaphore = asyncio.Semaphore(20)

    async def generate_for_user(user: User) -> tuple[bool, int]:
        """Generate forecast for a single user (with semaphore)."""
        async with semaphore:
            try:
                # Calculate natal chart
                natal_data = calculate_full_natal_chart(
                    birth_date=user.birth_date,
                    birth_time=user.birth_time,
                    latitude=user.birth_lat,
                    longitude=user.birth_lon,
                    timezone_str=user.timezone or "Europe/Moscow",
                )

                # Generate forecast (will cache automatically)
                _, telegraph_url = await ai_service.generate_daily_transit_forecast(
                    user_id=user.telegram_id,
                    natal_data=natal_data,
                    forecast_date=today,
                    timezone_str=user.timezone or "Europe/Moscow",
                )

                await logger.adebug(
                    "Transit forecast cached",
                    user_id=user.telegram_id,
                    has_telegraph=bool(telegraph_url),
                )
                return (True, user.telegram_id)

            except Exception as e:
                await logger.aerror(
                    "Failed to generate transit forecast",
                    user_id=user.telegram_id,
                    error=str(e),
                )
                return (False, user.telegram_id)

    async with async_session_maker() as session:
        # Find premium users with birth data
        stmt = select(User).where(
            and_(
                User.is_premium.is_(True),
                User.birth_date.isnot(None),
                User.birth_lat.isnot(None),
                User.birth_lon.isnot(None),
            )
        )
        result = await session.execute(stmt)
        users = result.scalars().all()

        await logger.ainfo("Starting transit forecast generation", user_count=len(users))

        # Generate ALL forecasts in parallel (asyncio.gather)
        results = await asyncio.gather(
            *[generate_for_user(user) for user in users],
            return_exceptions=False,
        )

        # Count successes and errors
        success_count = sum(1 for success, _ in results if success)
        error_count = sum(1 for success, _ in results if not success)

        await logger.ainfo(
            "Transit forecast generation complete",
            success=success_count,
            errors=error_count,
        )
