"""Simple TTL caching for AI-generated content."""

import time
from datetime import date, datetime
from typing import TypedDict


class CacheEntry(TypedDict):
    """Cache entry with expiration date."""

    text: str
    cached_at: datetime
    expires_date: date  # Expires at end of this date


class CardOfDayCacheEntry(TypedDict):
    """Cache entry for card of day with full data."""

    text: str
    cached_at: datetime
    expires_date: date
    card: dict
    is_reversed: bool


# Simple in-memory caches (sufficient for MVP, clears on restart)
# Key for horoscope: zodiac_sign.lower()
_horoscope_cache: dict[str, CacheEntry] = {}

# Key for card of day: str(user_id)
_card_of_day_cache: dict[str, CardOfDayCacheEntry] = {}

# Premium horoscope cache (by user_id, 1 hour TTL)
_premium_horoscope_cache: dict[int, tuple[str, float]] = {}
PREMIUM_HOROSCOPE_TTL = 3600  # 1 hour

# Natal interpretation cache (by user_id, 24 hour TTL)
# Natal chart is static for a user, so longer cache is appropriate
_natal_interpretation_cache: dict[int, tuple[str, float]] = {}
NATAL_INTERPRETATION_TTL = 86400  # 24 hours

# Transit forecast cache (by "user_id:YYYY-MM-DD", 24 hour TTL)
# Key format: f"{user_id}:{date_str}" where date_str is "YYYY-MM-DD"
# Value: tuple of (forecast_text, telegraph_url, cached_timestamp)
_transit_forecast_cache: dict[str, tuple[str, str, float]] = {}
TRANSIT_FORECAST_TTL = 86400  # 24 hours


def _is_expired(expires_date: date) -> bool:
    """Check if cache entry is expired (new day)."""
    return date.today() > expires_date


async def get_cached_horoscope(zodiac_sign: str) -> str | None:
    """Get cached horoscope for today.

    Args:
        zodiac_sign: English zodiac sign name (e.g., "aries")

    Returns:
        Cached horoscope text or None if not cached/expired
    """
    key = zodiac_sign.lower()
    entry = _horoscope_cache.get(key)

    if entry is None or _is_expired(entry["expires_date"]):
        return None

    return entry["text"]


async def set_cached_horoscope(zodiac_sign: str, text: str) -> None:
    """Cache horoscope until end of day.

    Args:
        zodiac_sign: English zodiac sign name
        text: Generated horoscope text
    """
    key = zodiac_sign.lower()
    _horoscope_cache[key] = {
        "text": text,
        "cached_at": datetime.now(),
        "expires_date": date.today(),
    }


async def get_cached_card_of_day(user_id: int) -> tuple[str, dict, bool] | None:
    """Get cached card of day interpretation for user.

    Args:
        user_id: Telegram user ID

    Returns:
        Tuple of (interpretation_text, card_dict, is_reversed) or None if not cached/expired
    """
    key = str(user_id)
    entry = _card_of_day_cache.get(key)

    if entry is None or _is_expired(entry["expires_date"]):
        return None

    return entry["text"], entry["card"], entry["is_reversed"]


async def set_cached_card_of_day(
    user_id: int,
    interpretation: str,
    card: dict,
    is_reversed: bool,
) -> None:
    """Cache card of day for user until end of day.

    Args:
        user_id: Telegram user ID
        interpretation: Generated interpretation text
        card: Card dictionary
        is_reversed: Whether the card is reversed
    """
    key = str(user_id)
    _card_of_day_cache[key] = {
        "text": interpretation,
        "cached_at": datetime.now(),
        "expires_date": date.today(),
        "card": card,
        "is_reversed": is_reversed,
    }


async def get_cached_premium_horoscope(user_id: int) -> str | None:
    """Get cached premium horoscope for user.

    Args:
        user_id: Telegram user ID

    Returns:
        Cached premium horoscope text or None if not cached/expired
    """
    if user_id in _premium_horoscope_cache:
        text, timestamp = _premium_horoscope_cache[user_id]
        if time.time() - timestamp < PREMIUM_HOROSCOPE_TTL:
            return text
        del _premium_horoscope_cache[user_id]
    return None


async def set_cached_premium_horoscope(user_id: int, text: str) -> None:
    """Cache premium horoscope for user.

    Args:
        user_id: Telegram user ID
        text: Generated premium horoscope text
    """
    _premium_horoscope_cache[user_id] = (text, time.time())


async def get_cached_natal_interpretation(user_id: int) -> str | None:
    """Get cached natal interpretation for user.

    Args:
        user_id: Telegram user ID

    Returns:
        Cached natal interpretation text or None if not cached/expired
    """
    if user_id in _natal_interpretation_cache:
        text, timestamp = _natal_interpretation_cache[user_id]
        if time.time() - timestamp < NATAL_INTERPRETATION_TTL:
            return text
        del _natal_interpretation_cache[user_id]
    return None


async def set_cached_natal_interpretation(user_id: int, text: str) -> None:
    """Cache natal interpretation for user.

    Args:
        user_id: Telegram user ID
        text: Generated natal interpretation text
    """
    _natal_interpretation_cache[user_id] = (text, time.time())


def clear_expired_cache() -> None:
    """Clear expired entries from all caches.

    Can be called by scheduler for cleanup (optional optimization).
    """
    today = date.today()
    now = time.time()

    # Clear expired horoscope entries
    expired_horoscope_keys = [
        k for k, v in _horoscope_cache.items() if v["expires_date"] < today
    ]
    for k in expired_horoscope_keys:
        del _horoscope_cache[k]

    # Clear expired card of day entries
    expired_card_keys = [
        k for k, v in _card_of_day_cache.items() if v["expires_date"] < today
    ]
    for k in expired_card_keys:
        del _card_of_day_cache[k]

    # Clear expired premium horoscope entries (TTL-based)
    expired_premium_keys = [
        k for k, v in _premium_horoscope_cache.items()
        if now - v[1] >= PREMIUM_HOROSCOPE_TTL
    ]
    for k in expired_premium_keys:
        del _premium_horoscope_cache[k]

    # Clear expired natal interpretation entries (TTL-based)
    expired_natal_keys = [
        k for k, v in _natal_interpretation_cache.items()
        if now - v[1] >= NATAL_INTERPRETATION_TTL
    ]
    for k in expired_natal_keys:
        del _natal_interpretation_cache[k]

    # Clear expired transit forecast entries (TTL-based)
    expired_transit_keys = [
        k for k, v in _transit_forecast_cache.items()
        if now - v[2] >= TRANSIT_FORECAST_TTL
    ]
    for k in expired_transit_keys:
        del _transit_forecast_cache[k]


def get_cache_stats() -> dict:
    """Get cache statistics (for debugging/monitoring).

    Returns:
        Dict with cache sizes and today's entries count
    """
    today = date.today()
    now = time.time()
    return {
        "horoscope_total": len(_horoscope_cache),
        "horoscope_today": sum(
            1 for v in _horoscope_cache.values() if v["expires_date"] == today
        ),
        "card_of_day_total": len(_card_of_day_cache),
        "card_of_day_today": sum(
            1 for v in _card_of_day_cache.values() if v["expires_date"] == today
        ),
        "premium_horoscope_total": len(_premium_horoscope_cache),
        "premium_horoscope_active": sum(
            1 for v in _premium_horoscope_cache.values()
            if now - v[1] < PREMIUM_HOROSCOPE_TTL
        ),
        "natal_interpretation_total": len(_natal_interpretation_cache),
        "natal_interpretation_active": sum(
            1 for v in _natal_interpretation_cache.values()
            if now - v[1] < NATAL_INTERPRETATION_TTL
        ),
        "transit_forecast_total": len(_transit_forecast_cache),
        "transit_forecast_active": sum(
            1 for v in _transit_forecast_cache.values()
            if now - v[2] < TRANSIT_FORECAST_TTL
        ),
    }


async def get_cached_transit_forecast(
    user_id: int, forecast_date: date
) -> tuple[str, str] | None:
    """Get cached transit forecast (text, telegraph_url).

    Args:
        user_id: User ID
        forecast_date: Date of forecast

    Returns:
        Tuple of (forecast_text, telegraph_url) or None if not cached/expired
    """
    cache_key = f"{user_id}:{forecast_date.isoformat()}"
    entry = _transit_forecast_cache.get(cache_key)

    if not entry:
        return None

    # Check if expired (24 hours)
    cached_at = entry[2]
    if time.time() - cached_at >= TRANSIT_FORECAST_TTL:
        del _transit_forecast_cache[cache_key]
        return None

    return (entry[0], entry[1])


async def set_cached_transit_forecast(
    user_id: int, forecast_date: date, text: str, telegraph_url: str
) -> None:
    """Cache transit forecast for 24 hours.

    Args:
        user_id: User ID
        forecast_date: Date of forecast
        text: Forecast text
        telegraph_url: Telegraph URL for the forecast
    """
    cache_key = f"{user_id}:{forecast_date.isoformat()}"
    _transit_forecast_cache[cache_key] = (text, telegraph_url, time.time())
