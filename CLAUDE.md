# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Проект

AdtroBot — Telegram бот для астрологии и таро с AI, freemium модель (бесплатные гороскопы + платная подписка через ЮКасса).

**Стек:**
- Backend: Python 3.11, FastAPI, aiogram 3.x, SQLAlchemy 2.x (async), PostgreSQL
- Frontend: React 19, Ant Design Pro, TypeScript, Vite, Zustand
- Инфраструктура: Railway (production), Docker
- AI: OpenRouter API
- Платежи: ЮКасса (YooKassa)
- Астрология: pyswisseph

## Команды разработки

### Backend (Python)

```bash
# Установка зависимостей
poetry install

# Активировать виртуальное окружение
poetry shell

# Запустить бота локально (без webhook)
python -m src.bot.bot

# Запустить FastAPI сервер (с webhook)
uvicorn src.main:app --reload --port 8000

# Миграции базы данных
alembic upgrade head                    # Применить миграции
alembic revision --autogenerate -m ""   # Создать новую миграцию

# Тесты
pytest                                  # Все тесты
pytest tests/services                   # Юнит-тесты сервисов
pytest tests/e2e                        # E2E тесты
pytest -m slow                          # Только медленные тесты
pytest --cov=src --cov-report=html      # С покрытием

# Линтер
ruff check .                            # Проверка
ruff check . --fix                      # Автофикс
ruff format .                           # Форматирование

# Нагрузочное тестирование
locust -f tests/load/basic.py --host=http://localhost:8000
```

### Frontend (Admin Panel)

```bash
cd admin-frontend

# Установка зависимостей
npm ci

# Запуск dev-сервера
npm run dev

# Сборка для продакшена
npm run build

# Линтер
npm run lint

# E2E тесты (Playwright)
npx playwright test
npx playwright test --ui                # С UI
npx playwright test --headed            # С браузером
```

### Docker

```bash
# Сборка
docker build -t adtrobot .

# Запуск
docker run -p 8000:8000 --env-file .env adtrobot
```

## Архитектура

### Backend структура (`src/`)

```
src/
├── main.py                  # FastAPI app, webhook endpoints, lifespan
├── config.py                # Pydantic settings (DATABASE_URL, API keys)
├── bot/                     # Telegram bot (aiogram)
│   ├── bot.py               # Bot & dispatcher singleton
│   ├── handlers/            # Telegram handlers по фичам
│   │   ├── start.py         # /start, /help, /about
│   │   ├── horoscope.py     # Гороскопы (бесплатные + premium)
│   │   ├── tarot.py         # Таро расклады
│   │   ├── natal.py         # Натальные карты
│   │   ├── subscription.py  # Подписки и покупки
│   │   └── profile.py       # Профиль пользователя
│   ├── keyboards/           # Inline/Reply клавиатуры
│   ├── callbacks/           # Callback query handlers
│   ├── middlewares/         # DbSessionMiddleware (async session в handler)
│   └── states/              # FSM состояния (ввод даты рождения и т.д.)
├── services/                # Бизнес-логика
│   ├── ai/                  # AI генерация (OpenRouter)
│   ├── astrology/           # pyswisseph расчёты
│   ├── payment/             # YooKassa integration
│   ├── horoscope_cache.py   # Кэш дневных гороскопов (PostgreSQL + in-memory)
│   ├── scheduler.py         # APScheduler для фоновых задач
│   └── telegraph.py         # Telegraph для больших текстов
├── db/                      # SQLAlchemy
│   ├── engine.py            # AsyncEngine, session factory
│   └── models/              # SQLAlchemy модели (User, Subscription, TarotSpread...)
├── admin/                   # Admin API (FastAPI)
│   ├── router.py            # REST endpoints (статистика, юзеры, платежи)
│   ├── auth.py              # JWT authentication для admin
│   └── services/            # Admin бизнес-логика
├── monitoring/              # Health checks
└── core/                    # Утилиты (logging)

migrations/                  # Alembic миграции
tests/
├── conftest.py              # Pytest fixtures (test DB, client)
├── services/                # Юнит-тесты сервисов
├── e2e/                     # End-to-end тесты бота
└── load/                    # Locust нагрузочные тесты

admin-frontend/              # React SPA для админ-панели
├── src/
│   ├── api/                 # Axios клиент + endpoints
│   ├── pages/               # Страницы (Dashboard, Users, Payments)
│   ├── components/          # React компоненты
│   ├── store/               # Zustand store (auth)
│   └── routes/              # React Router config
└── dist/                    # Собранный бандл (подключается в main.py)
```

### Ключевые паттерны

1. **Webhook обработка (src/main.py)**:
   - `/webhook` — Telegram updates (валидация через secret token)
   - `/webhook/yookassa` — ЮКасса webhooks (IP whitelist + idempotency через payment_id)
   - **КРИТИЧНО**: ЮКасса webhook должен вернуть HTTP 200 за <10 секунд, иначе повторные попытки. Используется BackgroundTasks для обработки.

2. **Database sessions**:
   - Async sessions через `AsyncSessionLocal()`
   - Telegram handlers получают session через `DbSessionMiddleware` (в `event.context["session"]`)
   - Admin API использует `Depends(get_session)`

3. **Лимиты (race conditions)**:
   - Atomic `SELECT ... FOR UPDATE` перед декрементом лимитов
   - Пример: `src/services/payment/service.py` — check-and-decrement в одной транзакции

4. **Кэш гороскопов (PERF-07)**:
   - Дневные гороскопы кэшируются в PostgreSQL (`horoscope_cache` таблица) + in-memory dict
   - Прогрев кэша при старте (см. `warm_horoscope_cache()` в `main.py`)
   - Автообновление через scheduler (каждый день в 00:00 UTC)

5. **AI генерация**:
   - OpenRouter API (модель настраивается в промптах)
   - Retry логика с exponential backoff (tenacity)
   - Тайминг: ~3-10 секунд на запрос

6. **Admin panel**:
   - SPA served через FastAPI (`/admin/*` → `index.html`)
   - JWT auth (Bearer token в headers)
   - Статика монтируется в `/admin/assets`

### Критические моменты (PITFALLS.md)

1. **YooKassa webhook**: возвращать 200 немедленно, обрабатывать в background
2. **Race conditions в лимитах**: использовать `SELECT FOR UPDATE`
3. **AI timeout**: не блокировать Telegram webhook, использовать async
4. **Миграции**: всегда тестировать на копии prod БД перед деплоем

## Деплой

**Railway** (production):
- Используется `Procfile` для запуска
- Миграции применяются автоматически при старте (`alembic upgrade head && uvicorn ...`)
- Frontend собирается в Docker при билде
- Переменные окружения настраиваются в Railway dashboard

**Локальная разработка**:
1. Скопировать `.env.example` в `.env`
2. Поднять PostgreSQL (или использовать Railway dev DB)
3. Применить миграции: `alembic upgrade head`
4. Запустить backend: `uvicorn src.main:app --reload`
5. Запустить frontend: `cd admin-frontend && npm run dev`

## Конвенции кода

- **Imports**: сортировка по алфавиту, сначала stdlib, потом third-party, потом local
- **Naming**: `snake_case` для Python, `camelCase` для TypeScript
- **Async/await**: всегда использовать для I/O (DB, API, файлы)
- **Type hints**: обязательны для всех функций (Python), интерфейсы для TS
- **Docstrings**: для публичных функций и классов, формат Google style
- **Error handling**: логировать с контекстом (structlog), не ломать бота при ошибках AI

## Особенности Telegram бота

- **Меню**: инлайн-клавиатуры с callback_data
- **FSM**: aiogram States для многошаговых сценариев (ввод даты рождения, места и т.д.)
- **Telegraph**: длинные тексты (>4096 символов) через Telegraph API
- **Markdown**: используется режим `parse_mode="Markdown"` для сообщений
- **Rate limiting**: нет встроенного, но лимиты на уровне бизнес-логики (подписки)

## Мониторинг

- `/health` — health check endpoint (DB, scheduler)
- `/metrics` — Prometheus метрики (автоматически экспортируются)
- Structlog логи в JSON (для Railway log aggregation)
