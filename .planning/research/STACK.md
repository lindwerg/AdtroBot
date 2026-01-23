# Stack Research

**Domain:** Telegram бот с астрологией/таро + AI + платежи + админ панель
**Researched:** 2026-01-23 (v2.0 additions)
**Confidence:** HIGH

## v2.0 Stack Additions

Этот документ расширяет v1.0 стек новыми технологиями для:
- AI генерации изображений
- Мониторинга и observability
- Улучшенного кэширования
- Тестирования через Telegram API
- Background jobs оптимизации

---

## 1. AI Image Generation

### Рекомендация: Together.ai + FLUX.1 [schnell]

| Provider | Model | Цена | Free Tier | Качество |
|----------|-------|------|-----------|----------|
| **Together.ai** | FLUX.1 [schnell] | $0 (3 мес.) | **Unlimited 3 мес.** | Высокое, быстрое |
| Replicate | FLUX.1 schnell | $0.015/img | 50 img/мес. | Высокое |
| fal.ai | FLUX.2 dev | $0.012/MP | Preview бесплатно | Очень высокое |
| OpenAI | DALL-E 3 | $0.04/img | Нет | Очень высокое |

**Почему Together.ai:**
1. **Бесплатно 3 месяца** — unlimited генерации через FLUX.1-schnell-Free endpoint
2. **Коммерческое использование разрешено** (в отличие от FLUX.1 dev)
3. **OpenAI-совместимый API** — легко интегрировать через существующий openai SDK
4. **Единый стиль** — FLUX.1 дает consistent visual style
5. **Высокое качество** — 95% prompt adherence (vs 87% DALL-E 3, по бенчмаркам)

### Интеграция

```python
# Используем существующий openai SDK с Together.ai base URL
from openai import OpenAI

client = OpenAI(
    api_key=settings.together_api_key,
    base_url="https://api.together.xyz/v1"
)

response = client.images.generate(
    model="black-forest-labs/FLUX.1-schnell-Free",
    prompt="Mystical Aries zodiac sign, celestial art style, stars and constellations",
    n=1
)
image_url = response.data[0].url
```

**Env variables:**
```
TOGETHER_API_KEY=...  # Новая переменная
```

### Fallback стратегия (после 3 месяцев)

| Сценарий | Решение | Цена |
|----------|---------|------|
| Together.ai free истек | fal.ai FLUX.2 dev | $0.012/MP (~$0.01/img) |
| Нужно дешевле | Replicate FLUX.1 schnell | $0.015/img |
| Нужно лучше | OpenAI DALL-E 3 | $0.04/img |

### Изображения для проекта (15-20 штук)

При использовании Together.ai free tier:
- Welcome image: 1 шт. — **$0**
- 12 знаков зодиака: 12 шт. — **$0**
- Таро расклады: 3 шт. (3-card, Celtic cross, card of day) — **$0**
- Натальная карта: 1 шт. — **$0**
- Paywall: 1 шт. — **$0**

**Итого: $0** (при генерации в free период)

### Что НЕ использовать

| Avoid | Why |
|-------|-----|
| Midjourney | Нет API, только Discord |
| DALL-E 3 напрямую | Дороже ($0.04/img), нет free tier |
| Self-hosted SD | Требует GPU, overkill для 20 изображений |
| Hugging Face Inference | Лимиты free tier сократились, 402 errors |

---

## 2. Monitoring & Observability

### Рекомендация: Sentry.io (Free Tier)

| Tool | Free Tier | Интеграция | Для чего |
|------|-----------|------------|----------|
| **Sentry.io** | 5K events/мес. | FastAPI native | Errors + Performance |
| Prometheus + Grafana | Unlimited (self-hosted) | Сложная настройка | Metrics |
| Datadog | 14 дней trial | Платный | Full observability |

**Почему Sentry:**
1. **5,000 events бесплатно** — достаточно для MVP/SMB
2. **FastAPI integration** — автоматическая, просто `pip install sentry-sdk`
3. **Error tracking** — все исключения с трейсами
4. **Performance monitoring** — response times, slow queries
5. **Railway совместимость** — просто добавить SENTRY_DSN env var

### Интеграция

```python
# src/main.py — добавить в начало
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    traces_sample_rate=0.1,  # 10% транзакций для performance
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
    ],
    environment=settings.environment,  # "production" / "development"
)
```

**Env variables:**
```
SENTRY_DSN=https://xxx@sentry.io/xxx
ENVIRONMENT=production
```

### Дополнительные метрики (в коде)

Для horoscopes_today, API costs, Bot Health — использовать **PostgreSQL таблицу**:

```sql
CREATE TABLE metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Примеры записей:
-- ('horoscopes_today', 12, now(), '{"date": "2026-01-23"}')
-- ('api_cost_openrouter', 0.0012, now(), '{"model": "gpt-4o-mini", "tokens": 500}')
-- ('bot_response_time_ms', 234, now(), '{"handler": "horoscope"}')
```

**Не нужно:**
- Prometheus — overkill, требует отдельный сервис
- Grafana — overkill для текущего масштаба
- Custom metrics server — PostgreSQL достаточно

---

## 3. Caching Solution

### Рекомендация: PostgreSQL-based caching (текущий подход)

| Solution | Цена/мес. | Latency | Persistence | Для AdtroBot |
|----------|-----------|---------|-------------|--------------|
| **PostgreSQL cache table** | $0 (уже есть) | ~5-10ms | Да | Рекомендуется |
| Railway Redis addon | ~$5-10 | ~1ms | Да | Не нужно |
| In-memory (текущий) | $0 | <1ms | Нет (теряется при рестарте) | Не для production |

**Почему PostgreSQL вместо Redis:**
1. **Уже есть** — не нужен дополнительный сервис
2. **Persistence** — кэш переживает рестарты
3. **Достаточная скорость** — 5-10ms для гороскопов нормально
4. **Дешевле** — Redis addon = +$5-10/мес.
5. **Проще** — одна БД вместо двух

### Схема кэширования

```sql
CREATE TABLE horoscope_cache (
    id SERIAL PRIMARY KEY,
    zodiac_sign VARCHAR(20) NOT NULL,
    cache_date DATE NOT NULL,
    horoscope_text TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(zodiac_sign, cache_date)
);

CREATE INDEX idx_horoscope_cache_date ON horoscope_cache(cache_date);
```

### Миграция с in-memory

Текущий `src/services/ai/cache.py` использует in-memory dict. Для v2.0:
1. Добавить таблицу `horoscope_cache`
2. Background job генерирует 12 гороскопов каждые 12ч
3. Handlers читают из таблицы (не генерируют на лету)

**Redis НЕ нужен потому что:**
- FSM storage в aiogram — MemoryStorage работает (state не критичен)
- Кэш гороскопов — PostgreSQL достаточно
- Rate limiting — не требуется на текущем масштабе

---

## 4. Telegram API Testing

### Рекомендация: Telethon + pytest

| Library | Purpose | Active | Docs |
|---------|---------|--------|------|
| **Telethon** | MTProto user client | Да | Отличные |
| Pyrogram | MTProto user client | **Не поддерживается** | Хорошие |
| python-telegram-bot | Bot API only | Да | Не для тестов |

**Почему Telethon:**
1. **Активная разработка** — v1.42.0, обновляется
2. **Pyrogram больше не поддерживается** — автор прекратил разработку
3. **MTProto** — прямой доступ к Telegram API, не через Bot API
4. **User client** — можно симулировать реального пользователя
5. **StringSession** — удобно для CI/CD (session в env var)

### Интеграция

```bash
pip install telethon==1.42.0
```

```python
# tests/test_telegram_bot.py
import pytest
from telethon import TelegramClient
from telethon.sessions import StringSession

# Получить api_id и api_hash на https://my.telegram.org
API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION_STRING = os.environ["TELEGRAM_SESSION_STRING"]
BOT_USERNAME = "@AdtroBot"

@pytest.fixture
async def client():
    client = TelegramClient(
        StringSession(SESSION_STRING),
        API_ID,
        API_HASH
    )
    await client.start()
    yield client
    await client.disconnect()

@pytest.mark.asyncio
async def test_start_command(client):
    """Test /start returns welcome message."""
    await client.send_message(BOT_USERNAME, "/start")
    response = await client.get_messages(BOT_USERNAME, limit=1)
    assert response[0].text is not None
    assert "Добро пожаловать" in response[0].text or "привет" in response[0].text.lower()

@pytest.mark.asyncio
async def test_horoscope_button(client):
    """Test horoscope flow."""
    await client.send_message(BOT_USERNAME, "/start")
    # Получить inline кнопки и нажать на гороскоп
    messages = await client.get_messages(BOT_USERNAME, limit=1)
    # ... проверить наличие кнопок
```

### Генерация StringSession

```python
# scripts/generate_session.py (запустить один раз локально)
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("Session string:", client.session.save())
    # Сохранить в TELEGRAM_SESSION_STRING
```

**Env variables для тестов:**
```
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=0123456789abcdef...
TELEGRAM_SESSION_STRING=1BVtsOH...
```

### Playwright для Web Testing

Playwright остается для:
- Admin panel testing (React SPA)
- Telegram Web App (если добавится)

```bash
pip install playwright pytest-playwright
playwright install chromium
```

---

## 5. Background Jobs

### Рекомендация: APScheduler (оставить текущий)

| Solution | Complexity | Redis Required | Для AdtroBot |
|----------|------------|----------------|--------------|
| **APScheduler** | Низкая | Нет | Рекомендуется |
| ARQ | Средняя | Да | Overkill |
| Celery | Высокая | Да (или RabbitMQ) | Overkill |
| Dramatiq | Средняя | Да | Overkill |

**Почему оставить APScheduler:**
1. **Уже работает** — настроен с SQLAlchemyJobStore
2. **Не требует Redis** — jobs в PostgreSQL
3. **Достаточно для задач:**
   - Генерация 12 гороскопов каждые 12ч
   - Проверка подписок
   - Отправка уведомлений
4. **Простота** — нет отдельных worker процессов

### Улучшения для v2.0

```python
# Добавить job для pre-generation horoscopes
from apscheduler.triggers.cron import CronTrigger

scheduler.add_job(
    generate_all_horoscopes,  # Новая функция
    CronTrigger(hour="6,18", minute=0, timezone="Europe/Moscow"),
    id="generate_all_horoscopes",
    replace_existing=True,
    misfire_grace_time=3600,
)

async def generate_all_horoscopes():
    """Pre-generate 12 horoscopes for all zodiac signs."""
    from src.services.ai.client import generate_horoscope
    from src.db.engine import async_session_maker

    signs = ["aries", "taurus", "gemini", ...]
    async with async_session_maker() as session:
        for sign in signs:
            text = await generate_horoscope(sign)
            # Сохранить в horoscope_cache таблицу
            ...
```

**ARQ/Celery НЕ нужны потому что:**
- Нет distributed workers
- Нет очередей с миллионами задач
- APScheduler + SQLAlchemy хватает

---

## Полный v2.0 Stack Summary

### Новые зависимости

```bash
# v2.0 additions
pip install sentry-sdk==2.50.0      # Monitoring
pip install telethon==1.42.0        # Telegram API testing
pip install playwright==1.50.0      # Web testing (admin)
pip install pytest-playwright       # Playwright pytest plugin
```

### pyproject.toml additions

```toml
[project]
dependencies = [
    # ... existing v1.0 deps ...
    "sentry-sdk>=2.50.0",
]

[tool.poetry.group.dev.dependencies]
# ... existing ...
telethon = ">=1.42.0"
playwright = ">=1.50.0"
pytest-playwright = ">=0.6.0"
```

### Environment Variables (новые)

```
# Image Generation (Together.ai)
TOGETHER_API_KEY=xxx

# Monitoring (Sentry)
SENTRY_DSN=https://xxx@sentry.io/xxx
ENVIRONMENT=production

# Testing (Telethon) - только для dev/CI
TELEGRAM_API_ID=xxx
TELEGRAM_API_HASH=xxx
TELEGRAM_SESSION_STRING=xxx
```

---

## Что НЕ добавлять

| Technology | Why Not |
|------------|---------|
| Redis | Не нужен — PostgreSQL хватает для кэша и scheduler |
| Celery / ARQ | Overkill — APScheduler достаточно |
| Prometheus / Grafana | Overkill — Sentry + PostgreSQL metrics |
| Self-hosted SD/Flux | Overkill — Together.ai free tier |
| Pyrogram | Не поддерживается — использовать Telethon |
| MongoDB | Данные реляционные — PostgreSQL лучше |

---

## Version Compatibility (v2.0 additions)

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| sentry-sdk 2.50.0 | FastAPI 0.128.0 | Native integration |
| sentry-sdk 2.50.0 | SQLAlchemy 2.0 | Native integration |
| telethon 1.42.0 | Python 3.11+ | Asyncio native |
| playwright 1.50.0 | Python 3.10+ | Chromium included |

---

## Railway Deployment Notes (v2.0)

**Дополнительные env vars:**
```
TOGETHER_API_KEY=...
SENTRY_DSN=...
ENVIRONMENT=production
```

**Не нужно добавлять сервисы:**
- Redis — не нужен
- Worker processes — не нужны
- Metrics server — не нужен

**Единственный сервис остается:**
1. Web Service (FastAPI + aiogram webhook + APScheduler)
2. PostgreSQL (данные + кэш + scheduler jobs + metrics)

---

## Sources

### AI Image Generation
- [Together.ai Flux Blog](https://www.together.ai/blog/flux-api-is-now-available-on-together-ai-new-pro-free-access-to-flux-schnell) — free tier info
- [Together.ai Pricing](https://www.together.ai/pricing) — pricing details
- [WaveSpeedAI Guide](https://wavespeed.ai/blog/posts/complete-guide-ai-image-apis-2026/) — API comparison
- [Replicate](https://replicate.com/collections/text-to-image) — alternative pricing

### Monitoring
- [Sentry FastAPI Docs](https://docs.sentry.io/platforms/python/integrations/fastapi/) — integration guide
- [Sentry Pricing](https://sentry.io/pricing/) — free tier (5K events)
- [sentry-sdk PyPI](https://pypi.org/project/sentry-sdk/) — version 2.50.0

### Telegram Testing
- [Telethon GitHub](https://github.com/LonamiWebs/Telethon) — MTProto library
- [Telethon Docs](https://docs.telethon.dev/en/stable/) — usage examples
- [Telethon PyPI](https://pypi.org/project/Telethon/) — version 1.42.0
- [Pyrogram Status](https://docs.pyrogram.org/) — "no longer maintained"

### Caching & Background Jobs
- [Railway Redis Docs](https://docs.railway.com/guides/redis) — pricing context
- [Railway Pricing](https://railway.com/pricing) — usage-based model
- [APScheduler Docs](https://apscheduler.readthedocs.io/) — SQLAlchemyJobStore

### Playwright
- [Playwright Python](https://playwright.dev/python/) — official docs
- [Playwright Releases](https://github.com/microsoft/playwright/releases) — version 1.50.0

---
*Stack research for: AdtroBot v2.0 — Visual Enhancement, Monitoring, Performance*
*Researched: 2026-01-23*
