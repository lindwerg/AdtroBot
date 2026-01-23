"""Natal chart calculation using Swiss Ephemeris.

Calculates Sun, Moon, and Ascendant positions for a given birth date/time/location.
Full natal chart includes all planets, houses, and aspects.
"""

from datetime import date, datetime, time
from typing import TypedDict

import pytz
import structlog
import swisseph as swe

logger = structlog.get_logger()

# Zodiac signs in order (0-11)
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Russian zodiac sign names
ZODIAC_SIGNS_RU = [
    "Овен", "Телец", "Близнецы", "Рак",
    "Лев", "Дева", "Весы", "Скорпион",
    "Стрелец", "Козерог", "Водолей", "Рыбы"
]

# Planets for full natal chart (11 total)
PLANETS = [
    (swe.SUN, "sun", "Солнце"),
    (swe.MOON, "moon", "Луна"),
    (swe.MERCURY, "mercury", "Меркурий"),
    (swe.VENUS, "venus", "Венера"),
    (swe.MARS, "mars", "Марс"),
    (swe.JUPITER, "jupiter", "Юпитер"),
    (swe.SATURN, "saturn", "Сатурн"),
    (swe.URANUS, "uranus", "Уран"),
    (swe.NEPTUNE, "neptune", "Нептун"),
    (swe.PLUTO, "pluto", "Плутон"),
    (swe.TRUE_NODE, "north_node", "Сев. узел"),
]

# Aspects with orbs (degrees)
ASPECTS = {
    0: ("Conjunction", "Соединение", 8),      # Orb 8 degrees
    60: ("Sextile", "Секстиль", 6),
    90: ("Square", "Квадрат", 8),
    120: ("Trine", "Трин", 8),
    180: ("Opposition", "Оппозиция", 8),
}


class NatalChartResult(TypedDict):
    """Result of natal chart calculation."""
    sun_sign: str
    sun_degree: float
    moon_sign: str
    moon_degree: float
    ascendant: str | None  # None if time unknown
    ascendant_degree: float | None
    time_known: bool


class PlanetPosition(TypedDict):
    """Position of a planet."""
    longitude: float
    sign: str
    sign_ru: str
    degree: float


class HouseCusp(TypedDict):
    """House cusp position."""
    cusp: float
    sign: str
    sign_ru: str


class AnglePosition(TypedDict):
    """Position of an angle (Ascendant, MC)."""
    longitude: float
    sign: str
    sign_ru: str
    degree: float


class AspectData(TypedDict):
    """Aspect between two planets."""
    planet1: str
    planet1_ru: str
    planet2: str
    planet2_ru: str
    aspect: str
    aspect_ru: str
    orb: float


class FullNatalChartResult(TypedDict):
    """Full natal chart with all planets, houses, aspects."""
    planets: dict[str, PlanetPosition]
    houses: dict[int, HouseCusp]
    angles: dict[str, AnglePosition]
    aspects: list[AspectData]
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


def _get_sign_ru(longitude: float) -> str:
    """Get Russian zodiac sign name for longitude."""
    sign_index = int(longitude / 30)
    return ZODIAC_SIGNS_RU[sign_index]


def _get_planet_ru(name: str) -> str:
    """Get Russian planet name."""
    for _, planet_name, planet_ru in PLANETS:
        if planet_name == name:
            return planet_ru
    return name


def _calculate_aspects(planets: dict[str, PlanetPosition]) -> list[AspectData]:
    """Calculate aspects between all planet pairs.

    Args:
        planets: Dict of planet positions

    Returns:
        List of aspects sorted by tightness (smallest orb first)
    """
    aspects: list[AspectData] = []
    planet_names = list(planets.keys())

    for i, p1 in enumerate(planet_names):
        for p2 in planet_names[i + 1:]:
            lon1 = planets[p1]["longitude"]
            lon2 = planets[p2]["longitude"]

            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff

            for angle, (name, name_ru, orb) in ASPECTS.items():
                if abs(diff - angle) <= orb:
                    aspects.append({
                        "planet1": p1,
                        "planet1_ru": _get_planet_ru(p1),
                        "planet2": p2,
                        "planet2_ru": _get_planet_ru(p2),
                        "aspect": name,
                        "aspect_ru": name_ru,
                        "orb": round(abs(diff - angle), 1),
                    })

    # Sort by orb (tightest aspects first)
    aspects.sort(key=lambda a: a["orb"])
    return aspects


def calculate_full_natal_chart(
    birth_date: date,
    birth_time: time | None,
    latitude: float,
    longitude: float,
    timezone_str: str,
) -> FullNatalChartResult:
    """Calculate complete natal chart with all planets, houses, aspects.

    CRITICAL: Converts local birth time to UTC for accurate calculations.

    Args:
        birth_date: Date of birth
        birth_time: Local time of birth (None = use noon UTC)
        latitude: Birth place latitude (-90 to 90)
        longitude: Birth place longitude (-180 to 180)
        timezone_str: Timezone string (e.g., "Europe/Moscow")

    Returns:
        FullNatalChartResult with planets, houses, angles, aspects
    """
    try:
        # Convert local time to UTC
        local_tz = pytz.timezone(timezone_str)

        if birth_time:
            dt = datetime.combine(birth_date, birth_time)
            dt_local = local_tz.localize(dt)
            dt_utc = dt_local.astimezone(pytz.UTC)
            hour_ut = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0

            # Also need to use UTC date
            utc_date = dt_utc.date()
        else:
            # No time known: use noon UTC
            hour_ut = 12.0
            utc_date = birth_date

        # Julian Day in UT
        jd = swe.julday(utc_date.year, utc_date.month, utc_date.day, hour_ut)

        # Calculate all planets
        planets: dict[str, PlanetPosition] = {}
        for planet_id, name, name_ru in PLANETS:
            result, _ = swe.calc_ut(jd, planet_id)
            lon = result[0]
            sign, degree = _get_sign_and_degree(lon)
            planets[name] = {
                "longitude": lon,
                "sign": sign,
                "sign_ru": _get_sign_ru(lon),
                "degree": degree,
            }

        # Calculate houses (Placidus system)
        cusps, ascmc = swe.houses(jd, latitude, longitude, b"P")
        houses: dict[int, HouseCusp] = {}
        for i in range(12):
            cusp_lon = cusps[i]
            houses[i + 1] = {
                "cusp": cusp_lon,
                "sign": _get_sign_and_degree(cusp_lon)[0],
                "sign_ru": _get_sign_ru(cusp_lon),
            }

        # Angles: Ascendant and MC
        asc_lon = ascmc[0]
        mc_lon = ascmc[1]
        asc_sign, asc_degree = _get_sign_and_degree(asc_lon)
        mc_sign, mc_degree = _get_sign_and_degree(mc_lon)

        angles: dict[str, AnglePosition] = {
            "ascendant": {
                "longitude": asc_lon,
                "sign": asc_sign,
                "sign_ru": _get_sign_ru(asc_lon),
                "degree": asc_degree,
            },
            "mc": {
                "longitude": mc_lon,
                "sign": mc_sign,
                "sign_ru": _get_sign_ru(mc_lon),
                "degree": mc_degree,
            },
        }

        # Calculate aspects
        aspects = _calculate_aspects(planets)

        result: FullNatalChartResult = {
            "planets": planets,
            "houses": houses,
            "angles": angles,
            "aspects": aspects,
            "time_known": birth_time is not None,
        }

        logger.debug(
            "full_natal_chart_calculated",
            birth_date=str(birth_date),
            timezone=timezone_str,
            time_known=birth_time is not None,
            planet_count=len(planets),
            aspect_count=len(aspects),
        )

        return result

    except Exception as e:
        logger.error(
            "full_natal_chart_error",
            error=str(e),
            birth_date=str(birth_date),
            timezone=timezone_str,
        )
        raise
