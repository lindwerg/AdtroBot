# Stack Research

**Domain:** Telegram бот с астрологией/таро + AI + платежи + админ панель
**Researched:** 2026-01-22
**Confidence:** HIGH

## Рекомендуемый стек

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Python** | 3.11+ | Runtime | Стабильная версия с полной async поддержкой, оптимальный баланс скорости и совместимости |
| **aiogram** | 3.24.0 | Telegram Bot Framework | Асинхронный, современный, активная разработка, FSM из коробки, webhook support. Стандарт для production ботов |
| **FastAPI** | 0.128.0 | Web Framework (API + Админка) | Асинхронный, автодокументация OpenAPI, отличная экосистема, идеален для Railway |
| **PostgreSQL** | 16+ | Database | Railway поддерживает нативно, надежность для платежей, масштабируемость |
| **SQLAlchemy** | 2.0.46 | ORM | Async support 2.0, зрелый, Alembic миграции, совместим с SQLAdmin |
| **Pydantic** | 2.12.5 | Validation | Интеграция с FastAPI, типизация, JSON Schema генерация |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **yookassa** | 3.9.0 | ЮКасса SDK | Все платежные операции (подписки, webhooks) |
| **openai** | 2.15.0 | OpenRouter API | AI интерпретации через OpenRouter (OpenAI-совместимый API) |
| **sqladmin** | 0.22.0 | Admin Panel | Веб-админка для управления пользователями, подписками, контентом |
| **alembic** | 1.18.1 | Migrations | Миграции схемы базы данных |
| **asyncpg** | 0.31.0 | PostgreSQL Driver | Async драйвер для SQLAlchemy 2.0 |
| **uvicorn** | 0.40.0 | ASGI Server | Production сервер для FastAPI на Railway |
| **redis** | 7.1.0 | Cache/Sessions | FSM storage для aiogram, кэширование гороскопов |
| **kerykeion** | 5.6.3 | Astrology Calculations | Расчет натальных карт (Swiss Ephemeris под капотом) |
| **APScheduler** | 3.10.4 | Task Scheduler | Ежедневная генерация гороскопов |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| **ruff** | Linter + Formatter | Замена flake8/black/isort, быстрый |
| **pytest** | Testing | С pytest-asyncio для async тестов |
| **pytest-asyncio** | Async Tests | Тестирование async handlers |
| **httpx** | HTTP Client | Async HTTP для тестов и внешних API |
| **python-dotenv** | Env Management | Локальная разработка с .env файлами |

## Installation

```bash
# Core
pip install aiogram==3.24.0 fastapi==0.128.0 uvicorn==0.40.0 pydantic==2.12.5

# Database
pip install sqlalchemy==2.0.46 asyncpg==0.31.0 alembic==1.18.1 psycopg2-binary

# Admin
pip install sqladmin==0.22.0

# Integrations
pip install yookassa==3.9.0 openai==2.15.0 redis==7.1.0

# Astrology
pip install kerykeion==5.6.3

# Scheduler
pip install apscheduler==3.10.4

# Dev dependencies
pip install -D ruff pytest pytest-asyncio httpx python-dotenv
```

Или единым requirements.txt:
```
aiogram==3.24.0
fastapi==0.128.0
uvicorn[standard]==0.40.0
pydantic==2.12.5
sqlalchemy[asyncio]==2.0.46
asyncpg==0.31.0
alembic==1.18.1
psycopg2-binary
sqladmin[full]==0.22.0
yookassa==3.9.0
openai==2.15.0
redis==7.1.0
kerykeion==5.6.3
apscheduler==3.10.4
python-dotenv
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| **aiogram** | python-telegram-bot | Если команда не знакома с asyncio; для простых синхронных ботов |
| **PostgreSQL** | SQLite | Только для локальной разработки/прототипа. НЕ для production с платежами |
| **SQLAlchemy** | SQLModel | Если нужен более простой ORM без сложных запросов |
| **sqladmin** | starlette-admin | Если нужна поддержка ORM отличных от SQLAlchemy |
| **kerykeion** | AstrologerAPI | Если нужен closed-source (kerykeion AGPL) или SaaS без локальных расчетов |
| **APScheduler** | Celery | Если нужен distributed task queue с workers (overkill для этого проекта) |
| **Redis** | Memory FSM | Только для разработки. Production требует persistent storage |

## Что НЕ использовать

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **python-telegram-bot (sync mode)** | Блокирующие вызовы снижают throughput, не оптимально для бота с AI вызовами | aiogram 3.x (полностью async) |
| **Flask** | WSGI, синхронный, требует отдельных workers для async | FastAPI (нативный ASGI) |
| **SQLite в production** | Не подходит для concurrent writes, нет транзакций уровня PostgreSQL | PostgreSQL |
| **Django Admin** | Overkill, синхронный, требует Django ORM | sqladmin (легковесный, async) |
| **flatlib** | Устаревшая, не поддерживается активно | kerykeion (активная разработка, Pydantic 2) |
| **Gunicorn напрямую** | WSGI сервер, для FastAPI нужен uvicorn worker | uvicorn или gunicorn с UvicornWorker |
| **MongoDB** | Реляционные данные (пользователи, подписки, платежи) лучше в SQL | PostgreSQL |
| **aioyookassa** | Сторонняя обертка, официальный SDK yookassa синхронный но надежный | yookassa (официальный SDK) + run_in_threadpool |

## Stack Patterns by Variant

**Если нужен closed-source (kerykeion AGPL ограничение):**
- Использовать AstrologerAPI (hosted API от автора kerykeion)
- Или написать собственные расчеты на pyswisseph (более низкоуровневый)
- Или использовать immanuel-python (MIT лицензия, но менее функциональный)

**Если Railway не подходит для Redis:**
- aiogram поддерживает MemoryStorage для FSM (только для dev)
- Или использовать Redis addon в Railway
- Или внешний Redis (Upstash, Redis Cloud)

**Если нужна высокая нагрузка (10K+ пользователей):**
- Добавить Celery для background AI генерации
- Horizontal scaling на Railway (multiple instances)
- Connection pooling для PostgreSQL (asyncpg pool)

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| SQLAlchemy 2.0.46 | asyncpg 0.31.0 | Протестировано, работает стабильно |
| SQLAlchemy 2.0.46 | sqladmin 0.22.0 | Полная совместимость |
| FastAPI 0.128.0 | Pydantic 2.12.5 | FastAPI требует Pydantic v2 |
| aiogram 3.24.0 | Python 3.10+ | aiogram 3.x не работает на Python < 3.10 |
| uvicorn 0.40.0 | Python 3.10+ | Требует Python 3.10+ |
| kerykeion 5.6.3 | Pydantic 2.x | Использует Pydantic v2 модели |

## Railway Deployment Notes

**Рекомендуемая конфигурация railway.json:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

**Сервисы в Railway:**
1. **Web Service** - FastAPI (админка + webhooks от Telegram и ЮКасса)
2. **PostgreSQL** - Railway PostgreSQL plugin
3. **Redis** - Railway Redis plugin или Upstash

**Переменные окружения:**
```
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
TELEGRAM_BOT_TOKEN=...
OPENROUTER_API_KEY=...
YOOKASSA_SHOP_ID=...
YOOKASSA_SECRET_KEY=...
```

## Architecture Decision: Monolith vs Microservices

**Рекомендация: Monolith (один FastAPI сервис)**

Причины:
1. Проще деплой на Railway (один сервис)
2. Меньше latency между компонентами
3. Проще отладка
4. Для MVP/SMB нагрузки достаточно
5. aiogram webhook handlers + FastAPI routes в одном приложении

**Структура:**
```
app/
├── main.py              # FastAPI + aiogram webhook
├── bot/                 # Telegram bot handlers
│   ├── handlers/
│   └── middlewares/
├── api/                 # REST API endpoints
├── admin/               # SQLAdmin configuration
├── services/            # Business logic
│   ├── astrology.py
│   ├── tarot.py
│   ├── ai.py
│   └── payments.py
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
└── core/                # Config, dependencies
```

## Confidence Assessment

| Component | Confidence | Reason |
|-----------|------------|--------|
| aiogram 3.24.0 | HIGH | Официальная документация, активная разработка, PyPI verified |
| FastAPI 0.128.0 | HIGH | Индустриальный стандарт, официальная документация |
| PostgreSQL + asyncpg | HIGH | Проверенная комбинация, Railway native support |
| yookassa 3.9.0 | HIGH | Официальный SDK от YooMoney, недавний релиз |
| openai SDK + OpenRouter | HIGH | OpenRouter официально поддерживает OpenAI SDK |
| sqladmin 0.22.0 | MEDIUM | Работает хорошо, но менее зрелый чем Django Admin |
| kerykeion 5.6.3 | MEDIUM | AGPL лицензия требует внимания, но функционал отличный |
| Redis FSM storage | HIGH | Документировано в aiogram, стандартный паттерн |

## Sources

- [aiogram PyPI](https://pypi.org/project/aiogram/) - версия 3.24.0, Jan 2, 2026
- [aiogram Documentation](https://docs.aiogram.dev/en/latest/) - FSM, handlers
- [FastAPI PyPI](https://pypi.org/project/fastapi/) - версия 0.128.0, Dec 27, 2025
- [Railway FastAPI Guide](https://docs.railway.com/guides/fastapi) - deployment patterns
- [SQLAlchemy PyPI](https://pypi.org/project/SQLAlchemy/) - версия 2.0.46, Jan 21, 2026
- [yookassa PyPI](https://pypi.org/project/yookassa/) - версия 3.9.0, Dec 17, 2025
- [yookassa GitHub](https://github.com/yoomoney/yookassa-sdk-python) - официальный SDK
- [OpenRouter Docs](https://openrouter.ai/docs/quickstart) - OpenAI SDK compatibility
- [sqladmin GitHub](https://github.com/aminalaee/sqladmin) - SQLAlchemy Admin
- [kerykeion PyPI](https://pypi.org/project/kerykeion/) - версия 5.6.3, Jan 19, 2026
- [kerykeion.net](https://www.kerykeion.net/) - AGPL licensing info

---
*Stack research for: AdtroBot - Telegram астро/таро бот*
*Researched: 2026-01-22*
