"""Validation for AI-generated outputs."""

import re

from pydantic import BaseModel, ValidationError, field_validator


# Forbidden patterns - AI self-references that should not appear in output
FORBIDDEN_PATTERNS = [
    r"(?i)я\s+(не\s+)?AI",
    r"(?i)как\s+языковая\s+модель",
    r"(?i)я\s+не\s+могу",
    r"(?i)извините,?\s+но",
    r"(?i)as\s+an?\s+AI",
    r"(?i)I\s+am\s+(not\s+)?an?\s+AI",
    r"(?i)language\s+model",
    r"(?i)я\s+искусственный\s+интеллект",
]


def _check_forbidden_patterns(text: str) -> str | None:
    """Check for forbidden AI self-reference patterns.

    Returns error message if found, None otherwise.
    """
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, text):
            return "Обнаружен AI-специфичный текст"
    return None


class HoroscopeOutput(BaseModel):
    """Validation for horoscope output."""

    text: str

    @field_validator("text")
    @classmethod
    def validate_structure(cls, v: str) -> str:
        """Validate horoscope text structure and content."""
        # Check minimum length (300 words ~ 800 chars in Russian)
        if len(v) < 800:
            raise ValueError("Гороскоп слишком короткий")

        # Check maximum length
        if len(v) > 4000:
            raise ValueError("Гороскоп слишком длинный")

        # Check for required sections (flexible matching)
        # At least 3 of 4 section keywords should be present
        required_keywords = ["любовь", "карьер", "здоровь", "финанс"]
        found = sum(1 for kw in required_keywords if kw.lower() in v.lower())
        if found < 3:
            raise ValueError(f"Отсутствуют разделы гороскопа (найдено {found}/4)")

        # Check for forbidden AI self-references
        error = _check_forbidden_patterns(v)
        if error:
            raise ValueError(error)

        return v


class TarotOutput(BaseModel):
    """Validation for tarot interpretation output."""

    text: str

    @field_validator("text")
    @classmethod
    def validate_structure(cls, v: str) -> str:
        """Validate tarot interpretation structure and content."""
        # Check minimum length
        if len(v) < 500:
            raise ValueError("Интерпретация слишком короткая")

        # Check maximum length
        if len(v) > 4000:
            raise ValueError("Интерпретация слишком длинная")

        # Check for position references (at least 2 of 3)
        positions = ["прошл", "настоящ", "будущ"]
        found = sum(1 for pos in positions if pos.lower() in v.lower())
        if found < 2:
            raise ValueError("Отсутствуют позиции расклада")

        # Check for forbidden AI self-references
        error = _check_forbidden_patterns(v)
        if error:
            raise ValueError(error)

        return v


class CardOfDayOutput(BaseModel):
    """Validation for card of day interpretation."""

    text: str

    @field_validator("text")
    @classmethod
    def validate_structure(cls, v: str) -> str:
        """Validate card of day interpretation."""
        # Check minimum length
        if len(v) < 300:
            raise ValueError("Интерпретация слишком короткая")

        # Check maximum length
        if len(v) > 2000:
            raise ValueError("Интерпретация слишком длинная")

        # Check for forbidden AI self-references
        error = _check_forbidden_patterns(v)
        if error:
            raise ValueError(error)

        return v


def validate_horoscope(text: str) -> tuple[bool, str | None]:
    """Validate horoscope output.

    Args:
        text: The generated horoscope text

    Returns:
        Tuple of (is_valid, error_message or None)
    """
    try:
        HoroscopeOutput(text=text)
        return True, None
    except ValidationError as e:
        # Extract the first error message
        errors = e.errors()
        if errors:
            return False, str(errors[0].get("msg", "Validation failed"))
        return False, "Validation failed"


def validate_tarot(text: str) -> tuple[bool, str | None]:
    """Validate tarot spread interpretation output.

    Args:
        text: The generated tarot interpretation text

    Returns:
        Tuple of (is_valid, error_message or None)
    """
    try:
        TarotOutput(text=text)
        return True, None
    except ValidationError as e:
        errors = e.errors()
        if errors:
            return False, str(errors[0].get("msg", "Validation failed"))
        return False, "Validation failed"


def validate_card_of_day(text: str) -> tuple[bool, str | None]:
    """Validate card of day interpretation output.

    Args:
        text: The generated card of day interpretation text

    Returns:
        Tuple of (is_valid, error_message or None)
    """
    try:
        CardOfDayOutput(text=text)
        return True, None
    except ValidationError as e:
        errors = e.errors()
        if errors:
            return False, str(errors[0].get("msg", "Validation failed"))
        return False, "Validation failed"
