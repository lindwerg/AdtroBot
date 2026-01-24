"""Transit calculations for daily forecasts.

Calculates current planetary positions and their aspects to natal chart.
"""

from datetime import date, datetime, time
from typing import TypedDict

import pytz
import structlog
import swisseph as swe

from src.services.astrology.natal_chart import (
    ASPECTS,
    PLANETS,
    FullNatalChartResult,
    _get_sign_and_degree,
    _get_sign_ru,
)

logger = structlog.get_logger()


class TransitPosition(TypedDict):
    """Position of a transiting planet."""

    longitude: float
    sign: str
    sign_ru: str
    degree: float
    house: int  # Which natal house it's in (0 if unknown)


class TransitAspect(TypedDict):
    """Aspect between transit and natal planet."""

    transit_planet: str
    transit_planet_ru: str
    natal_planet: str
    natal_planet_ru: str
    aspect: str  # Conjunction, Trine, Square, etc.
    aspect_ru: str
    orb: float
    exact: bool  # True if orb < 1 degree


class DailyTransitResult(TypedDict):
    """Daily transit forecast data."""

    date: date
    transits: dict[str, TransitPosition]  # Current planet positions
    aspects: list[TransitAspect]  # Transits aspecting natal planets


def _get_planet_ru(name: str) -> str:
    """Get Russian planet name."""
    for _, planet_name, planet_ru in PLANETS:
        if planet_name == name:
            return planet_ru
    return name


def _determine_natal_house(transit_lon: float, natal_data: FullNatalChartResult) -> int:
    """Determine which natal house a transit falls into.

    Args:
        transit_lon: Transit planet longitude (0-360)
        natal_data: Full natal chart with house cusps

    Returns:
        House number (1-12) or 0 if houses unknown
    """
    if not natal_data["time_known"]:
        return 0  # Houses unknown without birth time

    houses = natal_data["houses"]

    # Check each house (12 houses)
    for house_num in range(1, 13):
        cusp = houses[house_num]["cusp"]

        # Next house cusp (wrap around to house 1 for house 12)
        next_house = (house_num % 12) + 1
        next_cusp = houses[next_house]["cusp"]

        # Handle wrapping at 360/0 degrees
        if next_cusp < cusp:
            # House crosses 0° Aries
            if transit_lon >= cusp or transit_lon < next_cusp:
                return house_num
        else:
            # Normal case
            if cusp <= transit_lon < next_cusp:
                return house_num

    # Fallback (shouldn't happen)
    return 0


def _calculate_transit_aspects(
    transits: dict[str, TransitPosition],
    natal_planets: dict[str, any],
) -> list[TransitAspect]:
    """Calculate aspects between transiting and natal planets.

    Args:
        transits: Current transit positions
        natal_planets: Natal planet positions

    Returns:
        List of transit-natal aspects sorted by orb (tightest first)
    """
    aspects: list[TransitAspect] = []

    for transit_name, transit_pos in transits.items():
        transit_lon = transit_pos["longitude"]
        transit_ru = _get_planet_ru(transit_name)

        for natal_name, natal_pos in natal_planets.items():
            natal_lon = natal_pos["longitude"]
            natal_ru = _get_planet_ru(natal_name)

            # Calculate angle difference
            diff = abs(transit_lon - natal_lon)
            if diff > 180:
                diff = 360 - diff

            # Check for aspects
            for angle, (name, name_ru, orb) in ASPECTS.items():
                if abs(diff - angle) <= orb:
                    aspects.append(
                        {
                            "transit_planet": transit_name,
                            "transit_planet_ru": transit_ru,
                            "natal_planet": natal_name,
                            "natal_planet_ru": natal_ru,
                            "aspect": name,
                            "aspect_ru": name_ru,
                            "orb": round(abs(diff - angle), 1),
                            "exact": abs(diff - angle) < 1.0,
                        }
                    )

    # Sort by orb (tightest aspects first)
    aspects.sort(key=lambda a: a["orb"])
    return aspects


def calculate_daily_transits(
    natal_data: FullNatalChartResult,
    forecast_date: date,
    timezone_str: str,
) -> DailyTransitResult:
    """Calculate transits for a specific date against natal chart.

    Args:
        natal_data: Full natal chart to compare against
        forecast_date: Date to calculate transits for
        timezone_str: Timezone string (e.g., "Europe/Moscow")

    Returns:
        DailyTransitResult with transit positions and aspects

    Process:
        1. Convert forecast_date to noon in user's timezone
        2. Calculate all planet positions for that moment
        3. Determine which natal house each transit falls into
        4. Calculate aspects between transits and natal planets
    """
    try:
        # Convert to noon in user's timezone
        local_tz = pytz.timezone(timezone_str)
        noon_local = datetime.combine(forecast_date, time(12, 0, 0))
        noon_local_tz = local_tz.localize(noon_local)
        noon_utc = noon_local_tz.astimezone(pytz.UTC)

        # Calculate Julian Day in UT
        hour_ut = noon_utc.hour + noon_utc.minute / 60.0 + noon_utc.second / 3600.0
        utc_date = noon_utc.date()
        jd = swe.julday(utc_date.year, utc_date.month, utc_date.day, hour_ut)

        # Calculate all transit positions
        transits: dict[str, TransitPosition] = {}
        for planet_id, name, name_ru in PLANETS:
            result, _ = swe.calc_ut(jd, planet_id)
            lon = result[0]
            sign, degree = _get_sign_and_degree(lon)

            # Determine which natal house this transit is in
            house = _determine_natal_house(lon, natal_data)

            transits[name] = {
                "longitude": lon,
                "sign": sign,
                "sign_ru": _get_sign_ru(lon),
                "degree": degree,
                "house": house,
            }

        # Calculate aspects between transits and natal planets
        aspects = _calculate_transit_aspects(transits, natal_data["planets"])

        result: DailyTransitResult = {
            "date": forecast_date,
            "transits": transits,
            "aspects": aspects,
        }

        logger.debug(
            "daily_transits_calculated",
            date=str(forecast_date),
            timezone=timezone_str,
            transit_count=len(transits),
            aspect_count=len(aspects),
            exact_aspects=sum(1 for a in aspects if a["exact"]),
        )

        return result

    except Exception as e:
        logger.error(
            "daily_transits_error",
            error=str(e),
            date=str(forecast_date),
            timezone=timezone_str,
        )
        raise
