# Phase 5: AI Integration - Research

**Researched:** 2026-01-23
**Domain:** AI/LLM интеграция через OpenRouter API (GPT-4o-mini)
**Confidence:** HIGH

## Summary

Phase 5 требует интеграции с **GPT-4o-mini** через OpenRouter API для генерации персонализированных гороскопов и интерпретаций таро. Исследование выявило, что OpenRouter предоставляет OpenAI-совместимый API, позволяя использовать официальный `openai` Python SDK с минимальными изменениями.

**Изменение модели:** Пользователь решил использовать GPT-4o-mini вместо Claude 3.5 Sonnet из-за **50-кратной экономии** ($0.15/$0.60 vs $6/$30 за миллион токенов).

Ключевые решения:
- **Клиент:** `AsyncOpenAI` из `openai` SDK с `base_url="https://openrouter.ai/api/v1"`
- **Модель:** `openai/gpt-4o-mini` (context 128K, max output 16K, input $0.15/M, output $0.60/M)
- **Retry:** Встроенный в openai SDK (max_retries=3) + дополнительный tenacity для validation retry
- **Кеширование:** In-memory dict с TTL для MVP (проще aiocache для простых случаев)
- **Валидация:** Pydantic модели для структурированного вывода + длина/структура проверки

**Primary recommendation:** Использовать `openai` SDK с `AsyncOpenAI(base_url="https://openrouter.ai/api/v1")`, модель `openai/gpt-4o-mini`, встроенный retry SDK, Pydantic для валидации output.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openai | >=1.50.0 | API клиент | OpenRouter рекомендует, OpenAI-совместимый API, полная async поддержка, встроенный retry |
| pydantic | >=2.0 | Валидация output | Уже в проекте (pydantic-settings), type-safe validation |
| tenacity | >=8.2.0 | Дополнительный retry | Для validation retry (когда AI output не проходит проверку) |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | >=0.27.0 | HTTP timeout config | Для granular timeout (connect/read/write) если понадобится |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| openai SDK | aiohttp напрямую | Больше контроля, но нужно самому парсить и обрабатывать формат ответа |
| In-memory dict | aiocache | aiocache тяжелее, для простого TTL cache dict достаточно |
| GPT-4o-mini | GPT-4o | GPT-4o в 17x дороже ($2.50/$10), качество для гороскопов избыточно |
| GPT-4o-mini | GPT-4.1-mini | Новее (2025), но менее протестирован, можно мигрировать позже |

**Installation:**
```bash
poetry add openai tenacity
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── services/
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── client.py         # OpenRouter client wrapper
│   │   ├── prompts.py        # Prompt templates
│   │   ├── validators.py     # Output validation
│   │   └── cache.py          # Simple TTL caching
│   └── scheduler.py          # Existing
├── bot/
│   ├── handlers/
│   │   ├── horoscope.py      # Update to use AI
│   │   └── tarot.py          # Update to use AI
│   └── utils/
│       ├── horoscope.py      # Replace mock with AI service call
│       └── tarot_formatting.py # Update for AI interpretations
```

### Pattern 1: AI Service Layer

**What:** Отдельный сервисный слой для AI-операций, изолирующий API-специфику от бизнес-логики.

**When to use:** Всегда при интеграции с внешними AI API.

**Example:**
```python
# src/services/ai/client.py
# Source: OpenRouter docs + OpenAI SDK docs

from openai import AsyncOpenAI
import structlog

from src.config import settings

logger = structlog.get_logger()


class AIService:
    """AI service for generating horoscopes and tarot interpretations."""

    def __init__(self):
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
    ) -> str:
        """Generate AI response with built-in retry logic."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.8,  # Creativity for horoscopes
            extra_headers={
                "HTTP-Referer": "https://t.me/adtrobot",
                "X-Title": "AdtroBot - Astrology & Tarot",
            },
        )
        return response.choices[0].message.content
```

### Pattern 2: Prompt Templates with Injection Protection

**What:** Структурированные промпты с защитой от injection через четкое разделение system/user частей.

**When to use:** Когда пользовательский input включается в промпт.

**Example:**
```python
# src/services/ai/prompts.py
from dataclasses import dataclass


@dataclass
class HoroscopePrompt:
    """Prompt for daily horoscope generation."""

    SYSTEM = """Ты - опытный астролог, создающий персонализированные гороскопы.
Твоя задача - написать гороскоп на сегодня для указанного знака зодиака.

ФОРМАТ ОТВЕТА (300-500 слов):

[ЛЮБОВЬ]
2-3 предложения о любви и отношениях

[КАРЬЕРА]
2-3 предложения о работе и карьере

[ЗДОРОВЬЕ]
2-3 предложения о здоровье и энергии

[ФИНАНСЫ]
2-3 предложения о деньгах

[СОВЕТ ДНЯ]
1-2 конкретных совета

СТИЛЬ:
- Обращайся на "ты", дружелюбно и тепло
- К знаку: "Дорогой Овен" / "Дорогая Дева" (в зависимости от рода)
- Используй астрологические термины, объясняя простыми словами
- Пиши конкретно, избегай общих фраз типа "все будет хорошо"
- Создавай эффект узнавания себя через детали
- НЕ упоминай, что ты AI или что это сгенерировано"""

    @staticmethod
    def user(zodiac_sign_ru: str, date_str: str) -> str:
        return f"Создай гороскоп на {date_str} для знака: {zodiac_sign_ru}"


@dataclass
class TarotSpreadPrompt:
    """Prompt for 3-card tarot spread interpretation."""

    SYSTEM = """Ты - опытный таролог, интерпретирующий расклады.
Твоя задача - дать глубокую интерпретацию 3-карточного расклада (Прошлое-Настоящее-Будущее).

ВАЖНО:
- Строй интерпретацию ВОКРУГ вопроса пользователя
- НЕ цитируй вопрос дословно
- Связывай все три карты в единое повествование
- Учитывай, перевернута ли карта (меняет значение на противоположное или ослабленное)

ФОРМАТ ОТВЕТА (300-500 слов):

[ПРОШЛОЕ]
Интерпретация первой карты в контексте вопроса

[НАСТОЯЩЕЕ]
Интерпретация второй карты в контексте вопроса

[БУДУЩЕЕ]
Интерпретация третьей карты в контексте вопроса

[ОБЩИЙ ПОСЫЛ]
Связь всех трех карт и рекомендация

СТИЛЬ:
- Обращайся на "ты", эмпатично
- Используй символизм карт
- Пиши конкретно про ситуацию из вопроса
- Создавай ощущение глубины и понимания
- НЕ упоминай, что ты AI"""

    @staticmethod
    def user(question: str, cards: list[dict], is_reversed: list[bool]) -> str:
        # Sanitize question (basic prompt injection protection)
        # Limit length, remove newlines
        clean_question = question[:500].replace("\n", " ").strip()

        cards_text = []
        positions = ["Прошлое", "Настоящее", "Будущее"]
        for i, (card, reversed_flag) in enumerate(zip(cards, is_reversed)):
            status = " (перевернута)" if reversed_flag else ""
            cards_text.append(f"{positions[i]}: {card['name']}{status}")

        return f"""Вопрос пользователя: {clean_question}

Карты расклада:
{chr(10).join(cards_text)}"""


@dataclass
class CardOfDayPrompt:
    """Prompt for Card of the Day interpretation."""

    SYSTEM = """Ты - опытный таролог, интерпретирующий карты.
Твоя задача - дать вдохновляющую интерпретацию Карты Дня.

ФОРМАТ ОТВЕТА (150-250 слов):

[ЗНАЧЕНИЕ КАРТЫ]
Что символизирует эта карта

[ПОСЛАНИЕ ДНЯ]
Что карта говорит тебе на сегодня

[СОВЕТ]
Конкретная рекомендация на день

СТИЛЬ:
- Обращайся на "ты", вдохновляюще
- Используй символизм карты
- Создавай позитивный настрой (даже для сложных карт)
- НЕ упоминай, что ты AI"""

    @staticmethod
    def user(card: dict, is_reversed: bool) -> str:
        status = " (перевернута)" if is_reversed else ""
        card_type = "Старший Аркан" if card["type"] == "major" else "Младший Аркан"
        return f"Карта дня: {card['name']}{status} ({card_type})"
```

### Pattern 3: Output Validation with Pydantic

**What:** Валидация структуры и содержимого AI-ответа перед отправкой пользователю.

**When to use:** Для всех AI-генерируемых ответов.

**Example:**
```python
# src/services/ai/validators.py
from pydantic import BaseModel, field_validator
import re


class HoroscopeOutput(BaseModel):
    """Validation for horoscope output."""
    text: str

    @field_validator("text")
    @classmethod
    def validate_structure(cls, v: str) -> str:
        # Check minimum length (300 words ~ 1500 chars in Russian)
        if len(v) < 800:
            raise ValueError("Гороскоп слишком короткий")

        # Check maximum length
        if len(v) > 4000:
            raise ValueError("Гороскоп слишком длинный")

        # Check for required sections (flexible matching)
        required_keywords = ["любовь", "карьер", "здоровь", "финанс"]
        found = sum(1 for kw in required_keywords if kw.lower() in v.lower())
        if found < 3:  # At least 3 of 4 sections
            raise ValueError(f"Отсутствуют разделы гороскопа (найдено {found}/4)")

        # Filter AI self-references
        forbidden_patterns = [
            r"(?i)я\s+(не\s+)?AI",
            r"(?i)как\s+языковая\s+модель",
            r"(?i)я\s+не\s+могу",
            r"(?i)извините,?\s+но",
            r"(?i)as\s+an?\s+AI",
        ]
        for pattern in forbidden_patterns:
            if re.search(pattern, v):
                raise ValueError("Обнаружен AI-специфичный текст")

        return v


class TarotOutput(BaseModel):
    """Validation for tarot interpretation output."""
    text: str

    @field_validator("text")
    @classmethod
    def validate_structure(cls, v: str) -> str:
        if len(v) < 500:
            raise ValueError("Интерпретация слишком короткая")

        if len(v) > 4000:
            raise ValueError("Интерпретация слишком длинная")

        # Check for position references
        positions = ["прошл", "настоящ", "будущ"]
        found = sum(1 for pos in positions if pos.lower() in v.lower())
        if found < 2:
            raise ValueError("Отсутствуют позиции расклада")

        return v


class CardOfDayOutput(BaseModel):
    """Validation for card of day interpretation."""
    text: str

    @field_validator("text")
    @classmethod
    def validate_structure(cls, v: str) -> str:
        if len(v) < 300:
            raise ValueError("Интерпретация слишком короткая")

        if len(v) > 2000:
            raise ValueError("Интерпретация слишком длинная")

        return v


def validate_horoscope(text: str) -> tuple[bool, str | None]:
    """Validate horoscope output. Returns (is_valid, error_message)."""
    try:
        HoroscopeOutput(text=text)
        return True, None
    except ValueError as e:
        return False, str(e)


def validate_tarot(text: str) -> tuple[bool, str | None]:
    """Validate tarot output. Returns (is_valid, error_message)."""
    try:
        TarotOutput(text=text)
        return True, None
    except ValueError as e:
        return False, str(e)


def validate_card_of_day(text: str) -> tuple[bool, str | None]:
    """Validate card of day output. Returns (is_valid, error_message)."""
    try:
        CardOfDayOutput(text=text)
        return True, None
    except ValueError as e:
        return False, str(e)
```

### Pattern 4: Simple TTL Caching

**What:** Кеширование AI-ответов для экономии токенов и ускорения ответов.

**When to use:** Для ежедневных гороскопов (одинаковые для всех пользователей одного знака), карты дня.

**Example:**
```python
# src/services/ai/cache.py
from datetime import date, datetime
from typing import TypedDict


class CacheEntry(TypedDict):
    text: str
    cached_at: datetime
    expires_date: date  # Expires at end of this date


# Simple in-memory cache (sufficient for MVP, clears on restart)
_horoscope_cache: dict[str, CacheEntry] = {}
_card_of_day_cache: dict[str, CacheEntry] = {}


def _is_expired(entry: CacheEntry) -> bool:
    """Check if cache entry is expired (new day)."""
    return date.today() > entry["expires_date"]


async def get_cached_horoscope(zodiac_sign: str) -> str | None:
    """Get cached horoscope for today."""
    key = zodiac_sign.lower()
    entry = _horoscope_cache.get(key)

    if entry is None or _is_expired(entry):
        return None

    return entry["text"]


async def set_cached_horoscope(zodiac_sign: str, text: str) -> None:
    """Cache horoscope until end of day."""
    key = zodiac_sign.lower()
    _horoscope_cache[key] = {
        "text": text,
        "cached_at": datetime.now(),
        "expires_date": date.today(),
    }


async def get_cached_card_of_day(user_id: int) -> tuple[str, dict, bool] | None:
    """Get cached card of day interpretation for user.

    Returns (interpretation_text, card_dict, is_reversed) or None.
    """
    key = str(user_id)
    entry = _card_of_day_cache.get(key)

    if entry is None or _is_expired(entry):
        return None

    # entry["text"] is JSON-encoded card info + interpretation
    # Implementation detail: store card info in separate field
    return entry.get("full_data")


async def set_cached_card_of_day(
    user_id: int,
    interpretation: str,
    card: dict,
    is_reversed: bool
) -> None:
    """Cache card of day for user until end of day."""
    key = str(user_id)
    _card_of_day_cache[key] = {
        "text": interpretation,
        "cached_at": datetime.now(),
        "expires_date": date.today(),
        "full_data": (interpretation, card, is_reversed),
    }


def clear_expired_cache() -> None:
    """Clear expired entries (can be called by scheduler)."""
    today = date.today()

    for cache in [_horoscope_cache, _card_of_day_cache]:
        expired_keys = [
            k for k, v in cache.items()
            if v["expires_date"] < today
        ]
        for k in expired_keys:
            del cache[k]
```

### Anti-Patterns to Avoid

- **Прямая вставка user input в промпт без санитизации:** Всегда ограничивать длину (500 символов), удалять newlines, использовать отдельный user message
- **Синхронные API вызовы:** Использовать `AsyncOpenAI`, не блокировать event loop
- **Отсутствие timeout:** Всегда устанавливать timeout (рекомендация: 30 секунд для GPT-4o-mini)
- **Retry без backoff:** OpenAI SDK имеет встроенный exponential backoff, использовать его
- **Кеширование без TTL:** Всегда привязывать к дате (expires_date)
- **Игнорирование validation errors:** Retry при провале валидации, затем fallback

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP retry с backoff | Свой retry loop | `openai` SDK built-in (max_retries) | Правильно обрабатывает 429, 5xx, timeouts |
| OpenAI-compatible API client | `aiohttp` + парсинг | `openai` SDK | Типизация, streaming, error handling из коробки |
| Prompt injection защита | Сложные regex фильтры | System/user separation + length limits | Простые фильтры обходятся, proper structure надежнее |
| Token counting | Ручной подсчет | Не нужен для MVP | GPT-4o-mini дешевый, max_tokens ограничивает output |

**Key insight:** OpenRouter полностью совместим с OpenAI SDK - используем его напрямую без изменений кроме base_url и api_key.

## Common Pitfalls

### Pitfall 1: Слишком большой timeout

**What goes wrong:** Пользователь ждет 60+ секунд ответа, уходит.

**Why it happens:** GPT-4o-mini быстрее Claude, не нужен длинный timeout.

**How to avoid:**
- Timeout 30 секунд (GPT-4o-mini обычно отвечает за 5-15 сек)
- max_retries=3 (встроенный в SDK)
- При финальной ошибке - fallback message сразу

**Warning signs:** Медленные ответы бота в логах.

### Pitfall 2: Rate Limit (429) без понимания

**What goes wrong:** При 429 ошибке пользователь видит ошибку.

**Why it happens:** OpenRouter имеет rate limits, особенно для популярных моделей.

**How to avoid:**
- SDK автоматически делает retry с backoff
- max_retries=3 достаточно для большинства случаев
- Мониторить 429 в логах для диагностики

**Warning signs:** Частые 429 ошибки в логах.

### Pitfall 3: Prompt Injection через вопрос пользователя

**What goes wrong:** Пользователь вставляет в вопрос "Ignore previous instructions..." и получает нежелательный ответ.

**Why it happens:** User input помещается в system prompt без разделения.

**How to avoid:**
- System prompt отдельно, user input в user message
- Ограничение длины (500 символов для вопроса)
- Удаление newlines из user input
- Не включать инструкции в user message

**Warning signs:** AI выдает ответы не по теме, отказывается отвечать.

### Pitfall 4: Нет валидации AI output

**What goes wrong:** AI возвращает "Извините, как AI я не могу..." или текст без нужной структуры.

**Why it happens:** AI иногда "ломается" и выдает мета-комментарии или неполные ответы.

**How to avoid:**
- Pydantic валидация структуры
- Проверка длины (min/max)
- Regex фильтр на "AI-специфичные" фразы
- При провале - retry с тем же промптом (до 2 раз)

**Warning signs:** Пользователи жалуются на "странные" ответы бота.

### Pitfall 5: Потеря кеша при деплое

**What goes wrong:** После деплоя все гороскопы генерируются заново, всплеск расходов.

**Why it happens:** In-memory cache очищается при рестарте.

**How to avoid:**
- Для MVP это приемлемо (деплои редкие, GPT-4o-mini дешевый)
- При необходимости - мигрировать на Redis
- Scheduler может pre-warm cache утром

**Warning signs:** Всплески расходов на API после деплоев.

## Code Examples

### Complete AI Service Integration

```python
# src/services/ai/client.py
# Source: OpenRouter docs + OpenAI SDK docs

from openai import AsyncOpenAI, APIError
import structlog

from src.config import settings
from src.services.ai.prompts import HoroscopePrompt, TarotSpreadPrompt, CardOfDayPrompt
from src.services.ai.validators import validate_horoscope, validate_tarot, validate_card_of_day
from src.services.ai.cache import (
    get_cached_horoscope, set_cached_horoscope,
    get_cached_card_of_day, set_cached_card_of_day,
)

logger = structlog.get_logger()


class AIService:
    """AI service for generating horoscopes and tarot interpretations."""

    MAX_VALIDATION_RETRIES = 2

    def __init__(self):
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
        """Generate AI response. Returns None on failure."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.8,
                extra_headers={
                    "HTTP-Referer": "https://t.me/adtrobot",
                    "X-Title": "AdtroBot",
                },
            )
            return response.choices[0].message.content
        except APIError as e:
            logger.error("ai_generation_failed", error=str(e), status_code=getattr(e, 'status_code', None))
            return None

    async def generate_horoscope(self, zodiac_sign: str, zodiac_sign_ru: str, date_str: str) -> str | None:
        """Generate daily horoscope with caching. Returns None if all retries fail."""
        # Check cache first
        cached = await get_cached_horoscope(zodiac_sign)
        if cached:
            logger.debug("horoscope_cache_hit", zodiac=zodiac_sign)
            return cached

        # Generate with validation retry
        for attempt in range(self.MAX_VALIDATION_RETRIES + 1):
            text = await self._generate(
                system_prompt=HoroscopePrompt.SYSTEM,
                user_prompt=HoroscopePrompt.user(zodiac_sign_ru, date_str),
            )

            if text is None:
                return None  # API error, already logged

            is_valid, error = validate_horoscope(text)
            if is_valid:
                await set_cached_horoscope(zodiac_sign, text)
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
        """Generate tarot spread interpretation. Returns None if all retries fail."""
        for attempt in range(self.MAX_VALIDATION_RETRIES + 1):
            text = await self._generate(
                system_prompt=TarotSpreadPrompt.SYSTEM,
                user_prompt=TarotSpreadPrompt.user(question, cards, is_reversed),
            )

            if text is None:
                return None

            is_valid, error = validate_tarot(text)
            if is_valid:
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
        """Generate card of day interpretation with caching."""
        # Check cache first
        cached = await get_cached_card_of_day(user_id)
        if cached:
            logger.debug("card_of_day_cache_hit", user_id=user_id)
            return cached[0]  # Just the interpretation text

        for attempt in range(self.MAX_VALIDATION_RETRIES + 1):
            text = await self._generate(
                system_prompt=CardOfDayPrompt.SYSTEM,
                user_prompt=CardOfDayPrompt.user(card, is_reversed),
                max_tokens=800,  # Shorter response
            )

            if text is None:
                return None

            is_valid, error = validate_card_of_day(text)
            if is_valid:
                await set_cached_card_of_day(user_id, text, card, is_reversed)
                return text

            logger.warning(
                "card_of_day_validation_failed",
                error=error,
                attempt=attempt + 1,
            )

        logger.error("card_of_day_validation_exhausted", user_id=user_id)
        return None


# Singleton instance
_ai_service: AIService | None = None


def get_ai_service() -> AIService:
    """Get AI service singleton."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
```

### Handler Integration Example

```python
# Updated horoscope handler pattern
# Source: Existing project structure

from datetime import date


async def get_horoscope_text(zodiac_sign: str, zodiac_sign_ru: str) -> str:
    """
    Get horoscope text from AI (with caching) or fallback.

    Returns:
        Horoscope text ready for display
    """
    from src.services.ai.client import get_ai_service

    ai = get_ai_service()
    date_str = date.today().strftime("%d.%m.%Y")
    text = await ai.generate_horoscope(zodiac_sign, zodiac_sign_ru, date_str)

    if text:
        return text

    # Fallback: honest message
    return (
        "Сервис временно недоступен. Пожалуйста, попробуй через несколько минут.\n\n"
        "Иногда звезды молчат, чтобы мы прислушались к себе."
    )
```

### Config Extension

```python
# Addition to src/config.py
class Settings(BaseSettings):
    # ... existing fields ...

    # OpenRouter
    openrouter_api_key: str = Field(
        default="",
        validation_alias="OPENROUTER_API_KEY",
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Claude 3.5 Sonnet | GPT-4o-mini | User decision | 50x cost reduction |
| External retry lib | OpenAI SDK built-in | openai SDK 1.x | Simpler code |
| Complex aiocache | Simple dict with TTL | For MVP | Less dependencies |
| 60s timeout | 30s timeout | GPT-4o-mini | Faster user experience |

**Deprecated/outdated:**
- `openai` < 1.0: Старый синхронный API, не используется
- Claude 3.5 Sonnet: Заменен на GPT-4o-mini из-за стоимости

**Available alternatives (deferred):**
- GPT-4.1-mini: Новее (2025), потенциально лучше, можно мигрировать позже
- GPT-4o: В 17x дороже, избыточен для гороскопов

## Open Questions

1. **GPT-4o-mini vs GPT-4.1-mini**
   - What we know: GPT-4.1-mini - новая модель (2025), улучшенное следование инструкциям
   - What's unclear: Стабильность, доступность на OpenRouter
   - Recommendation: Начать с GPT-4o-mini (проверенный), мигрировать при необходимости

2. **Streaming vs non-streaming для Telegram**
   - What we know: Streaming уменьшает TTFB, но Telegram edit_message имеет rate limits
   - What's unclear: Оптимальная стратегия для UX
   - Recommendation: Начать без streaming (проще), GPT-4o-mini достаточно быстр

3. **Pre-warming cache утром**
   - What we know: Можно сгенерировать все 12 гороскопов scheduler'ом в 00:01
   - What's unclear: Нагрузка на API, необходимость
   - Recommendation: Сделать как оптимизацию позже (не блокер для MVP)

## Sources

### Primary (HIGH confidence)
- [OpenRouter GPT-4o-mini](https://openrouter.ai/openai/gpt-4o-mini) - Model specs, pricing ($0.15/$0.60 per M tokens)
- [OpenRouter Quickstart](https://openrouter.ai/docs/quickstart) - API integration patterns
- [OpenRouter Errors](https://openrouter.ai/docs/api/reference/errors-and-debugging) - Error codes (400, 401, 402, 403, 408, 429, 502, 503)
- [OpenAI Python SDK](https://github.com/openai/openai-python) - AsyncOpenAI, timeout, error types, built-in retry

### Secondary (MEDIUM confidence)
- [OpenAI Pricing](https://openai.com/api/pricing/) - GPT-4o-mini pricing verification
- [Tenacity Documentation](https://tenacity.readthedocs.io/) - Retry library (for validation retry)
- [GPT-4o-mini announcement](https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/) - Model capabilities

### Tertiary (LOW confidence)
- WebSearch: Prompt engineering best practices
- WebSearch: AI horoscope generation patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - OpenRouter официально поддерживает OpenAI SDK
- Architecture: HIGH - Паттерны из официальной документации
- Model choice: HIGH - GPT-4o-mini документирован, pricing подтвержден
- Retry/Error handling: HIGH - OpenAI SDK built-in retry документирован
- Prompt templates: MEDIUM - Базируется на best practices, требует итераций
- Validation: MEDIUM - Pydantic стандарт, regex требуют тестирования
- Caching: HIGH - Простая реализация, понятные edge cases

**Research date:** 2026-01-23
**Valid until:** 2026-02-23 (30 days - stable domain, OpenRouter API стабильный)
