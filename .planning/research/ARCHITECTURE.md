# Architecture Research

**Domain:** Telegram бот с подписками, админ панелью и AI интеграцией
**Researched:** 2026-01-22 (v1.0), 2026-01-23 (v2.0 дополнение)
**Confidence:** HIGH

---

## v2.0 Дополнение: Visual Assets, Caching, Background Jobs, Monitoring

### Обзор изменений v2.0

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Railway Service                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐        │
│  │   FastAPI      │    │    aiogram     │    │  APScheduler   │        │
│  │   + /metrics   │────│   Dispatcher   │    │ + pre-gen job  │        │
│  │   + /health    │    │                │    │ + metrics job  │        │
│  └───────┬────────┘    └───────┬────────┘    └───────┬────────┘        │
│          │                     │                     │                  │
│  ┌───────┴───────────┐  ┌──────┴───────────┐  ┌─────┴────────────┐     │
│  │  Metrics          │  │  Redis Cache     │  │  Image Service   │     │
│  │  Collector        │  │  (horoscopes,    │  │  (PostgreSQL     │     │
│  │  (prometheus-     │  │   file_ids)      │  │   + file_id)     │     │
│  │  fastapi-instr.)  │  │                  │  │                  │     │
│  └───────────────────┘  └────────┬─────────┘  └────────┬─────────┘     │
│                                  │                     │                │
│  ┌───────────────────────────────┴─────────────────────┴───────────────┐│
│  │                      SQLAlchemy Async                                ││
│  └──────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────┤
│              PostgreSQL                          Redis Addon            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     ┌──────────────┐        │
│  │  Users   │  │ Images   │  │ Metrics  │     │ Horoscope    │        │
│  │          │  │ (meta+   │  │ History  │     │ Cache (12h)  │        │
│  │          │  │ file_id) │  │          │     │              │        │
│  └──────────┘  └──────────┘  └──────────┘     └──────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
```

### Новые компоненты v2.0

| Компонент | Назначение | Интеграция |
|-----------|------------|------------|
| Redis Cache | TTL-кэш для гороскопов | Заменяет in-memory cache |
| Image Storage | file_id в PostgreSQL | Новая таблица zodiac_images |
| Pre-generation Job | Фоновая генерация | Расширение APScheduler |
| Prometheus Metrics | Метрики приложения | prometheus-fastapi-instrumentator |
| Metrics History | Исторические данные | Новая таблица metric_snapshots |

---

## Компонент 1: Image Storage + Serving

### Рекомендация: PostgreSQL + Telegram file_id

**Почему НЕ внешний storage (S3, R2):**
1. Telegram принимает изображения по file_id — бесплатно, мгновенно
2. Railway не имеет встроенного blob storage
3. Дополнительный сервис = стоимость + сложность

**Паттерн: Upload Once, Serve by file_id**

```
┌───────────────┐     ┌──────────────┐     ┌─────────────────┐
│ AI генерирует │────>│ Telegram     │────>│ Сохранить       │
│ изображение   │     │ send_photo() │     │ file_id в БД    │
│ (bytes)       │     │              │     │                 │
└───────────────┘     └──────────────┘     └─────────────────┘
                              │
                              v
                      ┌──────────────────┐
                      │ Повторная отправка│
                      │ по file_id       │
                      │ (бесплатно)      │
                      └──────────────────┘
```

### Модель данных

```python
class ZodiacImage(Base):
    """Изображения знаков зодиака."""
    __tablename__ = "zodiac_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    zodiac_sign: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    image_type: Mapped[str] = mapped_column(String(20))  # "daily", "weekly"
    telegram_file_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

### Интеграция с aiogram 3

```python
from aiogram.types import BufferedInputFile

async def send_horoscope_with_image(
    bot: Bot,
    chat_id: int,
    zodiac_sign: str,
    horoscope_text: str,
    session: AsyncSession,
):
    # Получить file_id из БД
    image = await session.scalar(
        select(ZodiacImage).where(ZodiacImage.zodiac_sign == zodiac_sign)
    )

    if image and image.telegram_file_id:
        # Отправить по file_id (быстро, бесплатно)
        await bot.send_photo(
            chat_id=chat_id,
            photo=image.telegram_file_id,
            caption=horoscope_text,
        )
    else:
        await bot.send_message(chat_id=chat_id, text=horoscope_text)
```

### Первоначальная загрузка

```python
async def upload_zodiac_image(
    zodiac_sign: str,
    image_bytes: bytes,
    bot: Bot,
    session: AsyncSession,
    admin_chat_id: int,
):
    photo = BufferedInputFile(file=image_bytes, filename=f"{zodiac_sign}.png")
    message = await bot.send_photo(chat_id=admin_chat_id, photo=photo)
    file_id = message.photo[-1].file_id

    image = ZodiacImage(
        zodiac_sign=zodiac_sign,
        image_type="daily",
        telegram_file_id=file_id,
    )
    session.add(image)
    await session.commit()
    return file_id
```

---

## Компонент 2: Caching Layer

### Рекомендация: Redis addon

**Сравнение Redis vs PostgreSQL UNLOGGED:**

| Критерий | Redis | PostgreSQL UNLOGGED |
|----------|-------|---------------------|
| Latency | ~0.1ms | ~1-2ms |
| TTL support | Нативный | Ручная очистка |
| Complexity | Простой key-value | Требует таблицы |
| Railway cost | ~$5/мес | Включен |

**Вывод:** Для 12 гороскопов Redis упрощает TTL-логику.

### Что кэшировать

| Данные | Key | TTL | Размер |
|--------|-----|-----|--------|
| Дневной гороскоп | `horoscope:{sign}:{date}` | 12h | ~2KB x 12 |
| file_id изображений | `image:{sign}:{type}` | 24h | ~100B x 12 |
| Health status | `health:openrouter` | 5min | ~100B |

### Redis Client

```python
# src/services/redis.py
import redis.asyncio as redis
from src.config import settings

_redis_client: redis.Redis | None = None

async def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client

async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
```

### Кэш гороскопов

```python
# src/services/ai/redis_cache.py
from datetime import date

HOROSCOPE_TTL = 12 * 60 * 60  # 12 hours

async def get_cached_horoscope(sign: str) -> str | None:
    redis = await get_redis()
    key = f"horoscope:{sign}:{date.today().isoformat()}"
    return await redis.get(key)

async def set_cached_horoscope(sign: str, text: str) -> None:
    redis = await get_redis()
    key = f"horoscope:{sign}:{date.today().isoformat()}"
    await redis.setex(key, HOROSCOPE_TTL, text)
```

### Fallback на in-memory

```python
async def get_cached_horoscope(sign: str) -> str | None:
    try:
        redis = await get_redis()
        return await redis.get(f"horoscope:{sign}:{date.today().isoformat()}")
    except Exception:
        from src.services.ai.cache import get_cached_horoscope as memory_cache
        return await memory_cache(sign)
```

---

## Компонент 3: Background Jobs

### Рекомендация: Расширить APScheduler

**Почему НЕ Celery:**
- Celery требует отдельный worker (отдельный Railway service)
- Для 12 гороскопов каждые 12 часов — overkill
- APScheduler с SQLAlchemyJobStore уже работает

### Новые jobs

```python
# src/services/scheduler.py

def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        # ... existing setup ...

        # Pre-generation job
        _scheduler.add_job(
            pregenerate_horoscopes,
            CronTrigger(hour="0,12", minute=5, timezone="Europe/Moscow"),
            id="pregenerate_horoscopes",
            replace_existing=True,
            misfire_grace_time=3600,
        )

        # Metrics collection job
        _scheduler.add_job(
            collect_daily_metrics,
            CronTrigger(hour=23, minute=55, timezone="Europe/Moscow"),
            id="collect_daily_metrics",
            replace_existing=True,
            misfire_grace_time=3600,
        )

    return _scheduler
```

### Pre-generation

```python
async def pregenerate_horoscopes() -> None:
    """Pre-generate all 12 horoscopes."""
    from src.services.ai.client import generate_horoscope
    from src.services.ai.redis_cache import set_cached_horoscope
    from src.bot.utils.zodiac import ZODIAC_SIGNS

    await logger.ainfo("Starting horoscope pre-generation")

    for sign in ZODIAC_SIGNS:
        try:
            text = await generate_horoscope(sign)
            await set_cached_horoscope(sign, text)
            await logger.ainfo("Generated horoscope", sign=sign)
        except Exception as e:
            await logger.aerror("Failed to generate", sign=sign, error=str(e))

    await logger.ainfo("Pre-generation complete")
```

### Graceful degradation

```python
async def get_horoscope(sign: str) -> str:
    # 1. Try cache
    cached = await get_cached_horoscope(sign)
    if cached:
        return cached

    # 2. Generate on-demand
    text = await generate_horoscope(sign)
    await set_cached_horoscope(sign, text)
    return text
```

---

## Компонент 4: Monitoring

### Prometheus Metrics

```python
# src/main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(lifespan=lifespan)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

**Встроенные метрики:**
- `http_requests_total` — counter по handler/status/method
- `http_request_size_bytes` — размер запросов
- `http_response_size_bytes` — размер ответов
- `http_request_duration_seconds` — latency

### Custom Business Metrics

```python
# src/services/metrics.py
from prometheus_client import Counter, Gauge, Histogram

HOROSCOPES_GENERATED = Counter(
    "horoscopes_generated_total",
    "Total horoscopes generated",
    ["sign", "source"],  # source: "cache" | "generated"
)

ACTIVE_SUBSCRIBERS = Gauge(
    "active_subscribers",
    "Current number of active premium subscribers",
)

API_COST_CENTS = Counter(
    "api_cost_cents_total",
    "Total API cost in cents",
    ["provider", "model"],
)

AI_REQUEST_LATENCY = Histogram(
    "ai_request_latency_seconds",
    "AI API request latency",
    ["provider"],
    buckets=[0.5, 1, 2, 5, 10, 30],
)
```

### OpenRouter Cost Tracking

```python
async def generate_with_tracking(prompt: str) -> tuple[str, dict]:
    response = await openrouter_client.chat.completions.create(...)

    usage = response.usage
    if usage:
        cost_cents = int(getattr(usage, "cost", 0) * 100)
        API_COST_CENTS.labels(provider="openrouter", model=model).inc(cost_cents)

    return response.choices[0].message.content, usage
```

### Extended Health Check

```python
@app.get("/health")
async def health():
    checks = {}

    # Database
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Redis
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    # Scheduler
    scheduler = get_scheduler()
    checks["scheduler"] = "running" if scheduler.running else "stopped"

    overall = "ok" if all(v in ("ok", "running", "configured")
                          for v in checks.values()) else "degraded"

    return {"status": overall, "checks": checks}
```

### Metrics History (PostgreSQL)

```python
class MetricSnapshot(Base):
    """Daily metrics for admin dashboard."""
    __tablename__ = "metric_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(index=True)
    metric_name: Mapped[str] = mapped_column(String(50))
    value: Mapped[float]
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("date", "metric_name", name="uq_metric_date"),
    )
```

---

## Data Flow v2.0

### Horoscope Request Flow

```
User requests horoscope
         │
         v
┌─────────────────┐
│ Check Redis     │─── HIT ──> Return cached + image
│ cache           │
└────────┬────────┘
         │ MISS
         v
┌─────────────────┐
│ Generate via    │
│ OpenRouter      │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Cache in Redis  │
│ (12h TTL)       │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Track metrics   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Send with image │
│ (by file_id)    │
└─────────────────┘
```

### Pre-generation Flow

```
Every 12 hours (00:05, 12:05 MSK)
         │
         v
┌─────────────────┐
│ For each of 12  │
│ zodiac signs    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Generate via    │
│ OpenRouter      │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Store in Redis  │
│ with 12h TTL    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Log metrics     │
└─────────────────┘
```

---

## Integration Points v2.0

### Изменения в существующих файлах

| Файл | Изменение |
|------|-----------|
| `src/config.py` | Добавить `redis_url: str` |
| `src/main.py` | Prometheus instrumentator, расширить /health |
| `src/services/scheduler.py` | Добавить `pregenerate_horoscopes`, `collect_daily_metrics` |
| `src/services/ai/cache.py` | Заменить in-memory на Redis (с fallback) |
| `src/bot/handlers/horoscope.py` | Интегрировать отправку с изображением |
| `pyproject.toml` | Добавить `redis`, `prometheus-fastapi-instrumentator` |

### Новые файлы

| Файл | Назначение |
|------|------------|
| `src/services/redis.py` | Redis client singleton |
| `src/services/metrics.py` | Custom Prometheus metrics |
| `src/db/models/zodiac_image.py` | Модель для file_id изображений |
| `src/db/models/metric_snapshot.py` | Модель для исторических метрик |
| `migrations/versions/xxx_add_zodiac_images.py` | Миграция |
| `migrations/versions/xxx_add_metric_snapshots.py` | Миграция |

### Railway Configuration

```yaml
# Environment variables (Railway UI)
REDIS_URL=redis://default:xxx@redis.railway.internal:6379
```

---

## Anti-Patterns v2.0

### Anti-Pattern 1: Storing Images as Blobs

**Что делают:** Хранят image bytes в BYTEA
**Почему плохо:** Увеличивает БД, медленнее, Telegram уже хранит
**Вместо этого:** Загрузить один раз, хранить только file_id

### Anti-Pattern 2: Celery для простых tasks

**Что делают:** Celery + worker для 12 задач в день
**Почему плохо:** Overkill, дополнительный сервис
**Вместо этого:** APScheduler в том же процессе

### Anti-Pattern 3: Prometheus без persistence

**Что делают:** Только Prometheus, теряют метрики при restart
**Почему плохо:** Railway = ephemeral storage
**Вместо этого:** Daily snapshots в PostgreSQL

### Anti-Pattern 4: Redis для persistent data

**Что делают:** Хранят subscriptions в Redis
**Почему плохо:** Redis = cache, данные могут потеряться
**Вместо этого:** Redis только для TTL-кэша

---

## Build Order v2.0

1. **Redis интеграция** — фундамент для кэширования
2. **Миграция кэша на Redis** — заменить in-memory
3. **Pre-generation job** — scheduled task
4. **Image storage model** — ZodiacImage table
5. **Image upload flow** — admin endpoint
6. **Horoscope + image sending** — интеграция в handlers
7. **Prometheus metrics** — instrumentator
8. **Custom metrics** — бизнес-метрики
9. **Health check расширение** — детальные checks
10. **Metrics history** — daily snapshots
11. **Admin dashboard integration** — графики

**Зависимости:**
- 2 требует 1
- 3 требует 2
- 6 требует 4, 5
- 7-10 независимы от 1-6

---

## Sources v2.0

**Redis vs PostgreSQL caching:**
- [Redis is fast - I'll cache in Postgres](https://dizzy.zone/2025/09/24/Redis-is-fast-Ill-cache-in-Postgres/)
- [I Replaced Redis with PostgreSQL](https://dev.to/polliog/i-replaced-redis-with-postgresql-and-its-faster-4942)

**Telegram file handling:**
- [aiogram 3 File Upload](https://docs.aiogram.dev/en/latest/api/upload_file.html)
- [Telegram Bot API - sendPhoto](https://core.telegram.org/bots/api#sendphoto)

**APScheduler + FastAPI:**
- [Scheduled Jobs with FastAPI and APScheduler](https://ahaw021.medium.com/scheduled-jobs-with-fastapi-and-apscheduler-5a4c50580b0e)

**Prometheus + FastAPI:**
- [prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)

**OpenRouter:**
- [OpenRouter Usage Accounting](https://openrouter.ai/docs/use-cases/usage-accounting)

**Railway:**
- [Railway FastAPI Deployment](https://docs.railway.com/guides/fastapi)

---

# v1.0 Original Architecture (preserved below)

---

## Standard Architecture

### System Overview

```
                            ┌─────────────────────────────────────────────────────────────┐
                            │                    EXTERNAL SERVICES                        │
                            │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
                            │  │  Telegram   │  │  OpenRouter │  │   YooKassa  │         │
                            │  │  Bot API    │  │  (AI/LLM)   │  │  (Payments) │         │
                            │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
                            └─────────┼────────────────┼────────────────┼─────────────────┘
                                      │                │                │
                                      │ Webhook        │ HTTPS          │ Webhook
                                      ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              APPLICATION LAYER (Railway)                                │
│                                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                           FastAPI Application                                    │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │   │
│  │  │  Bot Webhook   │  │ Payment Hook   │  │  Admin API     │  │ Admin Panel  │  │   │
│  │  │  /webhook/bot  │  │ /webhook/pay   │  │  /api/admin/*  │  │ /admin/*     │  │   │
│  │  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘  └──────┬───────┘  │   │
│  └──────────┼───────────────────┼───────────────────┼───────────────────┼──────────┘   │
│             │                   │                   │                   │              │
│             ▼                   ▼                   ▼                   ▼              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                           SERVICE LAYER                                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │   │
│  │  │  Bot Service │  │  AI Service  │  │ Payment Svc  │  │ User Service │         │   │
│  │  │  (aiogram)   │  │ (OpenRouter) │  │ (YooKassa)   │  │              │         │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘         │   │
│  └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                              │
│                                         ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                           DATA LAYER                                             │   │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                   SQLAlchemy + asyncpg                                    │   │   │
│  │  └──────────────────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                              │
└─────────────────────────────────────────┼──────────────────────────────────────────────┘
                                          │
                                          ▼
                            ┌─────────────────────────────┐
                            │      PostgreSQL (Railway)   │
                            │  ┌───────┐ ┌───────┐        │
                            │  │ users │ │ subs  │ ...    │
                            │  └───────┘ └───────┘        │
                            └─────────────────────────────┘
```

### Рекомендация: Модульный Монолит

**Почему монолит, а не микросервисы:**

1. **Масштаб проекта** — Telegram бот с админкой это small-to-medium проект
2. **Команда** — Скорее всего один разработчик или маленькая команда
3. **Скорость запуска** — Нужно быстро валидировать бизнес-модель
4. **Инфраструктура** — Railway проще деплоить один сервис
5. **Стоимость** — Один сервис = один контейнер = дешевле

**Когда пересматривать:**
- Если AI генерация станет узким местом (отделить в отдельный сервис)
- Если нужен отдельный API для мобильного приложения в будущем
- При достижении 100k+ активных пользователей

### Component Responsibilities

| Компонент | Ответственность | Реализация |
|-----------|-----------------|------------|
| **FastAPI App** | HTTP сервер, роутинг, webhooks | FastAPI + Uvicorn |
| **Bot Service** | Обработка Telegram updates, FSM, команды | aiogram 3.x |
| **AI Service** | Генерация интерпретаций, работа с LLM | OpenRouter SDK / httpx |
| **Payment Service** | Создание платежей, обработка webhooks | yookassa SDK |
| **User Service** | Управление пользователями, подписками, лимитами | Бизнес-логика |
| **Admin Panel** | Веб-интерфейс администратора | FastAPI + Jinja2 / React |
| **Data Layer** | ORM, миграции, транзакции | SQLAlchemy 2.0 async |
| **PostgreSQL** | Персистентное хранение | Railway managed PostgreSQL |

## Recommended Project Structure

```
src/
├── main.py                 # Точка входа: FastAPI app + uvicorn
├── config.py               # Pydantic Settings, env vars
│
├── bot/                    # Telegram бот (aiogram)
│   ├── __init__.py
│   ├── bot.py              # Bot instance, Dispatcher setup
│   ├── handlers/           # Обработчики по функционалу
│   │   ├── __init__.py
│   │   ├── start.py        # /start, регистрация
│   │   ├── horoscope.py    # Команды гороскопов
│   │   ├── tarot.py        # Команды таро
│   │   ├── subscription.py # Команды подписки
│   │   └── common.py       # Общие хендлеры
│   ├── middlewares/        # Middleware aiogram
│   │   ├── __init__.py
│   │   ├── auth.py         # Проверка/создание пользователя
│   │   ├── subscription.py # Проверка лимитов подписки
│   │   └── logging.py      # Логирование запросов
│   ├── keyboards/          # Inline и reply клавиатуры
│   │   ├── __init__.py
│   │   └── main.py
│   ├── states/             # FSM состояния
│   │   ├── __init__.py
│   │   └── tarot.py        # Состояния для раскладов
│   └── filters/            # Кастомные фильтры
│       └── __init__.py
│
├── services/               # Бизнес-логика
│   ├── __init__.py
│   ├── ai.py               # OpenRouter интеграция
│   ├── payment.py          # YooKassa интеграция
│   ├── horoscope.py        # Логика гороскопов
│   ├── tarot.py            # Логика таро, колода карт
│   ├── natal.py            # Логика натальных карт
│   └── subscription.py     # Логика подписок и лимитов
│
├── api/                    # FastAPI endpoints
│   ├── __init__.py
│   ├── webhooks/           # Webhook handlers
│   │   ├── __init__.py
│   │   ├── telegram.py     # POST /webhook/telegram
│   │   └── yookassa.py     # POST /webhook/payment
│   └── admin/              # Admin API
│       ├── __init__.py
│       ├── users.py        # CRUD пользователей
│       ├── stats.py        # Аналитика
│       └── broadcasts.py   # Рассылки
│
├── admin/                  # Admin Panel UI
│   ├── __init__.py
│   ├── routes.py           # GET /admin/*
│   └── templates/          # Jinja2 templates
│       ├── base.html
│       ├── dashboard.html
│       ├── users.html
│       └── stats.html
│
├── db/                     # Database layer
│   ├── __init__.py
│   ├── engine.py           # AsyncEngine, session factory
│   ├── models/             # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── subscription.py
│   │   ├── payment.py
│   │   ├── tarot_reading.py
│   │   └── horoscope.py
│   └── repositories/       # Data access layer
│       ├── __init__.py
│       ├── user.py
│       └── subscription.py
│
├── core/                   # Shared utilities
│   ├── __init__.py
│   ├── exceptions.py       # Custom exceptions
│   ├── logging.py          # Logging setup
│   └── constants.py        # Константы (знаки зодиака, карты таро)
│
└── migrations/             # Alembic migrations
    ├── env.py
    ├── versions/
    └── alembic.ini
```

### Structure Rationale

- **bot/** — Изолирует всю Telegram-специфичную логику. aiogram routers регистрируются в `bot.py`
- **services/** — Чистая бизнес-логика без зависимости от транспорта (Telegram/HTTP)
- **api/** — HTTP endpoints отдельно от бота. Webhooks и Admin API
- **admin/** — Админка как отдельный модуль, может быть заменена на React SPA позже
- **db/** — Слой данных изолирован. Repositories скрывают детали ORM от сервисов
- **core/** — Shared код, избегаем circular imports

## Architectural Patterns

### Pattern 1: Webhook-based Bot

**Что:** Telegram бот работает через webhook, а не polling
**Когда использовать:** Production deployment на Railway/Heroku/любой PaaS
**Trade-offs:**
- (+) Мгновенная доставка updates
- (+) Нет idle запросов к Telegram API
- (+) Нативно работает с Railway (есть публичный URL)
- (-) Требуется SSL (Railway предоставляет)
- (-) Сложнее локальная разработка (нужен ngrok)

**Пример:**
```python
# api/webhooks/telegram.py
from fastapi import APIRouter, Request
from aiogram.types import Update
from bot.bot import dp, bot

router = APIRouter()

@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    update = Update.model_validate(await request.json())
    await dp.feed_update(bot, update)
    return {"ok": True}
```

### Pattern 2: Middleware Chain для Auth и Лимитов

**Что:** aiogram middleware для проверки пользователя и лимитов подписки
**Когда использовать:** Любой запрос от пользователя должен проверять auth/лимиты
**Trade-offs:**
- (+) DRY — логика в одном месте
- (+) Чистые handlers — только бизнес-логика
- (-) Сложнее дебажить цепочку

**Пример:**
```python
# bot/middlewares/subscription.py
from aiogram import BaseMiddleware
from aiogram.types import Message

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        user = data["user"]  # Из предыдущего middleware

        # Проверка лимита
        if not await self.check_limit(user, action="tarot"):
            await event.answer("Лимит раскладов исчерпан. Оформите подписку!")
            return  # Не вызываем handler

        return await handler(event, data)
```

### Pattern 3: Repository Pattern для Data Access

**Что:** Репозитории абстрагируют доступ к данным
**Когда использовать:** Когда бизнес-логика не должна знать о SQLAlchemy
**Trade-offs:**
- (+) Легко тестировать (mock repositories)
- (+) Можно сменить ORM/БД
- (-) Дополнительный слой кода

**Пример:**
```python
# db/repositories/user.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create(self, telegram_id: int, username: str | None) -> User:
        user = User(telegram_id=telegram_id, username=username)
        self.session.add(user)
        await self.session.commit()
        return user
```

### Pattern 4: Service Layer для AI

**Что:** AI сервис инкапсулирует всю работу с OpenRouter
**Когда использовать:** Любая генерация контента через LLM
**Trade-offs:**
- (+) Единая точка для промптов, retry logic, rate limiting
- (+) Легко сменить провайдера (OpenAI, Anthropic)
- (-) Нужно продумать async правильно

**Пример:**
```python
# services/ai.py
from openrouter import OpenRouter
from config import settings

class AIService:
    def __init__(self):
        self.client = OpenRouter(api_key=settings.OPENROUTER_API_KEY)

    async def generate_tarot_interpretation(
        self,
        cards: list[str],
        question: str,
        spread_type: str
    ) -> str:
        prompt = self._build_tarot_prompt(cards, question, spread_type)

        async with self.client as client:
            response = await client.chat.send_async(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": prompt}]
            )
        return response.choices[0].message.content

    def _build_tarot_prompt(self, cards, question, spread_type) -> str:
        # Промпт для интерпретации
        ...
```

## Data Flow

### Flow 1: Пользователь запрашивает расклад таро

```
User (Telegram)
    │
    │ "Сделай расклад на любовь"
    ▼
┌─────────────────┐
│ Telegram API    │
│ (webhook POST)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ FastAPI         │
│ /webhook/tg     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ aiogram         │
│ Dispatcher      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Middleware Chain                        │
│ 1. AuthMiddleware → load/create user    │
│ 2. SubscriptionMiddleware → check limit │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ TarotHandler    │────▶│ TarotService    │
│                 │     │ - draw_cards()  │
└─────────────────┘     │ - save_reading()│
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ AIService       │
                        │ generate_inter- │
                        │ pretation()     │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ OpenRouter API  │
                        │ (Claude 3.5)    │
                        └────────┬────────┘
                                 │
                                 ▼
┌─────────────────┐     ┌─────────────────┐
│ User (Telegram) │◀────│ Format & Send   │
│ Красивый ответ  │     │ with cards      │
└─────────────────┘     └─────────────────┘
```

### Flow 2: Оплата подписки

```
User (Telegram)
    │
    │ "Оформить подписку"
    ▼
┌─────────────────┐
│ Bot Handler     │
│ /subscribe      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ PaymentService  │────▶│ YooKassa API    │
│ create_payment()│     │ Create Payment  │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │◀──────────────────────┘
         │ payment_url
         ▼
┌─────────────────┐
│ Send to User    │
│ "Оплатите: URL" │
└─────────────────┘
         │
         │ User pays on YooKassa page
         │
         ▼
┌─────────────────┐
│ YooKassa        │
│ payment.succeed │
└────────┬────────┘
         │
         │ POST /webhook/payment
         ▼
┌─────────────────┐
│ FastAPI         │
│ PaymentWebhook  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PaymentService  │
│ - verify_sign() │
│ - activate_sub()│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DB: Update      │
│ subscription    │
│ status=active   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Bot: Send       │
│ "Подписка актив"│
└─────────────────┘
```

### Flow 3: Админ смотрит статистику

```
Admin (Browser)
    │
    │ GET /admin/dashboard
    ▼
┌─────────────────┐
│ FastAPI         │
│ Admin Routes    │
└────────┬────────┘
         │
         │ Check admin auth (cookie/session)
         ▼
┌─────────────────┐
│ StatsService    │
│ - get_users()   │
│ - get_revenue() │
│ - get_funnel()  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DB: Aggregate   │
│ queries         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Render template │
│ dashboard.html  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Admin (Browser) │
│ Dashboard view  │
└─────────────────┘
```

## Scaling Considerations

| Scale | Архитектурные решения |
|-------|----------------------|
| 0-1k users | Монолит достаточен. Один Railway сервис + PostgreSQL. Redis не нужен |
| 1k-10k users | Добавить Redis для кэширования AI ответов (одинаковые гороскопы). Оптимизировать промпты |
| 10k-100k users | Отдельный воркер для AI генерации (очередь). Rate limiting на OpenRouter |
| 100k+ users | Выделить AI в отдельный сервис. Рассмотреть шардирование БД. CDN для статики админки |

### Scaling Priorities

1. **Первое узкое место:** OpenRouter API latency и стоимость
   - Кэшировать ежедневные гороскопы (одинаковые для всех)
   - Batch генерация гороскопов раз в сутки по cron

2. **Второе узкое место:** PostgreSQL connections
   - Connection pooling (asyncpg уже делает)
   - Read replicas если нужны тяжёлые аналитические запросы

3. **Третье узкое место:** Webhook throughput
   - Railway auto-scaling
   - Очередь для тяжёлых операций (AI генерация)

## Anti-Patterns

### Anti-Pattern 1: Polling в Production

**Что делают:** Используют `bot.polling()` на Railway
**Почему плохо:**
- Постоянные запросы к Telegram API (waste of resources)
- Задержка доставки updates
- Не работает с Railway sleep (бот "засыпает")
**Правильно:** Webhook. Railway даёт публичный HTTPS URL бесплатно

### Anti-Pattern 2: Синхронная БД в async приложении

**Что делают:** Используют `psycopg2` или синхронный SQLAlchemy
**Почему плохо:**
- Блокирует event loop
- Один медленный запрос замораживает весь бот
**Правильно:** `asyncpg` + SQLAlchemy async. Все операции `await`

### Anti-Pattern 3: AI вызовы в хендлере без timeout

**Что делают:** `await ai.generate()` без таймаута
**Почему плохо:**
- OpenRouter может ответить за 30+ секунд
- Telegram ждёт ответ, пользователь думает бот завис
**Правильно:**
```python
# Отправить "Генерирую..." сначала
await message.answer("Генерирую интерпретацию...")
# Потом генерировать
interpretation = await ai_service.generate(...)
await message.answer(interpretation)
```

### Anti-Pattern 4: Хранение состояния в памяти

**Что делают:** `user_data = {}` глобальный dict для FSM
**Почему плохо:**
- Теряется при рестарте (Railway рестартит часто)
- Не работает с несколькими инстансами
**Правильно:** FSM storage в Redis или PostgreSQL

### Anti-Pattern 5: Webhook без верификации

**Что делают:** Принимают любой POST на `/webhook/payment`
**Почему плохо:**
- Любой может отправить fake payment notification
- Мошенничество с подписками
**Правильно:** Верифицировать signature от YooKassa

## Integration Points

### External Services

| Сервис | Паттерн интеграции | Gotchas |
|--------|-------------------|---------|
| **Telegram Bot API** | Webhook на `/webhook/telegram` | Порты: 443, 80, 88, 8443. Secret token в header |
| **OpenRouter** | Async HTTP client | Rate limits. Timeout 60s+. Кэшировать где возможно |
| **YooKassa** | SDK + Webhook на `/webhook/payment` | Верификация подписи обязательна. Idempotency key |
| **PostgreSQL** | SQLAlchemy async + asyncpg | Connection pool. `pool_pre_ping=True` |

### Internal Boundaries

| Граница | Коммуникация | Notes |
|---------|--------------|-------|
| **Bot ↔ Services** | Direct Python calls | Инъекция зависимостей через middleware |
| **Services ↔ DB** | Repository pattern | Сервисы не знают о SQLAlchemy напрямую |
| **API ↔ Services** | Direct Python calls | Shared service instances |
| **Admin ↔ DB** | Repository pattern | Те же репозитории что и для бота |

## Deployment на Railway

### Структура Railway

```
Railway Project
├── Service: adtrobot (main)     # Python app
│   ├── Dockerfile / nixpacks
│   ├── Environment variables
│   └── Public domain (*.up.railway.app)
│
└── Plugin: PostgreSQL           # Managed DB
    └── Auto-injected DATABASE_URL
```

### Environment Variables

```bash
# Railway auto-injects
DATABASE_URL=postgresql://...

# Manual configuration
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_WEBHOOK_SECRET=random-string-for-verification
OPENROUTER_API_KEY=sk-or-...
YOOKASSA_SHOP_ID=123456
YOOKASSA_SECRET_KEY=test_...
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-password
```

### Railway-specific Notes

1. **Webhook URL:** Railway предоставляет `https://app-name.up.railway.app`. Использовать для Telegram webhook.
2. **Port:** Railway задаёт `PORT` env var. Слушать на нём.
3. **Health Check:** Добавить `/health` endpoint для Railway мониторинга
4. **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Порядок Сборки (Build Order)

На основе зависимостей между компонентами:

### Phase 1: Core Infrastructure
1. **Настройка проекта** — pyproject.toml, структура папок
2. **Database models** — SQLAlchemy модели (User, Subscription, Payment)
3. **Database engine** — Async engine, session factory
4. **Alembic migrations** — Базовые миграции
5. **Config** — Pydantic Settings

*Rationale:* БД это фундамент. Все остальное от неё зависит.

### Phase 2: Bot Core
1. **Bot instance** — aiogram Bot, Dispatcher
2. **FastAPI app** — Базовое приложение
3. **Webhook endpoint** — `/webhook/telegram`
4. **Auth middleware** — Создание/загрузка пользователя
5. **Basic handlers** — `/start`, help

*Rationale:* Минимально работающий бот. Можно деплоить и тестировать.

### Phase 3: Free Features
1. **Tarot service** — Колода карт, логика раскладов
2. **AI service** — OpenRouter интеграция
3. **Horoscope service** — Генерация гороскопов
4. **Tarot handlers** — Команды раскладов
5. **Horoscope handlers** — Команды гороскопов
6. **Subscription middleware** — Проверка лимитов

*Rationale:* Бесплатный функционал для привлечения пользователей.

### Phase 4: Payments
1. **YooKassa integration** — SDK setup
2. **Payment service** — Создание платежей
3. **Payment webhook** — `/webhook/payment`
4. **Subscription handlers** — `/subscribe`, статус подписки
5. **Subscription management** — Активация, продление, отмена

*Rationale:* Монетизация. Требует рабочего бота и юзеров.

### Phase 5: Premium Features
1. **Natal chart service** — Расчёт и интерпретация
2. **Advanced tarot** — Кельтский крест
3. **Detailed horoscopes** — По сферам жизни
4. **Premium handlers** — Команды для платных функций

*Rationale:* Ценность для платных подписчиков.

### Phase 6: Admin Panel
1. **Admin auth** — Basic auth или сессии
2. **Dashboard** — Основные метрики
3. **User management** — Список, поиск, детали
4. **Analytics** — Воронка, retention
5. **Broadcasts** — Рассылки пользователям

*Rationale:* Админка нужна когда есть что администрировать.

## Sources

**Aiogram:**
- [Aiogram Official Documentation](https://docs.aiogram.dev/)
- [Aiogram GitHub](https://github.com/aiogram/aiogram)
- [Aiogram FSM Documentation](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/index.html)
- [Aiogram Middlewares](https://docs.aiogram.dev/en/dev-3.x/dispatcher/middlewares.html)

**YooKassa:**
- [YooKassa Python SDK](https://github.com/yoomoney/yookassa-sdk-python)
- [YooKassa Webhooks](https://yookassa.ru/developers/using-api/webhooks)
- [Async YooKassa Library](https://pypi.org/project/aioyookassa/)

**OpenRouter:**
- [OpenRouter Quickstart](https://openrouter.ai/docs/quickstart)
- [OpenRouter Python SDK](https://openrouter.ai/docs/sdks/python/overview)

**SQLAlchemy Async:**
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI + SQLAlchemy Async Best Practices](https://leapcell.io/blog/building-high-performance-async-apis-with-fastapi-sqlalchemy-2-0-and-asyncpg)

**FastAPI Admin:**
- [FastAdmin](https://github.com/vsdudakov/fastadmin)
- [FastAPI Admin](https://github.com/fastapi-admin/fastapi-admin)

**Railway:**
- [Railway Python Telegram Bot Templates](https://railway.com/deploy/a0ln90)
- [Railway Telegram Bot Infrastructure](https://station.railway.com/questions/telegram-bot-infrastructure-a3268f8a)

**Telegram Bot API:**
- [Telegram Bot Payments](https://core.telegram.org/bots/payments)
- [Telegram Bot API](https://core.telegram.org/bots/api)

**Architecture:**
- [Monolith vs Microservices for Python](https://opsmatters.com/posts/monolith-or-microservices-architecture-choices-python-developers)
- [Telegram Bot Development Guide 2025](https://wnexus.io/the-complete-guide-to-telegram-bot-development-in-2025/)

---
*Architecture research for: AdtroBot — Telegram бот гороскопов и таро*
*Researched: 2026-01-22 (v1.0), 2026-01-23 (v2.0)*
