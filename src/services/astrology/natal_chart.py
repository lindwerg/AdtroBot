"""Natal chart calculation using Swiss Ephemeris.

Calculates Sun, Moon, and Ascendant positions for a given birth date/time/location.
"""

from datetime import date, time
from typing import TypedDict

import structlog
import swisseph as swe

logger = structlog.get_logger()

# Zodiac signs in order (0-11)
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]


class NatalChartResult(TypedDict):
    """Result of natal chart calculation."""
    sun_sign: str
    sun_degree: float
    moon_sign: str
    moon_degree: float
    ascendant: str | None  # None if time unknown
    ascendant_degree: float | None
    time_known: bool


def _get_sign_and_degree(longitude: float) -> tuple[str, float]:
    """Convert ecliptic longitude to sign and degree within sign.

    Args:
        longitude: Ecliptic longitude in degrees (0-360)

    Returns:
        Tuple of (sign_name, degree_within_sign)
    """
    sign_index = int(longitude / 30)
    degree_in_sign = longitude % 30
    return ZODIAC_SIGNS[sign_index], round(degree_in_sign, 1)


def _date_to_julian(
    birth_date: date,
    birth_time: time | None,
) -> float:
    """Convert date/time to Julian Day number.

    Args:
        birth_date: Date of birth
        birth_time: Time of birth (use noon if None)

    Returns:
        Julian Day number in UT
    """
    hour = 12.0  # Default to noon
    if birth_time:
        hour = birth_time.hour + birth_time.minute / 60.0 + birth_time.second / 3600.0

    # swe.julday expects year, month, day, hour (in UT)
    jd = swe.julday(
        birth_date.year,
        birth_date.month,
        birth_date.day,
        hour,
    )
    return jd


def calculate_natal_chart(
    birth_date: date,
    birth_time: time | None,
    latitude: float,
    longitude: float,
) -> NatalChartResult:
    """Calculate natal chart positions for Sun, Moon, and Ascendant.

    Args:
        birth_date: Date of birth
        birth_time: Time of birth (None = unknown, use noon)
        latitude: Birth place latitude (-90 to 90)
        longitude: Birth place longitude (-180 to 180)

    Returns:
        NatalChartResult with sun_sign, moon_sign, ascendant positions
    """
    try:
        # Convert to Julian Day
        jd = _date_to_julian(birth_date, birth_time)

        # Calculate Sun position
        sun_result, _ = swe.calc_ut(jd, swe.SUN)
        sun_lon = sun_result[0]
        sun_sign, sun_degree = _get_sign_and_degree(sun_lon)

        # Calculate Moon position
        moon_result, _ = swe.calc_ut(jd, swe.MOON)
        moon_lon = moon_result[0]
        moon_sign, moon_degree = _get_sign_and_degree(moon_lon)

        # Calculate Ascendant (only meaningful if time is known)
        ascendant = None
        ascendant_degree = None

        if birth_time is not None:
            # swe.houses returns (cusps, ascmc)
            # ascmc[0] is Ascendant, ascmc[1] is MC
            _, ascmc = swe.houses(jd, latitude, longitude, b"P")  # Placidus
            asc_lon = ascmc[0]
            ascendant, ascendant_degree = _get_sign_and_degree(asc_lon)

        result: NatalChartResult = {
            "sun_sign": sun_sign,
            "sun_degree": sun_degree,
            "moon_sign": moon_sign,
            "moon_degree": moon_degree,
            "ascendant": ascendant,
            "ascendant_degree": ascendant_degree,
            "time_known": birth_time is not None,
        }

        logger.debug(
            "natal_chart_calculated",
            birth_date=str(birth_date),
            time_known=birth_time is not None,
            sun=f"{sun_sign} {sun_degree}",
            moon=f"{moon_sign} {moon_degree}",
            asc=f"{ascendant} {ascendant_degree}" if ascendant else "unknown",
        )

        return result

    except Exception as e:
        logger.error(
            "natal_chart_error",
            error=str(e),
            birth_date=str(birth_date),
        )
        # Return a fallback based on birth date (at least sun sign)
        # Simple approximation: March 21 = 0 degrees Aries
        day_of_year = birth_date.timetuple().tm_yday
        # Approximate sun longitude (rough estimate)
        approx_sun_lon = ((day_of_year - 80) % 365) * (360 / 365)
        if approx_sun_lon < 0:
            approx_sun_lon += 360
        sun_sign, sun_degree = _get_sign_and_degree(approx_sun_lon)

        return {
            "sun_sign": sun_sign,
            "sun_degree": sun_degree,
            "moon_sign": "Unknown",
            "moon_degree": 0.0,
            "ascendant": None,
            "ascendant_degree": None,
            "time_known": False,
        }
