"""Simple TTL caching for AI-generated content."""

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


def clear_expired_cache() -> None:
    """Clear expired entries from all caches.

    Can be called by scheduler for cleanup (optional optimization).
    """
    today = date.today()

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


def get_cache_stats() -> dict:
    """Get cache statistics (for debugging/monitoring).

    Returns:
        Dict with cache sizes and today's entries count
    """
    today = date.today()
    return {
        "horoscope_total": len(_horoscope_cache),
        "horoscope_today": sum(
            1 for v in _horoscope_cache.values() if v["expires_date"] == today
        ),
        "card_of_day_total": len(_card_of_day_cache),
        "card_of_day_today": sum(
            1 for v in _card_of_day_cache.values() if v["expires_date"] == today
        ),
    }
