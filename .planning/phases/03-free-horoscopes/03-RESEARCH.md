# Phase 3: Free Horoscopes - Research

**Researched:** 2026-01-22
**Domain:** Telegram бот отображение контента, push-уведомления, таймзоны
**Confidence:** HIGH

## Summary

Исследование фокусируется на трёх ключевых областях:
1. **Форматирование гороскопов** — aiogram 3.x предоставляет `aiogram.utils.formatting` модуль с `BlockQuote`, `Bold`, `Text` для entity-based форматирования (не HTML/Markdown строки).
2. **Push-уведомления** — APScheduler 3.x с `AsyncIOScheduler` + `CronTrigger` для ежедневных уведомлений. Для персистентности — `SQLAlchemyJobStore` с PostgreSQL.
3. **Навигация по знакам** — `CallbackData` factory для inline keyboards с 12 знаками зодиака.

Telegram Bot API не имеет встроенного планировщика — нужен внешний механизм (APScheduler). Таймзоны пользователей хранятся как IANA строки (например, `Europe/Moscow`), используется `zoneinfo` (Python 3.9+) или `pytz`.

**Primary recommendation:** Использовать `aiogram.utils.formatting.BlockQuote` для цитат, APScheduler `CronTrigger` с per-user timezone для push-уведомлений, `CallbackData` factory для навигации по знакам.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| aiogram | 3.20+ | Telegram Bot framework | Уже в проекте, async-native |
| APScheduler | 3.11.x | Task scheduling | Async support, PostgreSQL persistence, timezone-aware |
| zoneinfo | stdlib | Timezone handling | Python 3.11 stdlib, IANA database |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tzdata | latest | IANA timezone data | Fallback если системные данные недоступны |
| pytz | 2024.x | Legacy timezone compat | Только если APScheduler требует (3.x ещё использует pytz) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| APScheduler | Celery Beat | Overkill для простых daily jobs, требует Redis/RabbitMQ |
| zoneinfo | pytz | pytz deprecated для Python 3.9+, но APScheduler 3.x ещё зависит от него |
| Entity formatting | HTML strings | Entity-based безопаснее (автоэкранирование), но сложнее для простых случаев |

**Installation:**
```bash
poetry add apscheduler pytz
# zoneinfo уже в Python 3.11 stdlib
```

## Architecture Patterns

### Recommended Project Structure

```
src/
├── bot/
│   ├── handlers/
│   │   ├── horoscope.py     # Кнопка "Гороскоп", выбор знака
│   │   └── profile.py       # Настройки уведомлений
│   ├── keyboards/
│   │   ├── horoscope.py     # Inline keyboard для знаков
│   │   └── timezone.py      # Выбор таймзоны
│   ├── callbacks/
│   │   └── horoscope.py     # CallbackData definitions
│   └── utils/
│       └── formatting.py    # Horoscope message formatting
├── services/
│   ├── horoscope.py         # Business logic для получения гороскопов
│   └── scheduler.py         # APScheduler setup и job functions
├── db/
│   └── models/
│       ├── user.py          # + timezone, notification_time fields
│       └── horoscope.py     # Daily horoscope cache
└── scheduler/
    └── jobs.py              # Scheduled job functions
```

### Pattern 1: Entity-Based Message Formatting

**What:** Используем `aiogram.utils.formatting` вместо HTML/Markdown строк
**When to use:** Для сложного форматирования с nested elements и user input
**Example:**
```python
# Source: https://docs.aiogram.dev/en/latest/utils/formatting.html
from aiogram.utils.formatting import Text, Bold, BlockQuote, as_line

def format_horoscope(sign_emoji: str, sign_name: str, date_str: str,
                     forecast: str, tip: str) -> Text:
    """Format horoscope message using entity-based formatting."""
    return Text(
        as_line(f"{sign_emoji} {sign_name} | {date_str}"),
        "\n",
        as_line(Bold("🔮 Общий прогноз")),
        "\n",
        as_line(forecast),
        "\n",
        as_line(Bold("💡 Совет дня")),
        "\n",
        BlockQuote(tip),
    )

# Usage in handler:
content = format_horoscope("♈️", "Овен", "22 января", forecast_text, tip_text)
await message.answer(**content.as_kwargs())
```

### Pattern 2: CallbackData Factory для навигации

**What:** Типизированные callback данные для inline buttons
**When to use:** Навигация между знаками зодиака, пагинация
**Example:**
```python
# Source: https://docs.aiogram.dev/en/dev-3.x/dispatcher/filters/callback_data.html
from aiogram.filters.callback_data import CallbackData
from aiogram import F

class ZodiacCallback(CallbackData, prefix="zodiac"):
    sign: str  # English sign name: "Aries", "Taurus", etc.

# Creating keyboard
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_zodiac_keyboard(current_sign: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name, zodiac in ZODIAC_SIGNS.items():
        text = f"{'✓ ' if name == current_sign else ''}{zodiac.emoji}"
        builder.button(
            text=text,
            callback_data=ZodiacCallback(sign=name).pack()
        )
    builder.adjust(4, 4, 4)  # 3 rows of 4 buttons
    return builder.as_markup()

# Handler
@router.callback_query(ZodiacCallback.filter())
async def show_sign_horoscope(callback: CallbackQuery, callback_data: ZodiacCallback):
    sign = callback_data.sign
    # ... fetch and display horoscope
    await callback.answer()
```

### Pattern 3: APScheduler с Per-User Timezone

**What:** Планирование уведомлений с учётом таймзоны каждого пользователя
**When to use:** Ежедневные push-уведомления в локальное время пользователя
**Example:**
```python
# Source: https://apscheduler.readthedocs.io/en/3.x/userguide.html
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

# Scheduler setup
jobstores = {
    'default': SQLAlchemyJobStore(url=settings.database_url)
}
scheduler = AsyncIOScheduler(jobstores=jobstores, timezone='UTC')

# Job function (must accept bot instance)
async def send_daily_horoscope(bot: Bot, user_id: int, zodiac_sign: str):
    horoscope = await get_horoscope(zodiac_sign)
    await bot.send_message(chat_id=user_id, text=horoscope)

# Schedule per-user job with their timezone
def schedule_user_notification(user_id: int, hour: int, timezone: str, zodiac_sign: str):
    job_id = f"daily_horoscope_{user_id}"
    scheduler.add_job(
        send_daily_horoscope,
        CronTrigger(hour=hour, minute=0, timezone=timezone),
        args=[bot, user_id, zodiac_sign],
        id=job_id,
        replace_existing=True,  # CRITICAL: avoid duplicate jobs on restart
    )
```

### Anti-Patterns to Avoid

- **HTML string concatenation с user input:** Уязвимость к injection. Используй entity-based formatting или `html.escape()`.
- **Storing timezone as offset (+3, -5):** DST не учитывается. Храни IANA name (`Europe/Moscow`).
- **One scheduler job for all users:** Не масштабируется. Создавай per-user jobs или batch processing по UTC-часам.
- **Scheduling jobs без `replace_existing=True`:** Дубликаты после каждого рестарта.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Message formatting | String templates с `<b>`, `*` | `aiogram.utils.formatting` | Entity-based автоматически экранирует, поддерживает nested elements |
| Task scheduling | Custom cron, database polling | APScheduler | Timezone support, persistence, cron expressions |
| Timezone conversion | Manual offset calculations | `zoneinfo.ZoneInfo` / `pytz` | DST handling, IANA database |
| Callback data parsing | `callback.data.split(":")` | `CallbackData` factory | Type safety, automatic pack/unpack |

**Key insight:** Telegram entity system сложнее чем кажется (overlapping entities, proper offsets). aiogram.utils.formatting решает это автоматически.

## Common Pitfalls

### Pitfall 1: BlockQuote newlines

**What goes wrong:** BlockQuote в Telegram не работает с `\n` внутри — это создаёт несколько quote blocks
**Why it happens:** Telegram трактует newline как конец блока
**How to avoid:** Один BlockQuote = один абзац. Для многострочных цитат используй пробел или soft break
**Warning signs:** Совет дня разбивается на несколько цитат с отдельными вертикальными чертами

### Pitfall 2: APScheduler job persistence with async functions

**What goes wrong:** Async функции не сериализуются корректно в SQLAlchemyJobStore
**Why it happens:** Pickle не может сериализовать coroutines
**How to avoid:**
1. Используй `func=` вместо лямбд
2. Передавай только serializable аргументы (int, str, не объекты)
3. Bot instance получай внутри job function, не передавай как аргумент
**Warning signs:** `PicklingError` при добавлении job

```python
# WRONG: passing bot instance
scheduler.add_job(send_msg, args=[bot, user_id])  # bot не сериализуется

# RIGHT: get bot inside function
async def send_msg(user_id: int):
    bot = get_bot()  # Lazy get
    await bot.send_message(user_id, "text")

scheduler.add_job(send_msg, args=[user_id])
```

### Pitfall 3: Timezone при рестарте

**What goes wrong:** Jobs не выполняются в правильное время после рестарта
**Why it happens:** Scheduler timezone и job timezone могут не совпадать
**How to avoid:**
1. Scheduler timezone = UTC
2. Каждый CronTrigger получает user-specific timezone
3. Тестируй с реальными перезапусками
**Warning signs:** Уведомления приходят не в то время после деплоя

### Pitfall 4: Callback data length limit

**What goes wrong:** `callback_data` обрезается или не работает
**Why it happens:** Telegram limit: 64 bytes для callback_data
**How to avoid:** Используй короткие prefix ("z" вместо "zodiac"), английские sign names
**Warning signs:** `CallbackData.unpack()` возвращает неправильные значения

## Code Examples

### Полный пример форматирования гороскопа

```python
# Source: aiogram docs + CONTEXT.md requirements
from datetime import date
from aiogram.utils.formatting import Text, Bold, BlockQuote, as_line

def format_daily_horoscope(
    sign_emoji: str,
    sign_name_ru: str,
    forecast_date: date,
    general_forecast: str,
    daily_tip: str,
) -> Text:
    """
    Format horoscope according to CONTEXT.md spec:

    ♈️ Овен | 22 января

    *🔮 Общий прогноз*

    [4-5 sentences]

    *💡 Совет дня*

    > [2 sentences]
    """
    # Format date in Russian
    months_ru = [
        "", "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    date_str = f"{forecast_date.day} {months_ru[forecast_date.month]}"

    return Text(
        as_line(f"{sign_emoji} {sign_name_ru} | {date_str}"),
        "\n",
        Bold("🔮 Общий прогноз"),
        "\n\n",
        as_line(general_forecast),
        "\n",
        Bold("💡 Совет дня"),
        "\n\n",
        BlockQuote(daily_tip),
    )

# Usage:
content = format_daily_horoscope(
    sign_emoji="♈️",
    sign_name_ru="Овен",
    forecast_date=date.today(),
    general_forecast="Сегодня звёзды благоволят новым начинаниям...",
    daily_tip="Не откладывайте важные разговоры на потом.",
)
await message.answer(**content.as_kwargs())
```

### Keyboard с 12 знаками

```python
# Source: aiogram docs callback_data
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

class ZodiacCB(CallbackData, prefix="z"):  # Short prefix!
    s: str  # sign name (English)

def build_zodiac_keyboard() -> InlineKeyboardMarkup:
    """Build 4x3 grid of zodiac signs."""
    from src.bot.utils.zodiac import ZODIAC_SIGNS

    builder = InlineKeyboardBuilder()
    for name, zodiac in ZODIAC_SIGNS.items():
        builder.button(
            text=zodiac.emoji,
            callback_data=ZodiacCB(s=name).pack()
        )
    builder.adjust(4, 4, 4)  # 3 rows of 4
    return builder.as_markup()
```

### APScheduler integration с FastAPI lifespan

```python
# Source: APScheduler docs + existing main.py pattern
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from pytz import utc

scheduler: AsyncIOScheduler | None = None

def get_scheduler() -> AsyncIOScheduler:
    global scheduler
    if scheduler is None:
        jobstores = {
            'default': SQLAlchemyJobStore(
                url=settings.database_url.replace("+asyncpg", "")  # Sync URL for jobstore
            )
        }
        scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            timezone=utc,
        )
    return scheduler

# In main.py lifespan:
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing setup ...

    # Start scheduler
    sched = get_scheduler()
    sched.start()
    await logger.ainfo("Scheduler started")

    yield

    # Shutdown scheduler gracefully
    sched.shutdown(wait=False)
    # ... existing cleanup ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `markdown.py` utils | `aiogram.utils.formatting` | aiogram 3.x | Entity-based, safer |
| pytz everywhere | zoneinfo stdlib | Python 3.9 | Simpler, no external dep |
| APScheduler 4.0 alpha | APScheduler 3.11.x | 2024-2025 | 4.0 ещё нестабильна, используй 3.x |
| HTML parse_mode strings | `as_kwargs()` with entities | aiogram 3.x | Auto-escaping |

**Deprecated/outdated:**
- `aiogram.utils.markdown` — legacy, будет удалён
- pytz для новых проектов — используй zoneinfo, но APScheduler 3.x всё ещё требует pytz

## Open Questions

1. **Batch vs per-user jobs для уведомлений**
   - What we know: Per-user jobs проще, но создают много записей в job store
   - What's unclear: Производительность при 10k+ пользователей
   - Recommendation: Начать с per-user, оптимизировать если нужно. Альтернатива: batch job каждый час UTC, фильтрация пользователей по их local time

2. **Timezone selection UX**
   - What we know: Нужен город/регион от пользователя
   - What's unclear: Лучший UX — список популярных городов vs inline search vs геолокация
   - Recommendation: Список популярных RU таймзон (Moscow, Kaliningrad, Samara, etc.) + кнопка "Другой"

3. **Horoscope cache table**
   - What we know: Нужно хранить сгенерированные гороскопы (Phase 5)
   - What's unclear: Структура для Phase 3 с mock data
   - Recommendation: Пока использовать in-memory dict как в Phase 2, добавить table в Phase 5

## Sources

### Primary (HIGH confidence)
- [aiogram.utils.formatting docs](https://docs.aiogram.dev/en/latest/utils/formatting.html) — BlockQuote, Bold, Text, as_kwargs()
- [aiogram CallbackData docs](https://docs.aiogram.dev/en/dev-3.x/dispatcher/filters/callback_data.html) — factory pattern, filter usage
- [APScheduler User Guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html) — AsyncIOScheduler, CronTrigger, SQLAlchemyJobStore
- [APScheduler CronTrigger docs](https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html) — timezone parameter, all trigger options

### Secondary (MEDIUM confidence)
- [aiogram GitHub Discussion #1362](https://github.com/aiogram/aiogram/discussions/1362) — APScheduler + aiogram integration pattern
- [Python zoneinfo docs](https://docs.python.org/3/library/zoneinfo.html) — stdlib timezone handling

### Tertiary (LOW confidence)
- WebSearch results on timezone UX patterns — нужна валидация с реальным UX тестированием

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — официальная документация, проверенные библиотеки
- Architecture: HIGH — официальные примеры из документации
- Pitfalls: MEDIUM — собраны из GitHub issues и discussions
- Timezone UX: LOW — нет единого стандарта, нужно тестирование

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days — стабильные библиотеки)
