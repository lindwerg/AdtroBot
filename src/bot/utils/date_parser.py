"""Russian date parsing utilities."""

from datetime import date

import dateparser


def parse_russian_date(text: str) -> date | None:
    """
    Parse Russian date string to date object.

    Accepts various formats:
    - "15.03.1990" (DD.MM.YYYY)
    - "15/03/1990" (DD/MM/YYYY)
    - "15-03-1990" (DD-MM-YYYY)
    - "15 марта 1990" (Russian text)
    - "1990-03-15" (ISO format)

    Args:
        text: Date string in any supported format

    Returns:
        date object if parsing successful and date is valid,
        None otherwise
    """
    if not text or not text.strip():
        return None

    result = dateparser.parse(
        text.strip(),
        languages=["ru"],
        settings={
            "DATE_ORDER": "DMY",
            "PREFER_DAY_OF_MONTH": "first",
        },
    )

    if result is None:
        return None

    # Validate year range: reasonable birth years
    # Must be at least 5 years old, born after 1920
    current_year = date.today().year
    if not (1920 <= result.year <= current_year - 5):
        return None

    return result.date()
