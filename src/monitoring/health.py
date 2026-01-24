"""Health check functions for /health endpoint."""

import asyncio
import time
from dataclasses import dataclass

import httpx
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.monitoring.metrics import HEALTH_CHECK_STATUS

logger = structlog.get_logger()


@dataclass
class HealthCheckResult:
    """Result of a single health check."""

    name: str
    healthy: bool
    message: str | None = None
    latency_ms: float | None = None


async def check_database(session: AsyncSession, timeout: float = 3.0) -> HealthCheckResult:
    """Check database connection with timeout."""
    start = time.monotonic()
    try:
        await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=timeout)
        latency = (time.monotonic() - start) * 1000
        HEALTH_CHECK_STATUS.labels(check="database").set(1)
        return HealthCheckResult("database", True, latency_ms=round(latency, 2))
    except asyncio.TimeoutError:
        HEALTH_CHECK_STATUS.labels(check="database").set(0)
        return HealthCheckResult("database", False, "Timeout")
    except Exception as e:
        HEALTH_CHECK_STATUS.labels(check="database").set(0)
        return HealthCheckResult("database", False, str(e))


async def check_scheduler(timeout: float = 2.0) -> HealthCheckResult:
    """Check APScheduler status."""
    try:
        from src.services.scheduler import get_scheduler

        scheduler = get_scheduler()
        if scheduler.running:
            jobs_count = len(scheduler.get_jobs())
            HEALTH_CHECK_STATUS.labels(check="scheduler").set(1)
            return HealthCheckResult("scheduler", True, f"{jobs_count} jobs scheduled")
        HEALTH_CHECK_STATUS.labels(check="scheduler").set(0)
        return HealthCheckResult("scheduler", False, "Scheduler not running")
    except Exception as e:
        HEALTH_CHECK_STATUS.labels(check="scheduler").set(0)
        return HealthCheckResult("scheduler", False, str(e))


async def check_openrouter(timeout: float = 10.0) -> HealthCheckResult:
    """Check OpenRouter API availability."""
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get("https://openrouter.ai/api/v1/models")
            latency = (time.monotonic() - start) * 1000
            if resp.status_code == 200:
                HEALTH_CHECK_STATUS.labels(check="openrouter").set(1)
                return HealthCheckResult("openrouter", True, latency_ms=round(latency, 2))
            HEALTH_CHECK_STATUS.labels(check="openrouter").set(0)
            return HealthCheckResult("openrouter", False, f"Status {resp.status_code}")
    except Exception as e:
        HEALTH_CHECK_STATUS.labels(check="openrouter").set(0)
        return HealthCheckResult("openrouter", False, str(e))


async def check_telegram_bot(timeout: float = 10.0) -> HealthCheckResult:
    """Check Telegram Bot API connection."""
    start = time.monotonic()
    try:
        from src.bot.bot import get_bot
        from src.config import settings

        if not settings.telegram_bot_token:
            # Token not configured - not an error in dev
            HEALTH_CHECK_STATUS.labels(check="telegram").set(1)
            return HealthCheckResult("telegram", True, "Token not configured (dev mode)")

        bot = get_bot()
        me = await asyncio.wait_for(bot.get_me(), timeout=timeout)
        latency = (time.monotonic() - start) * 1000
        HEALTH_CHECK_STATUS.labels(check="telegram").set(1)
        return HealthCheckResult("telegram", True, f"@{me.username}", latency_ms=round(latency, 2))
    except asyncio.TimeoutError:
        HEALTH_CHECK_STATUS.labels(check="telegram").set(0)
        return HealthCheckResult("telegram", False, "Timeout")
    except Exception as e:
        HEALTH_CHECK_STATUS.labels(check="telegram").set(0)
        return HealthCheckResult("telegram", False, str(e))


async def run_all_checks(session: AsyncSession) -> tuple[bool, list[HealthCheckResult]]:
    """Run all health checks in parallel.

    Returns:
        Tuple of (all_healthy, list of results)
    """
    checks = await asyncio.gather(
        check_database(session, timeout=3.0),
        check_scheduler(timeout=2.0),
        check_openrouter(timeout=10.0),
        check_telegram_bot(timeout=10.0),
    )
    all_healthy = all(c.healthy for c in checks)
    return all_healthy, list(checks)
