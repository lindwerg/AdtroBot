# Phase 12: Caching & Background Jobs - Research

**Researched:** 2026-01-23
**Domain:** PostgreSQL-backed caching, APScheduler background jobs, asyncio race condition prevention
**Confidence:** HIGH

## Summary

Исследование подтвердило, что текущая архитектура проекта полностью готова к реализации PostgreSQL-backed кэша. APScheduler 3.x уже используется с SQLAlchemyJobStore и AsyncIOScheduler, что означает нулевую миграцию scheduler'а. SQLAlchemy 2.x async с asyncpg уже настроен. Основная работа: создать таблицу кэша, добавить фоновый job для генерации, реализовать per-key locking через asyncio.Lock для race condition prevention.

**Ключевые находки:**
- APScheduler 3.10.4 уже используется с SQLAlchemyJobStore (persistent jobs)
- In-memory cache (`src/services/ai/cache.py`) нужно заменить на PostgreSQL-backed
- 12 знаков зодиака определены в `ZODIAC_SIGNS` dict
- `horoscope_content` таблица уже существует (для админки), можно расширить для кэша

**Primary recommendation:** Создать таблицу `horoscope_cache` для AI-генерированных гороскопов + `horoscope_views` для tracking. Использовать существующий APScheduler для фоновой генерации в 00:00. Race condition prevention через dict asyncio.Lock per zodiac sign.

## Standard Stack

### Core (уже установлено)
| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| APScheduler | 3.10.4 | Background job scheduling | Используется в `src/services/scheduler.py` |
| SQLAlchemy | 2.0.46 | Async ORM для PostgreSQL | Используется везде |
| asyncpg | 0.31.0 | Async PostgreSQL driver | Используется |
| structlog | 25.5.0 | Structured logging | Используется |

### Supporting (уже установлено)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytz | 2025.2 | Timezone handling | Для 00:00 Moscow time job |
| tenacity | 8.2.0 | Retry with backoff | Для retry логики генерации |

### Никаких новых зависимостей не требуется

Весь необходимый стек уже в проекте. Это подтверждает CONTEXT.md решение "Claude выбирает scheduler" — выбор очевиден: **продолжаем использовать APScheduler 3.x**.

**Alternatives Considered:**
| Instead of | Could Use | Why Not |
|------------|-----------|---------|
| APScheduler | Celery | Overkill для 1 job/day, требует Redis/RabbitMQ |
| APScheduler | BackgroundTasks (FastAPI) | Не persistent, теряется при restart |
| APScheduler 4.x | APScheduler 4.x | Pre-release, breaking changes, проект уже на 3.x |

## Architecture Patterns

### Recommended Project Structure
```
src/
├── db/
│   └── models/
│       └── horoscope_cache.py    # NEW: HoroscopeCache + HoroscopeView models
├── services/
│   ├── ai/
│   │   └── cache.py             # MODIFY: Add PostgreSQL backend
│   └── scheduler.py             # MODIFY: Add background generation job
```

### Pattern 1: PostgreSQL-Backed Cache Table

**What:** Отдельная таблица для хранения AI-генерированных гороскопов с TTL
**When to use:** Когда нужен persistent cache, surviving restarts

**Schema:**
```python
# Source: SQLAlchemy 2.0 patterns + project conventions
class HoroscopeCache(Base):
    __tablename__ = "horoscope_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    zodiac_sign: Mapped[str] = mapped_column(String(20), index=True)
    horoscope_date: Mapped[date] = mapped_column(Date, index=True)
    content: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("zodiac_sign", "horoscope_date", name="uq_horoscope_cache_sign_date"),
    )
```

### Pattern 2: Per-Key asyncio.Lock for Race Condition Prevention

**What:** Dictionary of asyncio.Lock objects, one per zodiac sign
**When to use:** Когда несколько coroutines могут одновременно запросить один ключ

**Example:**
```python
# Source: Python asyncio documentation + community patterns
from collections import defaultdict
import asyncio

class HoroscopeCacheService:
    def __init__(self):
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def get_or_generate(self, zodiac_sign: str) -> str:
        async with self._locks[zodiac_sign]:
            # Check cache first (inside lock)
            cached = await self._get_from_db(zodiac_sign)
            if cached:
                return cached

            # Generate (still inside lock - prevents duplicate generation)
            content = await self._generate_horoscope(zodiac_sign)
            await self._save_to_db(zodiac_sign, content)
            return content
```

### Pattern 3: APScheduler CronTrigger for Daily Generation

**What:** Фоновый job с CronTrigger для генерации в 00:00
**When to use:** Для scheduled tasks с persistent storage

**Example:**
```python
# Source: APScheduler 3.x documentation + existing scheduler.py patterns
from apscheduler.triggers.cron import CronTrigger

scheduler.add_job(
    generate_all_horoscopes,
    CronTrigger(hour=0, minute=0, timezone="Europe/Moscow"),
    id="generate_daily_horoscopes",
    replace_existing=True,
    misfire_grace_time=3600,  # 1 hour grace for misfires
)

async def generate_all_horoscopes():
    """Generate horoscopes for all 12 signs sequentially."""
    for sign_name, zodiac in ZODIAC_SIGNS.items():
        try:
            await generate_horoscope_with_retry(sign_name, zodiac.name_ru)
        except Exception as e:
            logger.error("horoscope_generation_failed", sign=sign_name, error=str(e))
            # Continue with other signs
```

### Pattern 4: Retry with Exponential Backoff (tenacity)

**What:** Автоматический retry при сбоях AI генерации
**When to use:** Для unreliable external APIs

**Example:**
```python
# Source: tenacity documentation + CONTEXT.md requirements (5/10/30 min backoff)
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(300),  # 5 min base, можно увеличить для 10/30
    reraise=True,
)
async def generate_horoscope_with_retry(zodiac_sign: str, zodiac_name_ru: str) -> str:
    ai = get_ai_service()
    return await ai.generate_horoscope(zodiac_sign, zodiac_name_ru, date_str)
```

### Anti-Patterns to Avoid

- **Global asyncio.Lock:** Блокирует ВСЕ знаки при генерации одного. Использовать per-key locks.
- **Polling for cache updates:** Расход ресурсов. Использовать event-driven (lock release).
- **In-memory dict cleanup:** Теряется при restart. Использовать PostgreSQL DELETE.
- **APScheduler 4.x migration:** Breaking changes, pre-release. Оставаться на 3.x.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Job persistence | Custom DB job table | APScheduler SQLAlchemyJobStore | Уже настроено, battle-tested |
| Retry with backoff | Manual sleep/retry loops | tenacity decorator | Clean API, configurable |
| Timezone handling | Manual UTC conversion | pytz + CronTrigger timezone param | Correct DST handling |
| Async locking | threading.Lock | asyncio.Lock | Non-blocking in event loop |

**Key insight:** APScheduler уже решает 80% задачи (persistent jobs, cron triggers, misfire handling). Не нужно писать свой scheduler.

## Common Pitfalls

### Pitfall 1: Race Condition при Cache Miss
**What goes wrong:** Два пользователя одновременно запрашивают Овна, оба получают cache miss, оба запускают AI генерацию = дублирование вызовов API и costs
**Why it happens:** Проверка кэша и генерация не атомарны
**How to avoid:** Per-key asyncio.Lock — lock до проверки кэша, release после записи
**Warning signs:** Duplicate log entries "horoscope_generated" для одного sign в одну секунду

### Pitfall 2: Memory Leak в defaultdict(asyncio.Lock)
**What goes wrong:** Locks накапливаются бесконечно если не чистить
**Why it happens:** defaultdict создает новый Lock для каждого ключа
**How to avoid:** 12 фиксированных знаков = 12 locks. Создать все заранее, не использовать defaultdict
**Warning signs:** Рост memory consumption over time

### Pitfall 3: APScheduler Job Duplication
**What goes wrong:** При каждом restart добавляется новый job с тем же ID
**Why it happens:** add_job() без replace_existing=True
**How to avoid:** Всегда `replace_existing=True` для persistent jobs
**Warning signs:** Job выполняется несколько раз в scheduled time

### Pitfall 4: Blocking Event Loop в Job Function
**What goes wrong:** AsyncIOScheduler блокируется на sync DB операции
**Why it happens:** Использование sync SQLAlchemy session в async job
**How to avoid:** Использовать async session (async_session_maker), await все DB операции
**Warning signs:** Bot перестает отвечать во время job execution

### Pitfall 5: Timezone Mismatch
**What goes wrong:** Гороскоп генерируется в неправильное время (не в 00:00 Moscow)
**Why it happens:** Server в UTC, job scheduled без timezone
**How to avoid:** Явно указывать timezone="Europe/Moscow" в CronTrigger
**Warning signs:** Генерация происходит в 3:00 Moscow time вместо 00:00

### Pitfall 6: Cache Warmup Race
**What goes wrong:** При startup несколько workers одновременно warmup кэш
**Why it happens:** Startup warmup без координации
**How to avoid:** Использовать тот же per-key locking. Или single-worker warmup (Railway = 1 instance)
**Warning signs:** Duplicate generation logs at startup

## Code Examples

### Cache Table Migration
```python
# Source: Project migration conventions (see existing migrations)
def upgrade() -> None:
    op.create_table(
        "horoscope_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zodiac_sign", sa.String(length=20), nullable=False),
        sa.Column("horoscope_date", sa.Date(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("zodiac_sign", "horoscope_date", name="uq_horoscope_cache_sign_date"),
    )
    op.create_index("ix_horoscope_cache_date", "horoscope_cache", ["horoscope_date"])
```

### Views Tracking Table
```python
# Source: Project conventions + MON-01 requirement
def upgrade() -> None:
    op.create_table(
        "horoscope_views",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zodiac_sign", sa.String(length=20), nullable=False),
        sa.Column("view_date", sa.Date(), nullable=False),
        sa.Column("view_count", sa.Integer(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("zodiac_sign", "view_date", name="uq_horoscope_views_sign_date"),
    )
```

### Cache Service with Per-Key Locking
```python
# Source: asyncio.Lock documentation + research patterns
class HoroscopeCacheService:
    _instance: "HoroscopeCacheService | None" = None

    def __init__(self):
        # Fixed locks for 12 zodiac signs (no memory leak)
        self._locks = {sign: asyncio.Lock() for sign in ZODIAC_SIGNS.keys()}

    @classmethod
    def get_instance(cls) -> "HoroscopeCacheService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def get_horoscope(
        self,
        zodiac_sign: str,
        session: AsyncSession
    ) -> str | None:
        """Get horoscope from cache or generate on-demand."""
        today = date.today()

        async with self._locks[zodiac_sign]:
            # Check cache (inside lock)
            stmt = select(HoroscopeCache).where(
                HoroscopeCache.zodiac_sign == zodiac_sign.lower(),
                HoroscopeCache.horoscope_date == today,
            )
            result = await session.execute(stmt)
            cached = result.scalar_one_or_none()

            if cached:
                # Track view
                await self._increment_view(session, zodiac_sign, today)
                return cached.content

            # Generate on-demand (rare case: first startup, after failure)
            zodiac = ZODIAC_SIGNS[zodiac_sign]
            ai = get_ai_service()
            content = await ai.generate_horoscope(
                zodiac_sign,
                zodiac.name_ru,
                today.strftime("%d.%m.%Y")
            )

            if content:
                # Save to cache
                cache_entry = HoroscopeCache(
                    zodiac_sign=zodiac_sign.lower(),
                    horoscope_date=today,
                    content=content,
                )
                session.add(cache_entry)
                await session.commit()
                await self._increment_view(session, zodiac_sign, today)

            return content
```

### Background Generation Job
```python
# Source: APScheduler 3.x docs + existing scheduler.py patterns
async def generate_all_daily_horoscopes() -> None:
    """Background job: generate horoscopes for all 12 signs at 00:00."""
    from src.db.engine import async_session_maker

    today = date.today()
    date_str = today.strftime("%d.%m.%Y")

    async with async_session_maker() as session:
        for sign_name, zodiac in ZODIAC_SIGNS.items():
            # Check if already generated (e.g., restart scenario)
            stmt = select(HoroscopeCache).where(
                HoroscopeCache.zodiac_sign == sign_name.lower(),
                HoroscopeCache.horoscope_date == today,
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                logger.info("horoscope_already_cached", sign=sign_name)
                continue

            # Generate with retry
            for attempt in range(3):
                try:
                    ai = get_ai_service()
                    content = await ai.generate_horoscope(
                        sign_name, zodiac.name_ru, date_str
                    )
                    if content:
                        cache_entry = HoroscopeCache(
                            zodiac_sign=sign_name.lower(),
                            horoscope_date=today,
                            content=content,
                        )
                        session.add(cache_entry)
                        await session.commit()
                        logger.info("horoscope_generated_background", sign=sign_name)
                        break
                except Exception as e:
                    backoff = [300, 600, 1800][attempt]  # 5/10/30 min
                    logger.warning(
                        "horoscope_generation_retry",
                        sign=sign_name,
                        attempt=attempt + 1,
                        backoff_sec=backoff,
                        error=str(e),
                    )
                    await asyncio.sleep(backoff)
            else:
                logger.error("horoscope_generation_failed", sign=sign_name)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| In-memory dict cache | PostgreSQL-backed cache | This phase | Survives restarts |
| On-demand generation | Pre-generated at 00:00 | This phase | <500ms response time |
| No view tracking | horoscope_views table | This phase | MON-01 metric available |

**Deprecated/outdated:**
- `src/services/ai/cache.py` in-memory dicts: Заменить на PostgreSQL-backed service
- `get_mock_horoscope()`: Already deprecated, kept for backwards compat

## Open Questions

1. **Cleanup старых записей**
   - What we know: CONTEXT.md говорит "Only current (24h)", нужно удалять
   - What's unclear: Когда чистить — перед генерацией или отдельный job?
   - Recommendation: Перед генерацией (DELETE WHERE horoscope_date < today) — проще, атомарно

2. **Cache warmup при startup**
   - What we know: После restart кэш в PostgreSQL остается
   - What's unclear: Нужен ли warmup in-memory cache из PostgreSQL?
   - Recommendation: Не нужен — читать напрямую из PostgreSQL, это достаточно быстро для 12 записей

3. **horoscope_views aggregation**
   - What we know: Нужен daily count для админки
   - What's unclear: Per-sign или total?
   - Recommendation: Per-sign per-day (более гранулярно), total считается через SUM

## Sources

### Primary (HIGH confidence)
- APScheduler 3.x documentation: https://apscheduler.readthedocs.io/en/3.x/userguide.html
- Python asyncio.Lock documentation: https://docs.python.org/3/library/asyncio-sync.html
- Project codebase: `src/services/scheduler.py`, `src/services/ai/cache.py`, `src/db/models/`

### Secondary (MEDIUM confidence)
- SQLAlchemy 2.0 async patterns: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html
- Per-key locking community patterns: https://superfastpython.com/asyncio-lock/

### Tertiary (LOW confidence)
- APScheduler 4.x migration notes (for reference only, NOT recommending migration)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Все библиотеки уже в проекте, проверено в pyproject.toml
- Architecture: HIGH - Паттерны основаны на официальной документации и existing code
- Pitfalls: MEDIUM - Часть основана на community experience, не личном опыте

**Research date:** 2026-01-23
**Valid until:** 2026-02-23 (30 days - stable technologies, no breaking changes expected)
