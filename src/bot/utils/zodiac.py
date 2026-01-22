"""Zodiac sign calculation utilities."""

from dataclasses import dataclass
from datetime import date


@dataclass
class ZodiacSign:
    """Zodiac sign data."""

    name: str  # English name
    name_ru: str  # Russian name
    emoji: str  # Zodiac emoji


# Zodiac signs with Russian names and emoji
ZODIAC_SIGNS: dict[str, ZodiacSign] = {
    "Capricorn": ZodiacSign("Capricorn", "Козерог", "\u2651"),
    "Aquarius": ZodiacSign("Aquarius", "Водолей", "\u2652"),
    "Pisces": ZodiacSign("Pisces", "Рыбы", "\u2653"),
    "Aries": ZodiacSign("Aries", "Овен", "\u2648"),
    "Taurus": ZodiacSign("Taurus", "Телец", "\u2649"),
    "Gemini": ZodiacSign("Gemini", "Близнецы", "\u264a"),
    "Cancer": ZodiacSign("Cancer", "Рак", "\u264b"),
    "Leo": ZodiacSign("Leo", "Лев", "\u264c"),
    "Virgo": ZodiacSign("Virgo", "Дева", "\u264d"),
    "Libra": ZodiacSign("Libra", "Весы", "\u264e"),
    "Scorpio": ZodiacSign("Scorpio", "Скорпион", "\u264f"),
    "Sagittarius": ZodiacSign("Sagittarius", "Стрелец", "\u2650"),
}

# Zodiac date boundaries: (month, day) - start of each sign
# Sign starts on this date (inclusive)
ZODIAC_BOUNDARIES = [
    ((1, 20), "Aquarius"),   # Jan 20 - Feb 18
    ((2, 19), "Pisces"),     # Feb 19 - Mar 20
    ((3, 21), "Aries"),      # Mar 21 - Apr 19
    ((4, 20), "Taurus"),     # Apr 20 - May 20
    ((5, 21), "Gemini"),     # May 21 - Jun 20
    ((6, 21), "Cancer"),     # Jun 21 - Jul 22
    ((7, 23), "Leo"),        # Jul 23 - Aug 22
    ((8, 23), "Virgo"),      # Aug 23 - Sep 22
    ((9, 23), "Libra"),      # Sep 23 - Oct 22
    ((10, 23), "Scorpio"),   # Oct 23 - Nov 21
    ((11, 22), "Sagittarius"),  # Nov 22 - Dec 21
    ((12, 22), "Capricorn"), # Dec 22 - Jan 19
]


def get_zodiac_sign(birth_date: date) -> ZodiacSign:
    """
    Determine zodiac sign from birth date.

    Args:
        birth_date: Date of birth

    Returns:
        ZodiacSign with name, Russian name, and emoji
    """
    month = birth_date.month
    day = birth_date.day

    # Find which sign the date falls into
    # We check if the date is >= start of each sign
    # The last matching boundary is the correct sign
    sign_name = "Capricorn"  # Default for Jan 1-19 and Dec 22-31

    for (boundary_month, boundary_day), name in ZODIAC_BOUNDARIES:
        if (month > boundary_month) or (month == boundary_month and day >= boundary_day):
            sign_name = name

    return ZODIAC_SIGNS[sign_name]
