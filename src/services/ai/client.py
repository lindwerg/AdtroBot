"""AI service client for OpenRouter API."""

import time

import structlog
from openai import APIError, AsyncOpenAI

from src.db.engine import AsyncSessionLocal
from src.monitoring.cost_tracking import record_ai_error, record_ai_usage

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
    DetailedNatalPrompt,
    GeneralHoroscopePrompt,
    HoroscopePrompt,
    NatalChartPrompt,
    PremiumHoroscopePrompt,
    TarotSpreadPrompt,
)
from src.services.ai.validators import (
    validate_card_of_day,
    validate_detailed_natal_section,
    validate_general_horoscope,
    validate_horoscope,
    validate_natal_chart,
    validate_tarot,
)

logger = structlog.get_logger()

# Cache for detailed natal interpretations (7 days)
_detailed_natal_cache: dict[int, tuple[str, float]] = {}
DETAILED_NATAL_CACHE_TTL = 604800  # 7 days


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
        operation: str = "unknown",
        user_id: int | None = None,
    ) -> str | None:
        """Generate AI response with usage tracking.

        Args:
            system_prompt: System instructions for the model
            user_prompt: User message/query
            max_tokens: Maximum tokens in response
            operation: Operation type for cost tracking
            user_id: User ID for cost attribution

        Returns:
            Generated text or None on API error
        """
        start_time = time.monotonic()
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
            latency_ms = int((time.monotonic() - start_time) * 1000)

            # Record usage asynchronously (don't block response)
            try:
                async with AsyncSessionLocal() as session:
                    await record_ai_usage(
                        session=session,
                        user_id=user_id,
                        operation=operation,
                        model=self.model,
                        response=response,
                        latency_ms=latency_ms,
                    )
            except Exception as e:
                logger.warning("cost_tracking_failed", error=str(e))

            content = response.choices[0].message.content
            return content
        except APIError as e:
            record_ai_error(operation, self.model, type(e).__name__)
            logger.error(
                "ai_generation_failed",
                error=str(e),
                status_code=getattr(e, "status_code", None),
                operation=operation,
            )
            return None

    async def generate_horoscope(
        self,
        zodiac_sign: str,
        zodiac_sign_ru: str,
        date_str: str,
        user_id: int | None = None,
    ) -> str | None:
        """Generate daily horoscope with caching.

        Args:
            zodiac_sign: English zodiac sign (e.g., "aries")
            zodiac_sign_ru: Russian zodiac sign (e.g., "Овен")
            date_str: Date string (e.g., "23.01.2026")
            user_id: User ID for cost tracking (None for scheduled generation)

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
                operation="horoscope",
                user_id=user_id,
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

    async def generate_general_horoscope(
        self,
        zodiac_sign: str,
        zodiac_sign_ru: str,
        date_str: str,
        user_id: int | None = None,
    ) -> str | None:
        """Generate general horoscope without sections for onboarding.

        Used for onboarding to show users the difference between general and premium horoscopes.
        NO CACHING - one-time operation per user.

        Args:
            zodiac_sign: English zodiac sign (e.g., "aries")
            zodiac_sign_ru: Russian zodiac sign (e.g., "Овен")
            date_str: Date string (e.g., "23.01.2026")
            user_id: User ID for cost tracking

        Returns:
            General horoscope text or None if all retries fail
        """
        # Generate with validation retry
        for attempt in range(self.MAX_VALIDATION_RETRIES + 1):
            text = await self._generate(
                system_prompt=GeneralHoroscopePrompt.SYSTEM,
                user_prompt=GeneralHoroscopePrompt.user(
                    zodiac_sign_ru=zodiac_sign_ru,
                    date_str=date_str,
                    zodiac_sign_en=zodiac_sign,
                ),
                max_tokens=1000,
                operation="general_horoscope",
                user_id=user_id,
            )

            if text is None:
                return None  # API error, already logged

            is_valid, error = validate_general_horoscope(text)
            if is_valid:
                logger.info(
                    "general_horoscope_generated",
                    zodiac=zodiac_sign,
                    chars=len(text),
                )
                return text

            logger.warning(
                "general_horoscope_validation_failed",
                error=error,
                attempt=attempt + 1,
                zodiac=zodiac_sign,
            )

        logger.error("general_horoscope_validation_exhausted", zodiac=zodiac_sign)
        return None

    async def generate_tarot_interpretation(
        self,
        question: str,
        cards: list[dict],
        is_reversed: list[bool],
        user_id: int | None = None,
    ) -> str | None:
        """Generate tarot spread interpretation.

        No caching - each spread is unique based on question.

        Args:
            question: User's question
            cards: List of 3 card dictionaries
            is_reversed: List of 3 booleans for reversed cards
            user_id: User ID for cost tracking

        Returns:
            Interpretation text or None if all retries fail
        """
        for attempt in range(self.MAX_VALIDATION_RETRIES + 1):
            text = await self._generate(
                system_prompt=TarotSpreadPrompt.SYSTEM,
                user_prompt=TarotSpreadPrompt.user(question, cards, is_reversed),
                operation="tarot",
                user_id=user_id,
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
            user_id: Telegram user ID (also used for cost tracking)
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
                operation="card_of_day",
                user_id=user_id,
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
            user_id: Telegram user ID (for caching and cost tracking)
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
                operation="premium_horoscope",
                user_id=user_id,
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
        user_id: int | None = None,
    ) -> str | None:
        """Generate Celtic Cross 10-card spread interpretation.

        No caching - each spread is unique based on question.

        Args:
            question: User's question
            cards: List of 10 card dictionaries
            is_reversed: List of 10 booleans for reversed cards
            user_id: User ID for cost tracking

        Returns:
            Interpretation text (800-1200 words) or None if all retries fail
        """
        for attempt in range(self.MAX_VALIDATION_RETRIES + 1):
            text = await self._generate(
                system_prompt=CelticCrossPrompt.SYSTEM,
                user_prompt=CelticCrossPrompt.user(question, cards, is_reversed),
                max_tokens=4000,  # Larger for 800-1200 word response
                operation="celtic_cross",
                user_id=user_id,
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
            user_id: Telegram user ID (for caching and cost tracking)
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
                max_tokens=1500,  # 400-500 words - reduced
                operation="natal_interpretation",
                user_id=user_id,
            )

            if text is None:
                return None  # API error, already logged

            # Use natal chart validation (checks correct sections)
            is_valid, error = validate_natal_chart(text)
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

    async def generate_detailed_natal_interpretation(
        self,
        user_id: int,
        natal_data: dict,
    ) -> str | None:
        """Generate detailed natal chart interpretation (3000-5000 words).

        Uses sectioned generation for reliable long-form output.
        Caches result for 7 days.

        Args:
            user_id: User ID for caching and cost tracking
            natal_data: FullNatalChartResult dict

        Returns:
            Full interpretation text or None on failure
        """
        import time as time_module

        # Check cache
        if user_id in _detailed_natal_cache:
            cached_text, cached_time = _detailed_natal_cache[user_id]
            if time_module.time() - cached_time < DETAILED_NATAL_CACHE_TTL:
                logger.info("detailed_natal_cache_hit", user_id=user_id)
                return cached_text

        logger.info("generating_detailed_natal", user_id=user_id)

        sections_text = []

        for section in DetailedNatalPrompt.SECTIONS:
            section_prompt = DetailedNatalPrompt.section_prompt(section, natal_data)

            # Generate section with higher max_tokens
            max_tokens = max(1500, section["min_words"] * 3)  # ~3 tokens per word

            response = None
            for attempt in range(3):  # Retry up to 3 times
                try:
                    response = await self._generate(
                        system_prompt=DetailedNatalPrompt.SYSTEM,
                        user_prompt=section_prompt,
                        max_tokens=max_tokens,
                        operation="detailed_natal",
                        user_id=user_id,
                    )

                    if response and validate_detailed_natal_section(response, section["min_words"]):
                        sections_text.append(f"## {section['title']}\n\n{response}")
                        break
                    else:
                        logger.warning(
                            "detailed_natal_section_short",
                            section=section["id"],
                            attempt=attempt + 1,
                            length=len(response) if response else 0,
                        )
                except Exception as e:
                    logger.error(
                        "detailed_natal_section_error",
                        section=section["id"],
                        error=str(e),
                    )

                if attempt == 2:
                    # Use whatever we got on last attempt
                    if response:
                        sections_text.append(f"## {section['title']}\n\n{response}")
                    else:
                        logger.error("detailed_natal_section_failed", section=section["id"])

        if not sections_text:
            return None

        full_text = "\n\n".join(sections_text)

        # Cache result
        _detailed_natal_cache[user_id] = (full_text, time_module.time())
        logger.info(
            "detailed_natal_generated",
            user_id=user_id,
            total_chars=len(full_text),
            sections=len(sections_text),
        )

        return full_text


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
