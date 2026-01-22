# Project Research Summary

**Project:** AdtroBot — Telegram астрологический бот с таро
**Domain:** Freemium Telegram bot (астрология, таро, AI, платежи)
**Researched:** 2026-01-22
**Confidence:** HIGH

## Executive Summary

AdtroBot — это Telegram бот freemium модели, предоставляющий астрологические и таро-сервисы с AI-интерпретациями и платными подписками через ЮКасса. Исследование показывает, что ключ к успеху — это **модульный монолит** на Python (aiogram 3.x + FastAPI + PostgreSQL), развёртываемый на Railway. Основная ценность продукта в **качестве AI-интерпретаций**, а не в количестве функций. Конкуренты предлагают либо глубокую астрологию без таро (Saturn.Love), либо простые таро без астрологии (@tarologia_robot). Наша ниша — баланс обоих направлений с акцентом на персонализацию через AI.

Критические риски сосредоточены в **трёх областях**: (1) платежи — webhook от ЮКасса должен обрабатываться идемпотентно с немедленным HTTP 200, иначе потеря платежей; (2) AI quality — промпты требуют структурирования и валидации, иначе users уйдут из-за generic ответов; (3) система лимитов — race conditions приведут к бесплатному доступу к платному контенту. Mitigation: атомарные операции в БД, webhook в очередь, human review первых 100 AI генераций.

Рекомендация: запускать с **минимальным MVP** (гороскоп дня + таро расклад 3 карты + AI интерпретация + платёж через Telegram Stars), валидировать конверсию free→paid (target 5-10%), затем добавлять premium функции (натальная карта, транзиты). Не строить "всё в одном" сразу — это путь к complexity без validation.

## Key Findings

### Recommended Stack

**Стек основан на async Python экосистеме** для максимальной производительности при работе с Telegram webhooks, AI API и БД. Выбор aiogram 3.x + FastAPI + PostgreSQL обусловлен нативной async поддержкой, активной разработкой, и совместимостью с Railway PaaS.

**Core technologies:**
- **Python 3.11+** + **aiogram 3.24.0**: асинхронный Telegram bot framework с FSM, webhook support. Стандарт для production ботов
- **FastAPI 0.128.0** + **uvicorn 0.40.0**: async web framework для admin панели и webhooks. Автодокументация OpenAPI, Railway-native
- **PostgreSQL 16+** + **SQLAlchemy 2.0 async** + **asyncpg**: реляционная БД для платежей и подписок. Railway managed, полная async поддержка
- **yookassa 3.9.0**: официальный SDK ЮКасса для платежей и подписок
- **openai 2.15.0** через **OpenRouter**: LLM API для AI-интерпретаций (Claude 3.5 Sonnet). OpenAI SDK совместим с OpenRouter
- **kerykeion 5.6.3**: астрологические расчёты натальных карт (Swiss Ephemeris). **AGPL лицензия — требует внимания**
- **sqladmin 0.22.0**: легковесная async admin панель поверх SQLAlchemy

**Что НЕ использовать:**
- python-telegram-bot (sync mode) — блокирующие вызовы
- Flask — WSGI, не async
- SQLite в production — нет concurrent writes для платежей
- MongoDB — реляционные данные (users, subscriptions, payments) лучше в SQL

### Expected Features

**Must have (table stakes):**
- Ежедневный гороскоп по знаку зодиака — базовое ожидание (48% пользователей заходят ежедневно)
- Карта дня таро — стандарт всех таро-сервисов, простой entry point
- Визуализация карт — пользователи ожидают изображения, не только текст (колода Райдера-Уэйта)
- Выбор знака зодиака при onboarding — персонализация с первого запуска
- Бесплатный базовый доступ — freemium модель стандарт индустрии
- Push-уведомления — 18-24% engagement rate при персонализированных пушах

**Should have (competitive advantage):**
- **AI-интерпретация раскладов** — ключевой дифференциатор. Персонализированные толкования vs шаблонный текст. +30-45% engagement
- Натальная карта с расшифровкой — глубокая персонализация, premium-фича у всех лидеров (Co-Star, Saturn.Love)
- 3-5 видов раскладов таро — разнообразие увеличивает retention
- История раскладов — возможность вернуться к прошлым гаданиям
- Тематические гороскопы (любовь/карьера/финансы) — структурированный контент

**Defer (v2+):**
- Уведомления о транзитах — Saturn.Love USP, но операционно сложно
- Совместимость (синастрия) — вирусный потенциал, но требует 2 натальные карты
- PDF-отчёты — premium feel, но не critical для MVP
- Голосовая озвучка — accessibility, но можно отложить
- 12+ раскладов — overkill для MVP

**Anti-features (чего НЕ делать):**
- Слишком много пушей — 33% uninstall при спаме
- Живые консультации с астрологами — операционная сложность (как у Numia)
- Социальная сеть внутри бота — модерация, отвлечение от core value
- Слишком много бесплатного контента — нет конверсии в платных (3-7% benchmark при правильном балансе)

### Architecture Approach

**Рекомендация: модульный монолит** (один FastAPI сервис). Microservices — overkill для этого масштаба. Монолит проще для Railway, дешевле, быстрее запуск. Пересматривать при 100k+ пользователей.

**Major components:**
1. **FastAPI App** — HTTP сервер, webhooks (Telegram + ЮКасса), admin панель
2. **Bot Service (aiogram)** — обработка Telegram updates, FSM, команды, inline buttons
3. **AI Service** — генерация интерпретаций через OpenRouter, промпты, retry logic
4. **Payment Service** — интеграция ЮКасса, создание платежей, обработка webhooks, активация подписок
5. **User Service** — управление пользователями, подписками, лимитами
6. **Data Layer** — SQLAlchemy 2.0 async + repository pattern
7. **PostgreSQL (Railway managed)** — персистентное хранение

**Ключевые паттерны:**
- **Webhook-based bot** — не polling в production. Railway даёт публичный HTTPS URL
- **Middleware chain** — auth + subscription checks на каждый запрос
- **Repository pattern** — бизнес-логика не знает о SQLAlchemy
- **Service layer для AI** — единая точка для промптов, timeout, fallback
- **Async везде** — asyncpg, aiogram, FastAPI. НЕТ синхронных DB вызовов

**Structure:**
```
src/
├── main.py              # FastAPI + aiogram webhook
├── bot/                 # Telegram handlers, middlewares, FSM
├── services/            # Бизнес-логика (AI, payments, tarot)
├── api/                 # FastAPI endpoints (webhooks, admin)
├── admin/               # Admin panel (sqladmin)
├── db/                  # SQLAlchemy models, repositories
└── core/                # Config, exceptions, constants
```

### Critical Pitfalls

1. **Webhook ЮКасса не подтверждён вовремя** — ЮКасса ожидает HTTP 200 за 10 секунд, иначе retry. **Решение:** немедленный ответ 200, обработка в очередь, идемпотентность по `payment_id`

2. **Race conditions в системе лимитов** — concurrent requests bypass лимиты free пользователей. **Решение:** атомарные операции в БД (`UPDATE ... WHERE limits > 0 RETURNING`), Redis DECR, mutex per user_id

3. **AI генерирует бред или generic контент** — потеря доверия. **Решение:** структурированные промпты с JSON schema, few-shot примеры, валидация упоминания карт/планет, human review первых 100 генераций

4. **Подписка истекла, но доступ остался** — потеря дохода. **Решение:** проверка `subscription_end_date` на каждый запрос, polling fallback раз в час, webhook retry queue

5. **Ошибки расчёта натальной карты** — репутационный ущерб. **Решение:** Swiss Ephemeris data files в deployment, timezone conversion (UTC), тестирование против astro.com

6. **OpenRouter timeout/failure** — бот "завис". **Решение:** timeout 30s, fallback модель (GPT-4 → Claude-3-Haiku), индикация "Анализирую...", cached generic response

7. **Пользователь не понимает ценность premium** — низкая конверсия. **Решение:** value first (бесплатный опыт качественный), teaser premium (первый абзац натальной карты), paywall после 3-5 free использований, таблица Free vs Premium

8. **Railway deployment issues** — connection pool exhausted, memory leaks. **Решение:** asyncpg pool (size=10-20), `/health` endpoint, мониторинг памяти, `RAILWAY_SHM_SIZE_BYTES=524288000`

9. **Пользователь ушёл после первого сообщения** — нет retention. **Решение:** immediate value (карта дня сразу после /start), buttons not commands, progressive disclosure, daily hook

10. **Abuse через multiple accounts** — drain AI costs. **Решение:** мониторинг аномалий, usage patterns, заложить в unit economics как cost of business

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Core Infrastructure + Auth
**Rationale:** База данных и пользовательская модель — фундамент всего. Без этого невозможны лимиты и подписки.
**Delivers:** PostgreSQL схема, SQLAlchemy models (User, Subscription, Payment), Alembic migrations, async session factory, config management
**Addresses:** Pitfall #2 (race conditions) — атомарная структура БД с первого дня
**Tech:** PostgreSQL 16, SQLAlchemy 2.0 async, asyncpg, Pydantic Settings

### Phase 2: Bot Core + Onboarding
**Rationale:** Минимально работающий бот. Можно деплоить и тестировать webhook flow.
**Delivers:** aiogram Bot + Dispatcher, FastAPI app, webhook endpoint `/webhook/telegram`, auth middleware (создание/загрузка user), базовые handlers (/start, /help), onboarding flow (дата рождения → знак зодиака)
**Addresses:** Pitfall #9 (плохой retention) — immediate value с первого сообщения
**Tech:** aiogram 3.24.0, FastAPI 0.128.0, Railway deployment

### Phase 3: Free Features (Таро + Гороскопы)
**Rationale:** Бесплатный функционал привлекает пользователей и валидирует product-market fit.
**Delivers:** Колода таро (Райдер-Уэйт), расклад 3 карты, ежедневный гороскоп по знаку, визуализация карт, subscription middleware (проверка лимитов)
**Addresses:** Features Table Stakes — гороскоп дня + карта дня обязательны
**Tech:** Tarot logic, horoscope service, inline buttons UI

### Phase 4: AI Integration
**Rationale:** Ключевой дифференциатор. После базового функционала добавляем AI для персонализации.
**Delivers:** OpenRouter интеграция, структурированные промпты, AI-интерпретация раскладов таро, timeout + fallback logic, кэширование гороскопов
**Addresses:** Pitfall #3 (AI quality) + Pitfall #6 (timeout) — с первой интеграции
**Tech:** openai SDK + OpenRouter, Claude 3.5 Sonnet, retry + cache

### Phase 5: Payments (ЮКасса)
**Rationale:** Монетизация. Требует рабочего бота и пользователей для валидации конверсии.
**Delivers:** yookassa SDK integration, создание платежей, webhook `/webhook/payment`, signature verification, активация подписок, subscription management (status, end_date), payment handlers (/subscribe, /status)
**Addresses:** Pitfall #1 (webhook timeout) + Pitfall #4 (expired subscription) — idempotent webhook processing
**Tech:** yookassa 3.9.0, webhook queue, signature verification

### Phase 6: Premium Features
**Rationale:** Ценность для платных подписчиков. Добавлять после подтверждения конверсии free→paid.
**Delivers:** Натальная карта (kerykeion), расширенные расклады таро (5-7 видов), тематические гороскопы (любовь/карьера/финансы), история раскладов
**Addresses:** Features Differentiators — натальная карта обязательна для retention платных
**Tech:** kerykeion 5.6.3, Swiss Ephemeris data files, timezone handling (pytz)

### Phase 7: Admin Panel
**Rationale:** Админка нужна когда есть что администрировать (пользователи, платежи, метрики).
**Delivers:** sqladmin setup, dashboard (метрики DAU/MAU/MRR), user management (поиск, детали, подписки), analytics (воронка, retention cohorts), broadcast management
**Addresses:** Операционные потребности после запуска
**Tech:** sqladmin 0.22.0, FastAPI routes, Jinja2 templates

### Phase Ordering Rationale

- **Инфраструктура первой** — БД и auth это фундамент. Все feature-фазы от них зависят.
- **Бесплатное перед платным** — нужна база пользователей для валидации конверсии в подписки.
- **AI после базовых features** — пользователи должны понимать ценность бесплатного функционала до AI enhancement.
- **Платежи после AI** — monetization когда есть ценность (AI интерпретации).
- **Premium после payments** — premium features осмысленны только для платящих.
- **Админка в конце** — операционная необходимость, не user-facing.

**Dependency chain:**
```
Phase 1 (DB)
  └──> Phase 2 (Bot Core)
         └──> Phase 3 (Free Features)
                └──> Phase 4 (AI)
                       └──> Phase 5 (Payments)
                              └──> Phase 6 (Premium)
                                     └──> Phase 7 (Admin)
```

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 4 (AI):** Prompt engineering — нужен research-phase для оптимизации промптов под разные расклады
- **Phase 6 (Premium - Натальная карта):** Swiss Ephemeris integration — сложная библиотека, sparse documentation на kerykeion, нужен research-phase для timezone handling

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Infrastructure):** SQLAlchemy async setup хорошо документирован
- **Phase 2 (Bot Core):** aiogram webhook flow стандартный паттерн
- **Phase 3 (Free Features):** Tarot logic straightforward
- **Phase 5 (Payments):** ЮКасса SDK официально документирован
- **Phase 7 (Admin):** sqladmin examples из коробки

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | Все компоненты (aiogram, FastAPI, PostgreSQL, yookassa, openai) имеют официальную документацию, активную разработку, PyPI verified. Версии актуальные (Jan 2026). |
| Features | **MEDIUM-HIGH** | Основано на анализе 10+ конкурентов (Saturn.Love, Numia, Tarot Go, @tarologia_robot). Метрики из industry sources (48% DAU, 5-10% конверсия). Kerykeion AGPL требует внимания. |
| Architecture | **HIGH** | Aiogram webhook + FastAPI монолит стандартный паттерн для Telegram ботов на Railway. Async SQLAlchemy 2.0 проверен в production. |
| Pitfalls | **HIGH** | Основано на официальной документации ЮКасса webhooks, Telegram Bot API rate limits, OpenRouter error handling, опыте сообщества (Reddit, GitHub issues). |

**Overall confidence:** **HIGH**

### Gaps to Address

**Gap #1: kerykeion AGPL лицензия**
- **Issue:** kerykeion использует AGPL лицензию — требует открытия кода при SaaS использовании
- **Mitigation:** Уточнить лицензию перед Phase 6. Альтернативы: AstrologerAPI (hosted), immanuel-python (MIT, менее функциональный), pyswisseph (низкоуровневый)
- **Phase to address:** Phase 6 planning

**Gap #2: Конверсия free→paid**
- **Issue:** 3-7% benchmark из VC.ru, но нет данных специфично для астро-ботов
- **Mitigation:** A/B тестирование paywall timing, freemium limits. Итерация на основе real data
- **Phase to address:** Phase 5 (Payments) — внедрить analytics с первого дня

**Gap #3: AI costs unit economics**
- **Issue:** OpenRouter pricing зависит от модели и токенов. Неизвестно сколько стоит интерпретация одного расклада
- **Mitigation:** Прототипировать промпты, замерить среднюю стоимость (expected ~$0.01-0.05 per расклад). Заложить в pricing
- **Phase to address:** Phase 4 (AI) — cost benchmarking

**Gap #4: Abuse/fraud patterns**
- **Issue:** Нет данных сколько % пользователей создают multiple accounts для бесплатных раскладов
- **Mitigation:** Мониторинг аномалий после запуска. Принять как cost of business (1-3%)
- **Phase to address:** Post-launch мониторинг

**Gap #5: Railway performance на реальной нагрузке**
- **Issue:** Неизвестно как Railway справляется с 1k+ concurrent webhook requests
- **Mitigation:** Load testing перед публичным запуском. Railway auto-scaling проверен на других Telegram ботах
- **Phase to address:** Phase 2 deployment — staging environment tests

## Sources

### Primary (HIGH confidence)
- [aiogram PyPI](https://pypi.org/project/aiogram/) v3.24.0 (Jan 2, 2026) — официальный SDK
- [aiogram Documentation](https://docs.aiogram.dev/en/latest/) — FSM, handlers, webhooks
- [FastAPI PyPI](https://pypi.org/project/fastapi/) v0.128.0 (Dec 27, 2025)
- [Railway FastAPI Guide](https://docs.railway.com/guides/fastapi) — deployment patterns
- [SQLAlchemy PyPI](https://pypi.org/project/SQLAlchemy/) v2.0.46 (Jan 21, 2026)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [yookassa PyPI](https://pypi.org/project/yookassa/) v3.9.0 (Dec 17, 2025)
- [YooKassa Webhooks Documentation](https://yookassa.ru/developers/using-api/webhooks)
- [OpenRouter Docs](https://openrouter.ai/docs/quickstart) — OpenAI SDK compatibility
- [Telegram Bot API](https://core.telegram.org/bots/api)

### Secondary (MEDIUM confidence)
- [Saturn.Love](https://saturn.love/ru) — конкурентный анализ
- [Numia (@numiaclub_bot)](https://telegram.org.ru/20476-personalnyy-astrolog.html) — 10M+ пользователей
- [Tarot Go](https://aidive.org/ai/tarot-go) — 12 раскладов, AI
- [Vocal Media: Why Astrology Apps Fail](https://vocal.media/humans/why-most-astrology-apps-fail-and-how-to-build-one-users-actually-trust) — 33% uninstall stats
- [VC.ru: Монетизация Telegram ботов](https://vc.ru/telegram/1916841-sozdanie-i-monetizatsiya-telegram-botov-v-2025-godu) — 3-7% конверсия, 299₽/мес
- [Consumer Subscription KPI Benchmarks](https://medium.com/parsa-vc/consumer-subscription-kpi-benchmarks-retention-engagement-and-conversion-rates-9ac13b57c3d3)

### Tertiary (LOW confidence, needs validation)
- [kerykeion PyPI](https://pypi.org/project/kerykeion/) v5.6.3 (Jan 19, 2026) — AGPL лицензия требует проверки
- 48% DAU stat (Vocal Media) — industry average, не специфично для Telegram ботов
- Unit economics AI costs — needs benchmarking

---
*Research completed: 2026-01-22*
*Ready for roadmap: YES*
