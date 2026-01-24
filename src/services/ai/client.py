"""AI service client for OpenRouter API."""

import time
from datetime import date

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


def _clean_markdown(text: str) -> str:
    """Remove markdown formatting from text.

    Removes: **, ***, *, _, `, ##, ###, ####, [], ||
    Preserves: emoji, newlines, normal text

    Args:
        text: Text potentially containing markdown

    Returns:
        Clean text without markdown symbols
    """
    import re

    # Remove bold (** or ***)
    text = re.sub(r'\*{2,3}([^*]+)\*{2,3}', r'\1', text)

    # Remove italic (single *)
    text = re.sub(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)', r'\1', text)

    # Remove underscores (italic)
    text = re.sub(r'_([^_]+)_', r'\1', text)

    # Remove code blocks (`)
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Remove headers (##, ###, ####)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Remove spoilers (||)
    text = re.sub(r'\|\|([^|]+)\|\|', r'\1', text)

    return text.strip()


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
        # Model for astrologer chat (free on OpenRouter!)
        self.chat_model = "google/gemini-2.0-flash-001"

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

    async def generate_daily_transit_forecast(
        self,
        user_id: int,
        natal_data: dict,
        forecast_date: date,
        timezone_str: str,
    ) -> tuple[str, str | None]:
        """Generate daily transit forecast and publish to Telegraph.

        Args:
            user_id: User ID for caching and cost tracking
            natal_data: User's natal chart (FullNatalChartResult)
            forecast_date: Date to forecast (usually today)
            timezone_str: User's timezone (e.g., "Europe/Moscow")

        Returns:
            Tuple of (forecast_text, telegraph_url)

        Process:
            1. Check cache (key: transit_forecast:{user_id}:{YYYY-MM-DD})
            2. Calculate transits for forecast_date
            3. Generate AI interpretation with DailyTransitPrompt
            4. Publish to Telegraph with title "Транзитный прогноз на {date}"
            5. Cache result for 24 hours
            6. Return text + Telegraph URL
        """
        from src.services.ai.cache import (
            get_cached_transit_forecast,
            set_cached_transit_forecast,
        )
        from src.services.ai.prompts import DailyTransitPrompt
        from src.services.astrology.transits import calculate_daily_transits
        from src.services.telegraph import get_telegraph_service

        # Check cache first
        cached = await get_cached_transit_forecast(user_id, forecast_date)
        if cached:
            logger.debug(
                "transit_forecast_cache_hit",
                user_id=user_id,
                date=str(forecast_date),
            )
            return cached

        # Calculate transits
        transit_data = calculate_daily_transits(
            natal_data=natal_data,
            forecast_date=forecast_date,
            timezone_str=timezone_str,
        )

        # Format date for prompt
        date_str = forecast_date.strftime("%d.%m.%Y")

        # Generate AI forecast
        text = await self._generate(
            system_prompt=DailyTransitPrompt.SYSTEM,
            user_prompt=DailyTransitPrompt.user(
                natal_data=natal_data,
                transit_data=transit_data,
                date_str=date_str,
            ),
            max_tokens=4000,  # For 1500-2500 words
            operation="transit_forecast",
            user_id=user_id,
        )

        if not text:
            return ("", None)  # API error, already logged

        # Publish to Telegraph
        telegraph_url = None
        try:
            import asyncio

            telegraph_service = get_telegraph_service()
            title = f"Транзитный прогноз на {date_str}"

            telegraph_url = await asyncio.wait_for(
                telegraph_service.publish_article(title, text),
                timeout=15.0,  # Longer timeout for long content
            )

            if telegraph_url:
                logger.info(
                    "transit_forecast_published",
                    user_id=user_id,
                    date=str(forecast_date),
                    chars=len(text),
                    url=telegraph_url,
                )
        except Exception as e:
            logger.error(
                "transit_forecast_telegraph_error",
                user_id=user_id,
                error=str(e),
            )

        # Cache result (even if Telegraph failed, cache the text)
        await set_cached_transit_forecast(
            user_id, forecast_date, text, telegraph_url or ""
        )

        logger.info(
            "transit_forecast_generated",
            user_id=user_id,
            date=str(forecast_date),
            chars=len(text),
            has_telegraph=telegraph_url is not None,
        )

        return (text, telegraph_url)

    async def chat_with_astrologer(
        self,
        user_id: int,
        question: str,
        natal_data: dict,
        conversation_history: list[dict],
        transit_data: dict | None = None,
    ) -> str | None:
        """Generate AI astrologer response in conversational mode.

        Uses Gemini 2.0 Flash (free on OpenRouter) with fallback to GPT-4o-mini.

        Args:
            user_id: User ID for cost tracking
            question: User's question about their natal chart
            natal_data: FullNatalChartResult
            conversation_history: Previous messages [{"role": "user"/"assistant", "content": str}, ...]
            transit_data: DailyTransitResult (optional)

        Returns:
            AI response or None if all retries fail
        """
        from src.services.ai.prompts import AstrologerChatPrompt

        # Build system prompt with natal chart
        system_prompt = AstrologerChatPrompt.system_with_chart(
            natal_data=natal_data,
            transit_data=transit_data,
        )

        # Build messages array
        messages = [{"role": "system", "content": system_prompt}]
        # Add conversation history
        messages.extend(conversation_history)
        # Add current question
        messages.append({"role": "user", "content": question})

        # Try Gemini first (free!)
        start_time = time.monotonic()
        try:
            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                max_tokens=500,  # 3-7 sentences
                temperature=0.7,  # Slightly less creative than horoscopes
                extra_headers={
                    "HTTP-Referer": "https://t.me/adtrobot",
                    "X-Title": "AdtroBot - Astrology Chat",
                },
            )
            latency_ms = int((time.monotonic() - start_time) * 1000)

            # Record usage
            try:
                async with AsyncSessionLocal() as session:
                    await record_ai_usage(
                        session=session,
                        user_id=user_id,
                        operation="astrologer_chat",
                        model=self.chat_model,
                        response=response,
                        latency_ms=latency_ms,
                    )
            except Exception as e:
                logger.warning("cost_tracking_failed", error=str(e))

            content = response.choices[0].message.content

            # Clean markdown formatting
            if content:
                content = _clean_markdown(content)

            # Basic validation
            if not content or len(content) < 50:
                logger.warning(
                    "astrologer_response_too_short",
                    user_id=user_id,
                    length=len(content) if content else 0,
                )
                return None

            logger.info(
                "astrologer_chat_response",
                user_id=user_id,
                model=self.chat_model,
                chars=len(content),
                latency_ms=latency_ms,
            )
            return content

        except APIError as e:
            # Gemini failed - try GPT-4o-mini fallback
            logger.warning(
                "astrologer_gemini_failed",
                user_id=user_id,
                error=str(e),
                status_code=getattr(e, "status_code", None),
            )

            # Fallback to GPT-4o-mini
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,  # gpt-4o-mini
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7,
                    extra_headers={
                        "HTTP-Referer": "https://t.me/adtrobot",
                        "X-Title": "AdtroBot - Astrology Chat",
                    },
                )
                latency_ms = int((time.monotonic() - start_time) * 1000)

                # Record usage
                try:
                    async with AsyncSessionLocal() as session:
                        await record_ai_usage(
                            session=session,
                            user_id=user_id,
                            operation="astrologer_chat_fallback",
                            model=self.model,
                            response=response,
                            latency_ms=latency_ms,
                        )
                except Exception as e:
                    logger.warning("cost_tracking_failed", error=str(e))

                content = response.choices[0].message.content

                # Clean markdown formatting
                if content:
                    content = _clean_markdown(content)

                if not content or len(content) < 50:
                    return None

                logger.info(
                    "astrologer_chat_fallback_success",
                    user_id=user_id,
                    model=self.model,
                    chars=len(content),
                )
                return content

            except APIError as fallback_error:
                record_ai_error(
                    "astrologer_chat", self.model, type(fallback_error).__name__
                )
                logger.error(
                    "astrologer_chat_failed",
                    user_id=user_id,
                    error=str(fallback_error),
                )
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
