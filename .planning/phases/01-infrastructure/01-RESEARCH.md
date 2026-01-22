# Phase 1: Infrastructure - Research

**Researched:** 2026-01-22
**Domain:** PostgreSQL + SQLAlchemy async + Alembic + Railway deployment + CI/CD
**Confidence:** HIGH

## Summary

Phase 1 создает фундамент для Telegram бота: PostgreSQL база данных на Railway, async SQLAlchemy ORM с asyncpg драйвером, Alembic миграции с автогенерацией, и автоматический CI/CD через GitHub Actions. Все компоненты уже выбраны в CONTEXT.md — исследование фокусируется на правильной конфигурации и паттернах.

Ключевые решения:
- **SQLAlchemy 2.0 async** с `async_sessionmaker` и `expire_on_commit=False`
- **Alembic** с async template и naming convention для constraints
- **Poetry** для dependency management (pyproject.toml, lock file)
- **pydantic-settings** для environment variables
- **Railway** auto-deploy через GitHub push + Wait for CI

**Primary recommendation:** Настроить минимальную работающую инфраструктуру с правильными defaults — connection pooling, naming conventions, structured logging — чтобы избежать рефакторинга позже.

## Standard Stack

### Core (Phase 1)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **Python** | 3.11+ | Runtime | Стабильная async поддержка, совместимость с Railway Nixpacks |
| **SQLAlchemy** | 2.0.46 | Async ORM | Зрелый, async из коробки, Alembic интеграция |
| **asyncpg** | 0.31.0 | PostgreSQL driver | Самый быстрый async драйвер для PostgreSQL |
| **Alembic** | 1.18.1 | Migrations | Стандарт для SQLAlchemy, autogenerate |
| **pydantic-settings** | 2.7.1 | Config | Type-safe env vars, .env поддержка |
| **structlog** | 25.5.0 | Logging | Structured JSON logs, async-friendly |
| **uvicorn** | 0.40.0 | ASGI Server | Production сервер для Railway |
| **Poetry** | 2.0+ | Package manager | Lock files, deterministic builds |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **python-dotenv** | 1.0.1 | .env loading | Локальная разработка |
| **greenlet** | 3.1.1 | SQLAlchemy async | Автоматически ставится с SQLAlchemy[asyncio] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Poetry | pip + requirements.txt | Poetry: lock file, dependency resolution; pip: проще но менее надежно |
| structlog | stdlib logging | structlog: JSON, context vars; stdlib: zero dependencies |
| pydantic-settings | python-decouple | pydantic: type validation; decouple: simpler |

**Installation (pyproject.toml dependencies):**
```toml
[project]
dependencies = [
    "sqlalchemy[asyncio]>=2.0.46",
    "asyncpg>=0.31.0",
    "alembic>=1.18.1",
    "pydantic-settings>=2.7.1",
    "structlog>=25.5.0",
    "uvicorn[standard]>=0.40.0",
    "python-dotenv>=1.0.1",
]
```

## Architecture Patterns

### Recommended Project Structure (Phase 1 scope)

```
src/
├── __init__.py
├── main.py              # Entry point (minimal FastAPI for health check)
├── config.py            # Pydantic Settings
├── db/
│   ├── __init__.py
│   ├── engine.py        # AsyncEngine, async_sessionmaker
│   └── models/
│       ├── __init__.py
│       ├── base.py      # DeclarativeBase with naming convention
│       └── user.py      # User model (minimal for Phase 1)
└── core/
    ├── __init__.py
    └── logging.py       # structlog configuration

migrations/              # Alembic migrations folder
├── env.py              # Async-configured env.py
├── script.py.mako      # Migration template
└── versions/           # Migration files

pyproject.toml          # Poetry config
alembic.ini             # Alembic config
.env.example            # Template for env vars
.gitignore              # Include .env
```

### Pattern 1: Async Session Factory

**What:** Использовать `async_sessionmaker` с `expire_on_commit=False`
**When to use:** Всегда при async SQLAlchemy
**Why:** Предотвращает неявные запросы к БД после commit

```python
# src/db/engine.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # Проверка соединения перед использованием
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # КРИТИЧНО для async
    autocommit=False,
    autoflush=False,
)

async def get_session() -> AsyncSession:
    """Dependency для FastAPI / middleware для aiogram."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Pattern 2: Naming Convention for Constraints

**What:** Явные имена для всех constraints (PK, FK, IX, UQ, CK)
**When to use:** Всегда — с первой миграции
**Why:** Без имён невозможно дропнуть constraint в миграции

```python
# src/db/models/base.py
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Стандартная naming convention
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)
```

### Pattern 3: Pydantic Settings

**What:** Type-safe конфигурация из environment variables
**When to use:** Всегда для secrets и environment-specific config

```python
# src/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Игнорировать лишние env vars
    )

    # Database
    database_url: str  # postgresql+asyncpg://user:pass@host/db

    # App
    debug: bool = False
    log_level: str = "INFO"

    # Railway auto-injected
    port: int = 8000
    railway_environment: str | None = None

settings = Settings()
```

### Pattern 4: Async Alembic env.py

**What:** Alembic с async engine
**When to use:** Когда используется async SQLAlchemy

```python
# migrations/env.py (ключевые части)
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from src.db.models.base import Base
from src.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Детектить изменения типов колонок
        render_as_batch=True,  # Для SQLite совместимости
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online():
    asyncio.run(run_async_migrations())
```

### Pattern 5: Structured Logging

**What:** JSON логи с context variables
**When to use:** Production для machine-readable logs

```python
# src/core/logging.py
import structlog

def configure_logging(log_level: str = "INFO", json_logs: bool = True):
    """Configure structlog for production or development."""

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(structlog, log_level.upper(), structlog.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

### Anti-Patterns to Avoid

- **`expire_on_commit=True` (default):** Вызывает lazy load после commit — падает в async
- **Анонимные constraints:** Невозможно дропнуть без имени
- **Sync драйвер (psycopg2):** Блокирует event loop
- **Hardcoded DATABASE_URL:** Secrets в коде = утечка
- **`echo=True` в production:** Спам в логах, performance hit

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Environment variables | Custom parser | pydantic-settings | Type validation, .env support, nested config |
| Connection pooling | Manual pool logic | asyncpg built-in / SQLAlchemy pool | Battle-tested, handles edge cases |
| Migration generation | Manual SQL files | Alembic autogenerate | Detects model changes, reversible |
| Constraint naming | Manual names per migration | SQLAlchemy naming_convention | Consistent, automatic |
| Structured logging | Custom JSON formatter | structlog | Context vars, async support, processors |

**Key insight:** Все эти проблемы выглядят простыми, но имеют edge cases (connection leaks, migration conflicts, constraint names в разных БД). Стандартные решения уже обработали эти cases.

## Common Pitfalls

### Pitfall 1: expire_on_commit не отключен

**What goes wrong:** После `session.commit()` атрибуты объекта помечаются как expired. При обращении к ним SQLAlchemy пытается сделать lazy load — падает в async контексте.
**Why it happens:** Default `expire_on_commit=True` в SQLAlchemy.
**How to avoid:** `async_sessionmaker(..., expire_on_commit=False)`
**Warning signs:** `MissingGreenlet` или `greenlet.error` exceptions

### Pitfall 2: Нет naming convention — миграция не может удалить constraint

**What goes wrong:** `alembic revision --autogenerate` генерирует `op.drop_constraint(None, ...)` — падает.
**Why it happens:** PostgreSQL автоматически создаёт constraints с именами типа `users_pkey`, но SQLAlchemy не знает этих имён.
**How to avoid:** Настроить `MetaData(naming_convention={...})` ДО первой миграции.
**Warning signs:** Ошибки при попытке изменить или удалить FK/UNIQUE constraints

### Pitfall 3: DATABASE_URL без +asyncpg

**What goes wrong:** SQLAlchemy пытается использовать sync драйвер.
**Why it happens:** Railway даёт URL вида `postgresql://...`, не `postgresql+asyncpg://...`
**How to avoid:** Трансформировать URL в config:
```python
@property
def async_database_url(self) -> str:
    return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
```
**Warning signs:** `TypeError: 'Pool' object is not callable` или sync operation errors

### Pitfall 4: Alembic не видит модели

**What goes wrong:** `alembic revision --autogenerate` создаёт пустую миграцию.
**Why it happens:** Модели не импортированы в `env.py` до `target_metadata = Base.metadata`.
**How to avoid:** Явный import всех моделей:
```python
# migrations/env.py
from src.db.models.base import Base
from src.db.models import user  # Import всех модулей с моделями
```
**Warning signs:** "No changes detected" при наличии новых моделей

### Pitfall 5: Railway PORT не используется

**What goes wrong:** App запускается на hardcoded порту, Railway не может проксировать.
**Why it happens:** `uvicorn ... --port 8000` вместо `--port $PORT`.
**How to avoid:** `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`
**Warning signs:** Service not reachable, 502 errors

### Pitfall 6: Pool exhaustion при высокой нагрузке

**What goes wrong:** `asyncpg.exceptions.PoolEmptyError` — все соединения заняты.
**Why it happens:** Default pool size (10) маленький для concurrent requests; connections не возвращаются в pool.
**How to avoid:**
1. Настроить `pool_size` и `max_overflow` в engine
2. Использовать context manager для sessions
3. Не держать session открытой во время long operations (AI calls)
**Warning signs:** Intermittent connection errors под нагрузкой

## Code Examples

### Minimal User Model (Phase 1)

```python
# src/db/models/user.py
from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
```

### pyproject.toml (Poetry 2.0+)

```toml
[build-system]
requires = ["poetry-core>=2.0.0"]
build-backend = "poetry.core.masonry.api"

[project]
name = "adtrobot"
version = "0.1.0"
description = "Telegram astrology and tarot bot"
requires-python = ">=3.11"
dependencies = [
    "sqlalchemy[asyncio]>=2.0.46",
    "asyncpg>=0.31.0",
    "alembic>=1.18.1",
    "pydantic-settings>=2.7.1",
    "structlog>=25.5.0",
    "uvicorn[standard]>=0.40.0",
    "python-dotenv>=1.0.1",
    "fastapi>=0.128.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.0",
]

[tool.poetry]
package-mode = false  # Non-package mode для application

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install Poetry
        run: pipx install poetry
      - name: Install dependencies
        run: poetry install
      - name: Run linter
        run: poetry run ruff check .
      - name: Run tests
        run: poetry run pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: railwayapp/cli-action@v1
        with:
          token: ${{ secrets.RAILWAY_TOKEN }}
          service: ${{ vars.RAILWAY_SERVICE_ID }}
```

### .env.example

```bash
# Database (Railway auto-injects DATABASE_URL)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/adtrobot

# App settings
DEBUG=true
LOG_LEVEL=DEBUG

# Railway (auto-injected in production)
PORT=8000
```

### alembic.ini (ключевые настройки)

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os

# Date-based file template for better organization
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(rev)s_%%(slug)s

[post_write_hooks]
hooks = ruff
ruff.type = exec
ruff.executable = ruff
ruff.options = format REVISION_SCRIPT_FILENAME
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SQLAlchemy 1.x sync | SQLAlchemy 2.0 async | 2023 | Native async support, better typing |
| setup.py | pyproject.toml (PEP 621) | 2022-2025 | Standardized metadata, Poetry 2.0 |
| stdlib logging | structlog | 2020+ | Structured JSON, context vars |
| Manual constraint names | naming_convention | SQLAlchemy 0.9.2+ | Automatic, consistent |

**Deprecated/outdated:**
- `create_engine()` для async: использовать `create_async_engine()`
- `Session` для async: использовать `AsyncSession`
- `poetry.tool` section: Poetry 2.0+ использует `[project]` (PEP 621)

## Open Questions

1. **Railway PostgreSQL connection limits**
   - What we know: Railway предоставляет managed PostgreSQL
   - What's unclear: Точные лимиты на connections для бесплатного/платного плана
   - Recommendation: Начать с `pool_size=5, max_overflow=10`, мониторить

2. **Alembic offline migrations**
   - What we know: Railway может не иметь доступа к БД во время build
   - What's unclear: Когда именно запускать миграции (startup vs build)
   - Recommendation: Запускать при startup приложения через FastAPI lifespan

## Sources

### Primary (HIGH confidence)
- [SQLAlchemy 2.0 Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) - session patterns, engine config
- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/) - autogenerate, naming conventions
- [Poetry Documentation](https://python-poetry.org/docs/pyproject/) - pyproject.toml structure
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - env vars, .env files
- [Railway GitHub Actions Guide](https://blog.railway.com/p/github-actions) - CI/CD workflow
- [Railway Autodeploys](https://docs.railway.com/guides/github-autodeploys) - Wait for CI feature

### Secondary (MEDIUM confidence)
- [structlog Documentation](https://www.structlog.org/en/stable/) - async logging, contextvars
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/current/usage.html) - connection pool

### Tertiary (LOW confidence)
- WebSearch results for "best practices 2026" - general patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - официальная документация, версии проверены на PyPI
- Architecture: HIGH - паттерны из официальной документации SQLAlchemy/Alembic
- Pitfalls: HIGH - задокументированы в issues и discussions
- Railway CI/CD: MEDIUM - официальный блог, но может измениться

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - stable technologies)
