"""AI service client for OpenRouter API."""

import structlog
from openai import APIError, AsyncOpenAI

from src.config import settings
from src.services.ai.cache import (
    get_cached_card_of_day,
    get_cached_horoscope,
    get_cached_natal_interpretation,
    get_cached_premium_horoscope,
    set_cached_card_of_day,
    set_cached_horoscope,
    set_cached_natal_interpretation,
    set_cached_premium_horoscope,
)
from src.services.ai.prompts import (
    CardOfDayPrompt,
    CelticCrossPrompt,
    HoroscopePrompt,
    NatalChartPrompt,
    PremiumHoroscopePrompt,
    TarotSpreadPrompt,
)
from src.services.ai.validators import validate_card_of_day, validate_horoscope, validate_tarot

logger = structlog.get_logger()


class AIService:
    """AI service for generating horoscopes and tarot interpretations.

    Uses OpenRouter API with GPT-4o-mini model.
    Features:
    - Built-in retry for API errors (429, 5xx, timeouts)
    - Validation retry for malformed outputs
    - Caching for horoscopes and card of day
    """

    MAX_VALIDATION_RETRIES = 2

    def __init__(self) -> None:
        """Initialize AI service with OpenRouter client."""
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
            timeout=30.0,  # 30 seconds - GPT-4o-mini is fast
            max_retries=3,  # Built-in retry for 429, 5xx, timeouts
        )
        self.model = "openai/gpt-4o-mini"

    async def _generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
    ) -> str | None:
        """Generate AI response.

        Args:
            system_prompt: System instructions for the model
            user_prompt: User message/query
            max_tokens: Maximum tokens in response

        Returns:
            Generated text or None on API error
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.8,  # Creativity for horoscopes/tarot
                extra_headers={
                    "HTTP-Referer": "https://t.me/adtrobot",
                    "X-Title": "AdtroBot - Astrology & Tarot",
                },
            )
            content = response.choices[0].message.content
            return content
        except APIError as e:
            logger.error(
                "ai_generation_failed",
                error=str(e),
                status_code=getattr(e, "status_code", None),
            )
            return None

    async def generate_horoscope(
        self,
        zodiac_sign: str,
        zodiac_sign_ru: str,
        date_str: str,
    ) -> str | None:
        """Generate daily horoscope with caching.

        Args:
            zodiac_sign: English zodiac sign (e.g., "aries")
            zodiac_sign_ru: Russian zodiac sign (e.g., "Овен")
            date_str: Date string (e.g., "23.01.2026")

        Returns:
            Horoscope text or None if all retries fail
        """
        # Check cache first
        cached = await get_cached_horoscope(zodiac_sign)
        if cached:
            logger.debug("horoscope_cache_hit", zodiac=zodiac_sign)
            return cached

        # Generate with validation retry
        for attempt in range(self.MAX_VALIDATION_RETRIES + 1):
            text = await self._generate(
                system_prompt=HoroscopePrompt.SYSTEM,
                user_prompt=HoroscopePrompt.user(
                    zodiac_sign_ru=zodiac_sign_ru,
                    date_str=date_str,
                    zodiac_sign_en=zodiac_sign,
                ),
            )

            if text is None:
                return None  # API error, already logged

            is_valid, error = validate_horoscope(text)
            if is_valid:
                await set_cached_horoscope(zodiac_sign, text)
                logger.info(
                    "horoscope_generated",
                    zodiac=zodiac_sign,
                    chars=len(text),
                )
                return text

            logger.warning(
                "horoscope_validation_failed",
                error=error,
                attempt=attempt + 1,
                zodiac=zodiac_sign,
            )

        logger.error("horoscope_validation_exhausted", zodiac=zodiac_sign)
        return None

    async def generate_tarot_interpretation(
        self,
        question: str,
        cards: list[dict],
        is_reversed: list[bool],
    ) -> str | None:
        """Generate tarot spread interpretation.

        No caching - each spread is unique based on question.

        Args:
            question: User's question
            cards: List of 3 card dictionaries
            is_reversed: List of 3 booleans for reversed cards

        Returns:
            Interpretation text or None if all retries fail
        """
        for attempt in range(self.MAX_VALIDATION_RETRIES + 1):
            text = await self._generate(
                system_prompt=TarotSpreadPrompt.SYSTEM,
                user_prompt=TarotSpreadPrompt.user(question, cards, is_reversed),
            )

            if text is None:
                return None

            is_valid, error = validate_tarot(text)
            if is_valid:
                logger.info(
                    "tarot_interpretation_generated",
                    cards=[c.get("name") for c in cards],
                    chars=len(text),
                )
                return text

            logger.warning(
                "tarot_validation_failed",
                error=error,
                attempt=attempt + 1,
            )

        logger.error("tarot_validation_exhausted")
        return None

    async def generate_card_of_day(
        self,
        user_id: int,
        card: dict,
        is_reversed: bool,
    ) -> str | None:
        """Generate card of day interpretation with caching.

        Args:
            user_id: Telegram user ID
            card: Card dictionary
            is_reversed: Whether the card is reversed

        Returns:
            Interpretation text or None if all retries fail
        """
        # Check cache first
        cached = await get_cached_card_of_day(user_id)
        if cached:
            logger.debug("card_of_day_cache_hit", user_id=user_id)
            return cached[0]  # Just the interpretation text

        for attempt in range(self.MAX_VALIDATION_RETRIES + 1):
            text = await self._generate(
                system_prompt=CardOfDayPrompt.SYSTEM,
                user_prompt=CardOfDayPrompt.user(card, is_reversed),
                max_tokens=800,  # Shorter response for card of day
            )

            if text is None:
                return None

            is_valid, error = validate_card_of_day(text)
            if is_valid:
                await set_cached_card_of_day(user_id, text, card, is_reversed)
                logger.info(
                    "card_of_day_generated",
                    user_id=user_id,
                    card=card.get("name"),
                    reversed=is_reversed,
                    chars=len(text),
                )
                return text

            logger.warning(
                "card_of_day_validation_failed",
                error=error,
                attempt=attempt + 1,
            )

        logger.error("card_of_day_validation_exhausted", user_id=user_id)
        return None

    async def generate_premium_horoscope(
        self,
        user_id: int,
        zodiac_sign: str,
        zodiac_sign_ru: str,
        date_str: str,
        natal_data: dict,
    ) -> str | None:
        """Generate premium personalized horoscope with natal chart.

        Args:
            user_id: Telegram user ID (for caching)
            zodiac_sign: English zodiac sign (e.g., "aries")
            zodiac_sign_ru: Russian zodiac sign (e.g., "Овен")
            date_str: Date string (e.g., "23.01.2026")
            natal_data: Dict from calculate_natal_chart()

        Returns:
            Premium horoscope text or None if all retries fail
        """
        # Check cache first
        cached = await get_cached_premium_horoscope(user_id)
        if cached:
            logger.debug("premium_horoscope_cache_hit", user_id=user_id)
            return cached

        # Generate with validation retry
        for attempt in range(self.MAX_VALIDATION_RETRIES + 1):
            text = await self._generate(
                system_prompt=PremiumHoroscopePrompt.SYSTEM,
                user_prompt=PremiumHoroscopePrompt.user(
                    zodiac_sign_ru=zodiac_sign_ru,
                    date_str=date_str,
                    natal_data=natal_data,
                    zodiac_sign_en=zodiac_sign,
                ),
                max_tokens=2000,  # Longer for premium
            )

            if text is None:
                return None  # API error, already logged

            is_valid, error = validate_horoscope(text)
            if is_valid:
                await set_cached_premium_horoscope(user_id, text)
                logger.info(
                    "premium_horoscope_generated",
                    user_id=user_id,
                    zodiac=zodiac_sign,
                    chars=len(text),
                )
                return text

            logger.warning(
                "premium_horoscope_validation_failed",
                error=error,
                attempt=attempt + 1,
                user_id=user_id,
            )

        logger.error("premium_horoscope_validation_exhausted", user_id=user_id)
        return None

    async def generate_celtic_cross(
        self,
        question: str,
        cards: list[dict],
        is_reversed: list[bool],
    ) -> str | None:
        """Generate Celtic Cross 10-card spread interpretation.

        No caching - each spread is unique based on question.

        Args:
            question: User's question
            cards: List of 10 card dictionaries
            is_reversed: List of 10 booleans for reversed cards

        Returns:
            Interpretation text (800-1200 words) or None if all retries fail
        """
        for attempt in range(self.MAX_VALIDATION_RETRIES + 1):
            text = await self._generate(
                system_prompt=CelticCrossPrompt.SYSTEM,
                user_prompt=CelticCrossPrompt.user(question, cards, is_reversed),
                max_tokens=4000,  # Larger for 800-1200 word response
            )

            if text is None:
                return None

            is_valid, error = validate_tarot(text)
            if is_valid:
                logger.info(
                    "celtic_cross_generated",
                    cards=[c.get("name") for c in cards],
                    chars=len(text),
                )
                return text

            logger.warning(
                "celtic_cross_validation_failed",
                error=error,
                attempt=attempt + 1,
            )

        logger.error("celtic_cross_validation_exhausted")
        return None

    async def generate_natal_interpretation(
        self,
        user_id: int,
        natal_data: dict,
    ) -> str | None:
        """Generate full natal chart interpretation (1000-1500 words).

        Uses 24-hour cache since natal chart doesn't change.

        Args:
            user_id: Telegram user ID (for caching)
            natal_data: FullNatalChartResult from calculate_full_natal_chart()

        Returns:
            Natal interpretation text or None if all retries fail
        """
        # Check cache first (24 hour TTL)
        cached = await get_cached_natal_interpretation(user_id)
        if cached:
            logger.debug("natal_interpretation_cache_hit", user_id=user_id)
            return cached

        # Generate with validation retry
        for attempt in range(self.MAX_VALIDATION_RETRIES + 1):
            text = await self._generate(
                system_prompt=NatalChartPrompt.SYSTEM,
                user_prompt=NatalChartPrompt.user(natal_data),
                max_tokens=4000,  # 1000-1500 words needs more tokens
            )

            if text is None:
                return None  # API error, already logged

            # Use horoscope validation (length + no AI self-reference)
            is_valid, error = validate_horoscope(text)
            if is_valid:
                await set_cached_natal_interpretation(user_id, text)
                logger.info(
                    "natal_interpretation_generated",
                    user_id=user_id,
                    chars=len(text),
                )
                return text

            logger.warning(
                "natal_interpretation_validation_failed",
                error=error,
                attempt=attempt + 1,
                user_id=user_id,
            )

        logger.error("natal_interpretation_validation_exhausted", user_id=user_id)
        return None


# Singleton instance
_ai_service: AIService | None = None


def get_ai_service() -> AIService:
    """Get AI service singleton.

    Returns:
        AIService instance
    """
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
