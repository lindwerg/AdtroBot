# Phase 5: AI Integration - Research

**Researched:** 2026-01-22
**Domain:** AI/LLM интеграция через OpenRouter API
**Confidence:** HIGH

## Summary

Phase 5 требует интеграции с Claude 3.5 Sonnet через OpenRouter API для генерации персонализированных гороскопов и интерпретаций таро. Исследование выявило, что OpenRouter предоставляет OpenAI-совместимый API, что позволяет использовать официальный `openai` Python SDK с минимальными изменениями.

Ключевые решения:
- **Клиент:** `AsyncOpenAI` из `openai` SDK с `base_url="https://openrouter.ai/api/v1"`
- **Модель:** `anthropic/claude-3.5-sonnet` (context window 200K, input $6/M, output $30/M tokens)
- **Retry:** `tenacity` с exponential backoff + jitter для 429/5xx ошибок
- **Кеширование:** In-memory (SimpleMemoryCache) для MVP, Redis для production при необходимости
- **Валидация:** Pydantic модели для структурированного вывода + длина/структура проверки

**Primary recommendation:** Использовать `openai` SDK с `AsyncOpenAI(base_url="https://openrouter.ai/api/v1")`, `tenacity` для retry-логики, Pydantic для валидации output.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openai | >=1.50.0 | API клиент | OpenRouter рекомендует, OpenAI-совместимый API, полная async поддержка |
| tenacity | >=8.2.0 | Retry логика | De facto стандарт для Python retry, поддерживает async, exponential backoff с jitter |
| pydantic | >=2.0 | Валидация output | Уже в проекте (pydantic-settings), type-safe validation |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| aiocache | >=0.12.0 | Async кеширование | Кеширование AI ответов (гороскопы на день) |
| httpx | >=0.27.0 | HTTP timeout config | Если нужен granular timeout control (connect/read/write) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| openai SDK | aiohttp напрямую | Больше контроля, но нужно самому парсить SSE и обрабатывать формат ответа |
| tenacity | stamina | Новее, но tenacity более mature и документирован |
| aiocache | Redis напрямую | Redis требует отдельный сервис, для MVP in-memory достаточно |

**Installation:**
```bash
poetry add openai tenacity aiocache
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
│   │   └── cache.py          # Caching layer
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
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type
from openai import RateLimitError, APITimeoutError, APIConnectionError

class AIClient:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            timeout=60.0,  # 60 seconds timeout
        )

    @retry(
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError)),
        wait=wait_random_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
    )
    async def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 1000) -> str:
        response = await self.client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            extra_headers={
                "HTTP-Referer": "https://t.me/adtrobot",
                "X-Title": "AdtroBot",
            },
        )
        return response.choices[0].message.content
```

### Pattern 2: Prompt Templates with Injection Protection

**What:** Структурированные промпты с защитой от injection через чёткое разделение system/user частей.

**When to use:** Когда пользовательский input включается в промпт.

**Example:**
```python
# src/services/ai/prompts.py
from dataclasses import dataclass

@dataclass
class HoroscopePrompt:
    """Промпт для генерации ежедневного гороскопа."""

    SYSTEM = """Ты — опытный астролог, создающий персонализированные гороскопы.
Твоя задача — написать гороскоп на сегодня для указанного знака зодиака.

ФОРМАТ ОТВЕТА:
Напиши гороскоп в следующей структуре (300-500 слов):

[ЛЮБОВЬ]
2-3 предложения о любви и отношениях

[КАРЬЕРА]
2-3 предложения о работе и карьере

[ЗДОРОВЬЕ]
2-3 предложения о здоровье и энергии

[ФИНАНСЫ]
2-3 предложения о деньгах и материальном благополучии

[СОВЕТ ДНЯ]
1-2 конкретных совета на сегодня

СТИЛЬ:
- Обращайся на «ты», дружелюбно и тепло
- К знаку обращайся: «Дорогой Овен» / «Дорогая Дева» и т.д.
- Используй астрологические термины, но объясняй простыми словами
- Пиши конкретно, избегай общих фраз
- Создавай эффект «узнавания себя» через детали
- Никогда не упоминай, что ты AI или что это сгенерировано"""

    @staticmethod
    def user(zodiac_sign_ru: str, date_str: str) -> str:
        return f"Создай гороскоп на {date_str} для знака: {zodiac_sign_ru}"


@dataclass
class TarotSpreadPrompt:
    """Промпт для интерпретации 3-карточного расклада таро."""

    SYSTEM = """Ты — опытный таролог, интерпретирующий расклады.
Твоя задача — дать глубокую интерпретацию 3-карточного расклада (Прошлое-Настоящее-Будущее).

ВАЖНО:
- Строй интерпретацию ВОКРУГ вопроса пользователя
- НЕ цитируй вопрос дословно
- Связывай все три карты в единое повествование
- Учитывай, перевёрнута ли карта (меняет значение)

ФОРМАТ ОТВЕТА:
Напиши интерпретацию (300-500 слов):

[ПРОШЛОЕ]
Интерпретация первой карты в контексте вопроса

[НАСТОЯЩЕЕ]
Интерпретация второй карты в контексте вопроса

[БУДУЩЕЕ]
Интерпретация третьей карты в контексте вопроса

[ОБЩИЙ ПОСЫЛ]
Связь всех трёх карт и рекомендация

СТИЛЬ:
- Обращайся на «ты», эмпатично
- Используй символизм карт
- Пиши конкретно про ситуацию из вопроса
- Создавай ощущение глубины и понимания
- Никогда не упоминай, что ты AI"""

    @staticmethod
    def user(question: str, cards: list[dict], is_reversed: list[bool]) -> str:
        # Sanitize question (basic prompt injection protection)
        clean_question = question[:500].replace("\n", " ").strip()

        cards_text = []
        positions = ["Прошлое", "Настоящее", "Будущее"]
        for i, (card, reversed_flag) in enumerate(zip(cards, is_reversed)):
            status = " (перевёрнута)" if reversed_flag else ""
            cards_text.append(f"{positions[i]}: {card['name']}{status}")

        return f"""Вопрос пользователя: {clean_question}

Карты расклада:
{chr(10).join(cards_text)}"""
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
    """Валидация гороскопа."""
    text: str

    @field_validator("text")
    @classmethod
    def validate_structure(cls, v: str) -> str:
        # Проверка минимальной длины
        if len(v) < 200:
            raise ValueError("Гороскоп слишком короткий")

        # Проверка максимальной длины
        if len(v) > 3000:
            raise ValueError("Гороскоп слишком длинный")

        # Проверка наличия разделов
        required_sections = ["ЛЮБОВЬ", "КАРЬЕРА", "ЗДОРОВЬЕ", "ФИНАНСЫ"]
        for section in required_sections:
            if f"[{section}]" not in v and section.lower() not in v.lower():
                raise ValueError(f"Отсутствует раздел: {section}")

        # Фильтр неуместного контента
        forbidden_patterns = [
            r"(?i)я\s+(не\s+)?AI",
            r"(?i)как\s+языковая\s+модель",
            r"(?i)я\s+не\s+могу",
            r"(?i)извините,?\s+но",
        ]
        for pattern in forbidden_patterns:
            if re.search(pattern, v):
                raise ValueError("Обнаружен AI-специфичный текст")

        return v

def validate_horoscope(text: str) -> tuple[bool, str | None]:
    """Validate horoscope output. Returns (is_valid, error_message)."""
    try:
        HoroscopeOutput(text=text)
        return True, None
    except ValueError as e:
        return False, str(e)
```

### Pattern 4: Caching with TTL

**What:** Кеширование AI-ответов для экономии токенов и ускорения ответов.

**When to use:** Для ежедневных гороскопов (одинаковые для всех пользователей одного знака), карты дня.

**Example:**
```python
# src/services/ai/cache.py
from aiocache import Cache
from aiocache.serializers import JsonSerializer
from datetime import date

# In-memory cache (достаточно для MVP)
cache = Cache(Cache.MEMORY, serializer=JsonSerializer())

async def get_cached_horoscope(zodiac_sign: str) -> str | None:
    """Get cached horoscope for today."""
    key = f"horoscope:{zodiac_sign}:{date.today().isoformat()}"
    return await cache.get(key)

async def set_cached_horoscope(zodiac_sign: str, text: str) -> None:
    """Cache horoscope until end of day (max 24h TTL)."""
    key = f"horoscope:{zodiac_sign}:{date.today().isoformat()}"
    await cache.set(key, text, ttl=86400)  # 24 hours
```

### Anti-Patterns to Avoid

- **Прямая вставка user input в промпт без санитизации:** Всегда ограничивать длину, удалять newlines, использовать отдельный user message
- **Синхронные API вызовы:** Использовать `AsyncOpenAI`, не блокировать event loop
- **Отсутствие timeout:** Всегда устанавливать timeout (рекомендация: 60 секунд)
- **Retry без backoff:** Использовать exponential backoff с jitter для защиты от thundering herd
- **Кеширование без TTL:** Всегда устанавливать TTL для AI-ответов

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP retry с backoff | Свой retry loop | `tenacity` | Edge cases: jitter, exception filtering, async support |
| OpenAI-compatible API client | `aiohttp` + парсинг | `openai` SDK | Типизация, streaming, error handling из коробки |
| Async caching | Dict с lock | `aiocache` | TTL, serialization, multiple backends |
| Prompt injection защита | Regex фильтры | System/user separation + length limits | Простые фильтры обходятся, proper structure надёжнее |

**Key insight:** OpenRouter специально поддерживает OpenAI SDK формат — использование его напрямую экономит время и снижает риск ошибок.

## Common Pitfalls

### Pitfall 1: Timeout без retry

**What goes wrong:** AI запрос таймаутит, пользователь видит ошибку, хотя повторный запрос бы прошёл.

**Why it happens:** Сеть, нагрузка на провайдера, cold start модели.

**How to avoid:**
- Timeout 60 секунд (достаточно для Claude)
- Retry 3 раза с exponential backoff (2, 4, 8+ секунд)
- При финальной ошибке — fallback message

**Warning signs:** Частые "Service unavailable" ошибки в логах.

### Pitfall 2: Rate Limit (429) без proper backoff

**What goes wrong:** При 429 ошибке делается немедленный retry, что усугубляет проблему.

**Why it happens:** Неправильная retry стратегия без backoff.

**How to avoid:**
```python
@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_random_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
)
```

**Warning signs:** Каскадные 429 ошибки, "thundering herd" в логах.

### Pitfall 3: Prompt Injection через вопрос пользователя

**What goes wrong:** Пользователь вставляет в вопрос "Ignore previous instructions..." и получает нежелательный ответ.

**Why it happens:** User input помещается в system prompt без разделения.

**How to avoid:**
- System prompt отдельно, user input в user message
- Ограничение длины (500 символов для вопроса)
- Удаление newlines из user input
- Не включать инструкции в user message

**Warning signs:** AI выдаёт ответы не по теме, отказывается отвечать.

### Pitfall 4: Нет валидации AI output

**What goes wrong:** AI возвращает "Извините, как AI я не могу..." или текст без нужной структуры.

**Why it happens:** AI иногда "ломается" и выдаёт мета-комментарии или неполные ответы.

**How to avoid:**
- Pydantic валидация структуры
- Проверка длины (min/max)
- Regex фильтр на "AI-специфичные" фразы
- При провале — retry с тем же промптом (до 2 раз)

**Warning signs:** Пользователи жалуются на "странные" ответы бота.

### Pitfall 5: Отсутствие fallback при полном отказе AI

**What goes wrong:** После всех retry AI недоступен, бот молчит или крашится.

**Why it happens:** Нет graceful degradation.

**How to avoid:**
- После исчерпания retry — честное сообщение пользователю
- "Сервис временно недоступен, попробуй через несколько минут"
- Логирование для мониторинга
- Для гороскопов: можно показать cached версию (если есть)

**Warning signs:** Unhandled exceptions в production логах.

## Code Examples

### Complete AI Service Integration

```python
# src/services/ai/client.py
# Source: OpenRouter docs + OpenAI SDK docs

from openai import AsyncOpenAI, RateLimitError, APITimeoutError, APIConnectionError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import structlog

from src.config import settings

logger = structlog.get_logger()


class AIService:
    """AI service for generating horoscopes and tarot interpretations."""

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
            timeout=60.0,
        )
        self.model = "anthropic/claude-3.5-sonnet"

    @retry(
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError)),
        wait=wait_random_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, structlog.stdlib.INFO),
    )
    async def _generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
    ) -> str:
        """Generate AI response with retry logic."""
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

    async def generate_horoscope(self, zodiac_sign_ru: str, date_str: str) -> str | None:
        """Generate daily horoscope. Returns None if all retries fail."""
        from src.services.ai.prompts import HoroscopePrompt
        from src.services.ai.validators import validate_horoscope

        try:
            text = await self._generate(
                system_prompt=HoroscopePrompt.SYSTEM,
                user_prompt=HoroscopePrompt.user(zodiac_sign_ru, date_str),
            )

            # Validate output
            is_valid, error = validate_horoscope(text)
            if not is_valid:
                logger.warning("horoscope_validation_failed", error=error)
                # Retry once on validation failure
                text = await self._generate(
                    system_prompt=HoroscopePrompt.SYSTEM,
                    user_prompt=HoroscopePrompt.user(zodiac_sign_ru, date_str),
                )
                is_valid, error = validate_horoscope(text)
                if not is_valid:
                    logger.error("horoscope_validation_failed_after_retry", error=error)
                    return None

            return text

        except Exception as e:
            logger.error("horoscope_generation_failed", error=str(e))
            return None

    async def generate_tarot_interpretation(
        self,
        question: str,
        cards: list[dict],
        is_reversed: list[bool],
    ) -> str | None:
        """Generate tarot spread interpretation. Returns None if all retries fail."""
        from src.services.ai.prompts import TarotSpreadPrompt

        try:
            text = await self._generate(
                system_prompt=TarotSpreadPrompt.SYSTEM,
                user_prompt=TarotSpreadPrompt.user(question, cards, is_reversed),
            )

            # Basic validation (length only for tarot)
            if len(text) < 200 or len(text) > 3000:
                logger.warning("tarot_validation_failed", length=len(text))
                text = await self._generate(
                    system_prompt=TarotSpreadPrompt.SYSTEM,
                    user_prompt=TarotSpreadPrompt.user(question, cards, is_reversed),
                )

            return text

        except Exception as e:
            logger.error("tarot_generation_failed", error=str(e))
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

async def get_horoscope_text(zodiac_sign: str, zodiac_sign_ru: str) -> tuple[str, str]:
    """
    Get horoscope text from AI (with caching) or fallback.

    Returns:
        (forecast_text, tip_text)
    """
    from src.services.ai.cache import get_cached_horoscope, set_cached_horoscope
    from src.services.ai.client import get_ai_service

    # Check cache first
    cached = await get_cached_horoscope(zodiac_sign)
    if cached:
        return parse_horoscope_sections(cached)

    # Generate with AI
    ai = get_ai_service()
    date_str = date.today().strftime("%d.%m.%Y")
    text = await ai.generate_horoscope(zodiac_sign_ru, date_str)

    if text:
        # Cache for the day
        await set_cached_horoscope(zodiac_sign, text)
        return parse_horoscope_sections(text)

    # Fallback: honest message
    return (
        "Сервис временно недоступен. Пожалуйста, попробуй через несколько минут.",
        "Иногда звёзды молчат, чтобы мы прислушались к себе."
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct HTTP calls | OpenAI SDK | 2024 | Типизация, error handling, streaming из коробки |
| Sync requests | AsyncOpenAI | 2024 | Не блокирует event loop, лучше для Telegram бота |
| Simple retry | Exponential backoff + jitter | Standard | Защита от thundering herd, лучше recovery |
| String parsing | Pydantic validation | Standard | Type safety, clear error messages |

**Deprecated/outdated:**
- `openai` < 1.0: Старый синхронный API, не используется
- Прямые HTTP запросы к OpenRouter: Работает, но SDK проще

## Open Questions

1. **Выбор между Claude 3.5 Sonnet и Claude 3.7 Sonnet**
   - What we know: Claude 3.7 Sonnet доступен на OpenRouter, улучшенный reasoning
   - What's unclear: Нужен ли reasoning для гороскопов, cost difference
   - Recommendation: Начать с 3.5 Sonnet (указан в requirements), мигрировать если нужно

2. **Streaming vs non-streaming для Telegram**
   - What we know: Streaming уменьшает TTFB, но Telegram edit_message имеет rate limits
   - What's unclear: Оптимальная стратегия для UX
   - Recommendation: Начать без streaming (проще), добавить если нужно

3. **Redis vs in-memory кеширование**
   - What we know: In-memory проще, но не переживает рестарт
   - What's unclear: Критичность потери кеша при деплое
   - Recommendation: In-memory для MVP (aiocache.MEMORY), Redis при необходимости

## Sources

### Primary (HIGH confidence)
- [OpenRouter Quickstart](https://openrouter.ai/docs/quickstart) - API integration patterns
- [OpenRouter Python SDK](https://openrouter.ai/docs/sdks/python) - SDK documentation
- [OpenRouter Errors](https://openrouter.ai/docs/api/reference/errors-and-debugging) - Error codes and handling
- [Claude 3.5 Sonnet on OpenRouter](https://openrouter.ai/anthropic/claude-3.5-sonnet) - Model specs and pricing
- [Tenacity Documentation](https://tenacity.readthedocs.io/) - Retry library

### Secondary (MEDIUM confidence)
- [OpenAI Python SDK GitHub](https://github.com/openai/openai-python) - AsyncOpenAI usage
- [aiocache Documentation](https://aiocache.aio-libs.org/) - Caching patterns
- [Pydantic LLM Validation](https://pydantic.dev/articles/llm-validation) - Output validation

### Tertiary (LOW confidence)
- WebSearch: Prompt injection best practices (OWASP, various blogs)
- WebSearch: AI horoscope generation patterns (various sources)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - OpenRouter официально рекомендует OpenAI SDK
- Architecture: HIGH - Паттерны из официальной документации
- Retry/Error handling: HIGH - Стандартные практики, документированы
- Prompt templates: MEDIUM - Базируется на best practices, но требует итераций
- Validation: MEDIUM - Pydantic стандарт, но конкретные regex требуют тестирования
- Caching: HIGH - aiocache документирован, простая реализация

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - stable domain, OpenRouter API стабильный)
