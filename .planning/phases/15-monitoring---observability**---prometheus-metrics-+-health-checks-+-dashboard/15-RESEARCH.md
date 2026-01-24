# Phase 15: Monitoring & Observability - Research

**Researched:** 2026-01-24
**Domain:** Python/FastAPI Monitoring, Prometheus Metrics, Health Checks, Dashboard Visualization
**Confidence:** HIGH

## Summary

Исследование охватывает четыре ключевых области: Prometheus metrics интеграция в FastAPI, health check endpoints для Kubernetes/Railway, OpenRouter API cost tracking, и dashboard визуализация на React с Recharts.

Для Prometheus интеграции существует зрелая библиотека `prometheus-fastapi-instrumentator` (v7.1.0), которая автоматически добавляет стандартные HTTP метрики и позволяет создавать custom metrics с prefix. Health checks реализуются через стандартные FastAPI endpoints с проверками DB, scheduler, и внешних API. OpenRouter предоставляет встроенный usage tracking через response `usage` field и `/api/v1/generation` endpoint для точных данных о стоимости.

Существующий стек проекта (FastAPI, SQLAlchemy async, APScheduler, React + Recharts + Ant Design) полностью совместим с требованиями фазы без необходимости добавления новых major зависимостей.

**Primary recommendation:** Использовать `prometheus-fastapi-instrumentator` для базовых HTTP метрик + `prometheus-client` для custom business metrics с prefix `adtrobot_*`. Health checks реализовать как sync проверки с timeout. Cost tracking через сохранение OpenRouter response data в БД.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| prometheus-fastapi-instrumentator | 7.1.0 | Автоматические HTTP метрики для FastAPI | 1.4k stars, активно поддерживается, zero-config setup |
| prometheus-client | 0.24.1 | Custom metrics (Counter, Gauge, Histogram) | Официальный Python client от Prometheus |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| recharts | 3.7.0 | Графики в React dashboard | Уже в проекте, идеален для time series |
| antd | 5.29.3 | UI компоненты для dashboard | Уже в проекте, включает Alert для warnings |
| dayjs | 1.11.19 | Работа с датами и time filters | Уже в проекте |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| prometheus-fastapi-instrumentator | prometheus-client + make_asgi_app | Больше boilerplate, но полный контроль |
| Хранение метрик в PostgreSQL | TimescaleDB | Overkill для текущего объема, усложняет деплой |
| Recharts | Chart.js | Recharts уже в проекте, нет смысла менять |

**Installation:**
```bash
pip install prometheus-fastapi-instrumentator prometheus-client
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── monitoring/
│   ├── __init__.py
│   ├── metrics.py           # Custom Prometheus metrics definitions
│   ├── health.py            # Health check logic
│   └── cost_tracking.py     # OpenRouter cost tracking
├── admin/
│   ├── services/
│   │   └── monitoring.py    # Dashboard data aggregation
│   └── router.py            # Add /monitoring endpoints
admin-frontend/
└── src/
    └── pages/
        └── Monitoring.tsx   # New monitoring dashboard page
```

### Pattern 1: Prometheus Metrics Registration
**What:** Регистрация custom metrics при старте приложения
**When to use:** Для всех custom business metrics
**Example:**
```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Gauge, Histogram

# Naming convention: adtrobot_<type>_<name>_<unit>
REQUESTS_TOTAL = Counter(
    "adtrobot_requests_total",
    "Total HTTP requests",
    labelnames=["handler", "method", "status"]
)

ERRORS_TOTAL = Counter(
    "adtrobot_errors_total",
    "Total errors",
    labelnames=["handler", "error_type"]
)

AI_REQUEST_DURATION = Histogram(
    "adtrobot_ai_request_duration_seconds",
    "AI request duration in seconds",
    labelnames=["operation", "model"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)

AI_TOKENS_TOTAL = Counter(
    "adtrobot_ai_tokens_total",
    "Total AI tokens used",
    labelnames=["operation", "model", "token_type"]  # token_type: prompt/completion
)

AI_COST_TOTAL = Counter(
    "adtrobot_ai_cost_dollars_total",
    "Total AI cost in dollars",
    labelnames=["operation", "model"]
)

ACTIVE_USERS = Gauge(
    "adtrobot_active_users",
    "Active users count",
    labelnames=["period"]  # dau/wau/mau
)

QUEUE_DEPTH = Gauge(
    "adtrobot_queue_depth",
    "Background queue depth",
    labelnames=["status"]  # pending/failed/completed
)
```

### Pattern 2: Health Check with Timeouts
**What:** Отдельные проверки с разными timeout
**When to use:** Для /health endpoint
**Example:**
```python
# src/monitoring/health.py
import asyncio
from dataclasses import dataclass
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

@dataclass
class HealthCheckResult:
    name: str
    healthy: bool
    message: str | None = None
    latency_ms: float | None = None

async def check_database(session: AsyncSession, timeout: float = 3.0) -> HealthCheckResult:
    """Check database connection with timeout."""
    import time
    start = time.monotonic()
    try:
        await asyncio.wait_for(
            session.execute(text("SELECT 1")),
            timeout=timeout
        )
        latency = (time.monotonic() - start) * 1000
        return HealthCheckResult("database", True, latency_ms=latency)
    except asyncio.TimeoutError:
        return HealthCheckResult("database", False, "Timeout")
    except Exception as e:
        return HealthCheckResult("database", False, str(e))

async def check_scheduler() -> HealthCheckResult:
    """Check APScheduler status."""
    from src.services.scheduler import get_scheduler
    scheduler = get_scheduler()
    if scheduler.running:
        jobs_count = len(scheduler.get_jobs())
        return HealthCheckResult("scheduler", True, f"{jobs_count} jobs scheduled")
    return HealthCheckResult("scheduler", False, "Scheduler not running")

async def check_openrouter(timeout: float = 10.0) -> HealthCheckResult:
    """Check OpenRouter API availability."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get("https://openrouter.ai/api/v1/models")
            if resp.status_code == 200:
                return HealthCheckResult("openrouter", True)
            return HealthCheckResult("openrouter", False, f"Status {resp.status_code}")
    except Exception as e:
        return HealthCheckResult("openrouter", False, str(e))

async def check_telegram_bot(timeout: float = 10.0) -> HealthCheckResult:
    """Check Telegram Bot API."""
    from src.bot.bot import get_bot
    from src.config import settings
    if not settings.telegram_bot_token:
        return HealthCheckResult("telegram", True, "Token not configured")
    try:
        bot = get_bot()
        me = await asyncio.wait_for(bot.get_me(), timeout=timeout)
        return HealthCheckResult("telegram", True, f"@{me.username}")
    except Exception as e:
        return HealthCheckResult("telegram", False, str(e))
```

### Pattern 3: OpenRouter Cost Tracking
**What:** Извлечение cost data из OpenRouter response
**When to use:** После каждого AI запроса
**Example:**
```python
# src/monitoring/cost_tracking.py
from dataclasses import dataclass

@dataclass
class AIUsageRecord:
    user_id: int
    operation: str  # horoscope, tarot, natal_chart
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_dollars: float | None
    generation_id: str | None

def extract_usage_from_response(
    response,
    user_id: int,
    operation: str,
) -> AIUsageRecord:
    """Extract usage data from OpenRouter/OpenAI response."""
    usage = response.usage
    # OpenRouter может включать cost в x_openrouter field
    cost = getattr(response, "x_openrouter", {}).get("cost")
    gen_id = getattr(response, "id", None)

    return AIUsageRecord(
        user_id=user_id,
        operation=operation,
        model=response.model,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
        cost_dollars=cost,
        generation_id=gen_id,
    )
```

### Pattern 4: Instrumentator Setup with Custom Metrics
**What:** Интеграция prometheus-fastapi-instrumentator в main.py
**When to use:** При старте FastAPI app
**Example:**
```python
# src/main.py
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import make_asgi_app

# Create instrumentator with custom settings
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/metrics"],
    inprogress_name="adtrobot_requests_in_progress",
    inprogress_labels=True,
)

# In lifespan or app creation
instrumentator.instrument(app)

# Mount /metrics endpoint (no auth per CONTEXT.md)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

### Anti-Patterns to Avoid
- **Cascade health checks:** Не вызывать health check одного сервиса из другого - это приводит к каскадным failures
- **Blocking health checks:** Не использовать sync database calls в async health endpoint без timeout
- **Exposing secrets in /health:** Не показывать connection strings или tokens в health response
- **Metrics cardinality explosion:** Не использовать user_id как label в Prometheus (огромная кардинальность)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP metrics collection | Custom middleware | prometheus-fastapi-instrumentator | Handles all edge cases, tested |
| Prometheus exposition format | Custom formatter | prometheus-client make_asgi_app | Standard format, multiprocess support |
| Time series charts | Custom canvas/SVG | Recharts (already in project) | React-native, handles updates |
| Cost calculation | Manual token counting | OpenRouter usage field | Native tokenizer, accurate pricing |

**Key insight:** Prometheus ecosystem очень зрелый. Custom solutions будут менее точными и потребуют больше maintenance.

## Common Pitfalls

### Pitfall 1: High Cardinality Labels
**What goes wrong:** Использование user_id, request_id как label в Prometheus
**Why it happens:** Кажется логичным отслеживать по пользователю
**How to avoid:** User-level tracking делать в PostgreSQL, Prometheus только для aggregated metrics
**Warning signs:** Количество time series растет пропорционально пользователям

### Pitfall 2: Blocking in Async Context
**What goes wrong:** Sync database call в async health check без timeout
**Why it happens:** Забывают про asyncio.wait_for
**How to avoid:** Всегда wrap external calls в asyncio.wait_for с timeout
**Warning signs:** Health check "hangs" при проблемах с DB

### Pitfall 3: Stale Gauge Values
**What goes wrong:** Gauge показывает устаревшие значения
**Why it happens:** Gauge не обновляется автоматически
**How to avoid:** Использовать callback functions или обновлять при каждом scrape
**Warning signs:** Метрики не меняются при изменении реального состояния

### Pitfall 4: Cost Tracking Without Fallback
**What goes wrong:** Полагаться только на OpenRouter cost field
**Why it happens:** Не все модели возвращают cost
**How to avoid:** Fallback на вычисление: tokens * price_per_token
**Warning signs:** cost = None для некоторых операций

### Pitfall 5: Health Check Cascading Failures
**What goes wrong:** Health check возвращает unhealthy при любой проблеме
**Why it happens:** Одна проверка падает -> весь сервис marked unhealthy
**How to avoid:** Различать liveness (app running) и readiness (can serve traffic)
**Warning signs:** Частые рестарты при временных проблемах с external API

## Code Examples

### Complete Health Endpoint
```python
# Source: Pattern from FastAPI best practices + SQLAlchemy docs
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

@app.get("/health")
async def health_check(
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """
    Comprehensive health check.
    Returns 200 if all checks pass, 503 if any fails.
    """
    checks = await asyncio.gather(
        check_database(session, timeout=3.0),
        check_scheduler(),
        check_openrouter(timeout=10.0),
        check_telegram_bot(timeout=10.0),
    )

    all_healthy = all(c.healthy for c in checks)

    response_data = {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": {
            c.name: {
                "healthy": c.healthy,
                "message": c.message,
                "latency_ms": c.latency_ms,
            }
            for c in checks
        }
    }

    return JSONResponse(
        content=response_data,
        status_code=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )
```

### Recording AI Metrics
```python
# Source: prometheus-client documentation + OpenRouter API
import time
from src.monitoring.metrics import AI_REQUEST_DURATION, AI_TOKENS_TOTAL, AI_COST_TOTAL

async def generate_with_metrics(
    operation: str,
    model: str,
    **kwargs
) -> str | None:
    """Generate AI response and record metrics."""
    start = time.monotonic()

    try:
        response = await self.client.chat.completions.create(
            model=model,
            **kwargs
        )
        duration = time.monotonic() - start

        # Record duration
        AI_REQUEST_DURATION.labels(
            operation=operation,
            model=model
        ).observe(duration)

        # Record tokens
        usage = response.usage
        AI_TOKENS_TOTAL.labels(
            operation=operation,
            model=model,
            token_type="prompt"
        ).inc(usage.prompt_tokens)

        AI_TOKENS_TOTAL.labels(
            operation=operation,
            model=model,
            token_type="completion"
        ).inc(usage.completion_tokens)

        # Record cost if available
        cost = getattr(response, "x_openrouter", {}).get("cost")
        if cost:
            AI_COST_TOTAL.labels(
                operation=operation,
                model=model
            ).inc(cost)

        return response.choices[0].message.content

    except Exception as e:
        ERRORS_TOTAL.labels(
            handler="ai_service",
            error_type=type(e).__name__
        ).inc()
        raise
```

### Dashboard Time Filter Component
```typescript
// Source: Existing project patterns + Ant Design
import { Segmented } from 'antd'
import { useState } from 'react'

type TimeRange = '24h' | '7d' | '30d'

interface TimeFilterProps {
  value: TimeRange
  onChange: (value: TimeRange) => void
}

const TimeFilter = ({ value, onChange }: TimeFilterProps) => (
  <Segmented
    value={value}
    onChange={(v) => onChange(v as TimeRange)}
    options={[
      { label: '24 часа', value: '24h' },
      { label: '7 дней', value: '7d' },
      { label: '30 дней', value: '30d' },
    ]}
  />
)
```

### API Cost Table Schema
```python
# Source: SQLAlchemy patterns from existing project
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from src.db.models.base import Base

class AIUsage(Base):
    __tablename__ = "ai_usage"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    operation = Column(String(50), index=True)  # horoscope, tarot, natal_chart
    model = Column(String(100))
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    cost_dollars = Column(Float, nullable=True)
    generation_id = Column(String(100), nullable=True)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| @app.on_event("startup") | Lifespan context manager | FastAPI 0.95+ | Чище, await-friendly |
| Custom /metrics formatting | prometheus_client.make_asgi_app | Always preferred | Standard format |
| Sync health checks | Async with timeout | Best practice | Non-blocking |
| Manual token counting | OpenRouter usage field | OpenRouter feature | More accurate |

**Deprecated/outdated:**
- `@app.on_event("startup")` - заменен на lifespan (проект уже использует lifespan)
- `should_group_untemplated` в instrumentator - переименован в `should_ignore_untemplated`

## Open Questions

1. **OpenRouter cost precision**
   - What we know: API возвращает cost в некоторых ответах, но не всегда
   - What's unclear: Когда именно cost доступен vs когда нужен fallback
   - Recommendation: Implement fallback на token * price calculation, log когда cost отсутствует

2. **Multiprocess metrics in Railway**
   - What we know: Railway может запускать несколько workers
   - What's unclear: Используется ли multiprocess mode в текущем деплое
   - Recommendation: Проверить Railway config, возможно нужен MultiProcessCollector

3. **WAU calculation method**
   - What we know: DAU/MAU через TarotSpread как proxy активности
   - What's unclear: Достаточно ли tarot spreads для WAU или нужны другие события
   - Recommendation: Добавить tracking для horoscope views тоже (horoscope_views table существует)

## Sources

### Primary (HIGH confidence)
- [prometheus-fastapi-instrumentator GitHub](https://github.com/trallnag/prometheus-fastapi-instrumentator) - v7.1.0, basic setup, custom metrics
- [prometheus-client Python](https://github.com/prometheus/client_python) - v0.24.1, Counter/Gauge/Histogram API
- [Prometheus Python Client Docs](https://prometheus.github.io/client_python/) - FastAPI integration, multiprocess

### Secondary (MEDIUM confidence)
- [OpenRouter API Docs](https://openrouter.ai/docs/api/reference/overview) - Usage field structure, generation endpoint
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html) - Pre-ping, health check patterns
- [FastAPI Health Check Best Practices](https://www.index.dev/blog/how-to-implement-health-check-in-python) - Liveness/readiness separation

### Tertiary (LOW confidence)
- WebSearch results on dashboard patterns, time filter UX - Validated against existing project code

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official documentation, PyPI verified versions
- Architecture: HIGH - Patterns from official docs + existing project structure
- Pitfalls: MEDIUM - Community best practices, some from experience
- Cost tracking: MEDIUM - OpenRouter docs partially incomplete on cost field availability

**Research date:** 2026-01-24
**Valid until:** 2026-02-24 (30 days - stable domain)
