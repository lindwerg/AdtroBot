# Architecture Research

**Domain:** Telegram бот с подписками, админ панелью и AI интеграцией
**Researched:** 2026-01-22
**Confidence:** HIGH

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
*Researched: 2026-01-22*
