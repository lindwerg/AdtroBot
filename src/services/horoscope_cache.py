"""Horoscope cache service with PostgreSQL persistence and per-key locking."""

import asyncio
from datetime import date

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.utils.zodiac import ZODIAC_SIGNS
from src.db.models.horoscope_cache import HoroscopeCache, HoroscopeView
from src.services.ai.client import get_ai_service

logger = structlog.get_logger()

# Retry backoff times in seconds (5, 10, 30)
RETRY_BACKOFFS = [5, 10, 30]


class HoroscopeCacheService:
    """Service for managing horoscope cache with PostgreSQL persistence.

    Features:
    - Per-key asyncio.Lock prevents duplicate generation for same zodiac sign
    - Reads from PostgreSQL cache
    - Falls back to AI generation with retry on cache miss
    - Tracks view counts per sign per day via UPSERT
    """

    _instance: "HoroscopeCacheService | None" = None

    def __init__(self) -> None:
        """Initialize with fixed locks for 12 zodiac signs."""
        # Fixed dict of 12 locks - no defaultdict to prevent memory leaks
        self._locks: dict[str, asyncio.Lock] = {
            sign: asyncio.Lock() for sign in ZODIAC_SIGNS.keys()
        }

    async def get_horoscope(
        self,
        zodiac_sign: str,
        session: AsyncSession,
    ) -> str | None:
        """Get horoscope from cache or generate on-demand.

        Args:
            zodiac_sign: English zodiac sign name (e.g., "Aries")
            session: Async database session

        Returns:
            Horoscope content or None if all retries fail
        """
        today = date.today()
        sign_lower = zodiac_sign.lower()

        # Acquire lock BEFORE cache check (prevents race condition)
        async with self._locks[zodiac_sign]:
            # Check cache inside lock
            stmt = select(HoroscopeCache).where(
                HoroscopeCache.zodiac_sign == sign_lower,
                HoroscopeCache.horoscope_date == today,
            )
            result = await session.execute(stmt)
            cached = result.scalar_one_or_none()

            if cached:
                logger.info(
                    "horoscope_cache_hit",
                    sign=zodiac_sign,
                    date=today,
                    cached_at=cached.generated_at if hasattr(cached, "generated_at") else None,
                )
                await self._increment_view(session, sign_lower, today)
                return cached.content

            # Cache miss - generate with retry
            logger.info("horoscope_cache_miss", sign=zodiac_sign, date=today)
            zodiac = ZODIAC_SIGNS[zodiac_sign]
            ai_service = get_ai_service()

            for attempt, backoff in enumerate(RETRY_BACKOFFS):
                try:
                    content = await ai_service.generate_horoscope(
                        zodiac_sign,
                        zodiac.name_ru,
                        today.strftime("%d.%m.%Y"),
                    )

                    # Validate content before caching
                    if content and len(content) >= 50:  # Minimum reasonable length
                        try:
                            # Save to cache with proper error handling
                            cache_entry = HoroscopeCache(
                                zodiac_sign=sign_lower,
                                horoscope_date=today,
                                content=content,
                            )
                            session.add(cache_entry)
                            await session.flush()  # Use flush instead of commit

                            # Track view
                            await self._increment_view(session, sign_lower, today)

                            logger.info(
                                "horoscope_generated_and_cached",
                                sign=zodiac_sign,
                                chars=len(content),
                            )
                            return content
                        except Exception as cache_error:
                            logger.error(
                                "horoscope_cache_save_failed",
                                error=str(cache_error),
                                sign=zodiac_sign,
                            )
                            # Continue anyway - return generated content
                            return content

                    logger.warning(
                        "horoscope_generation_invalid",
                        sign=zodiac_sign,
                        attempt=attempt + 1,
                        content_length=len(content) if content else 0,
                    )

                except Exception as e:
                    logger.warning(
                        "horoscope_generation_retry",
                        sign=zodiac_sign,
                        attempt=attempt + 1,
                        backoff_sec=backoff,
                        error=str(e),
                    )

                # Wait before next attempt (unless last attempt)
                if attempt < len(RETRY_BACKOFFS) - 1:
                    await asyncio.sleep(backoff)

            logger.error("horoscope_generation_failed", sign=zodiac_sign)
            return None

    async def _increment_view(
        self,
        session: AsyncSession,
        zodiac_sign: str,
        view_date: date,
    ) -> None:
        """Increment view count via UPSERT.

        Uses PostgreSQL ON CONFLICT DO UPDATE to atomically
        insert or increment view_count.
        """
        stmt = (
            insert(HoroscopeView)
            .values(
                zodiac_sign=zodiac_sign,
                view_date=view_date,
                view_count=1,
            )
            .on_conflict_do_update(
                constraint="uq_horoscope_views_sign_date",
                set_={"view_count": HoroscopeView.view_count + 1},
            )
        )

        await session.execute(stmt)
        await session.commit()


# Singleton getter
_instance: HoroscopeCacheService | None = None


def get_horoscope_cache_service() -> HoroscopeCacheService:
    """Get horoscope cache service singleton.

    Returns:
        HoroscopeCacheService instance
    """
    global _instance
    if _instance is None:
        _instance = HoroscopeCacheService()
    return _instance
