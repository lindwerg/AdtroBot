# Project Research Summary

**Project:** AdtroBot v2.0 — Visual Enhancement, Monitoring, Performance
**Domain:** Telegram astrology/tarot bot with freemium model
**Researched:** 2026-01-23
**Confidence:** HIGH

## Executive Summary

AdtroBot v2.0 расширяет готовый MVP (v1.0) новыми возможностями: AI-генерация изображений, мониторинг, кэширование, фоновая генерация гороскопов. Это типичный процесс доработки Telegram-ботов после запуска — фокус на performance, визуальной привлекательности и observability.

**Рекомендованный подход:** Использовать Together.ai (бесплатно 3 месяца) для генерации 15-20 изображений, Sentry для мониторинга ошибок и performance, PostgreSQL для кэширования (вместо Redis), APScheduler для фоновых задач. Архитектура остаётся модульным монолитом на Railway — добавление Redis или отдельных воркеров избыточно на текущем масштабе.

**Ключевые риски:** (1) In-memory кэш теряется при Railway restart — нужен persistent storage. (2) Telegram file_id не кэшируется — картинки загружаются повторно, медленно и дорого. (3) APScheduler jobs могут пропускаться при redeploy — требуется misfire handling. (4) Высокая cardinality метрик (user_id в labels) приведёт к Prometheus OOM.

## Key Findings

### Recommended Stack

**v2.0 добавляет 5 новых технологий** поверх существующего стека v1.0 (FastAPI, aiogram, PostgreSQL, OpenRouter, YooKassa):

**Core technologies:**
- **Together.ai + FLUX.1 [schnell]**: AI image generation — бесплатно 3 месяца (unlimited), коммерческое использование разрешено, OpenAI-совместимый API
- **Sentry.io**: Мониторинг ошибок и performance — 5,000 events/месяц бесплатно, native FastAPI integration
- **PostgreSQL (existing)**: Кэш гороскопов вместо Redis — достаточная скорость (~5-10ms), persistence, дешевле
- **Telethon**: Telegram API testing через MTProto — активная разработка (в отличие от Pyrogram), StringSession для CI/CD
- **APScheduler (existing)**: Background jobs для pre-generation — расширение существующего scheduler, без отдельных воркеров

**Критические выборы:**
- **Не использовать Redis** — PostgreSQL достаточно для 12 гороскопов, Redis addon = +$5-10/мес без явной выгоды
- **Не использовать Celery/ARQ** — overkill для 12 гороскопов каждые 12 часов
- **Не использовать self-hosted Stable Diffusion** — Together.ai free tier решает задачу

**Версии:**
```
sentry-sdk==2.50.0
telethon==1.42.0
playwright==1.50.0
```

### Expected Features

**Must have (table stakes):**
- **Typing indicator во время AI generation** — Telegram native UX pattern, без него кажется что бот завис
- **Быстрый ответ на /start (<1 сек)** — первое впечатление критично
- **Кэширование общих гороскопов** — 12 знаков x AI call = дорого и медленно
- **Markdown/HTML корректное форматирование** — видимая разметка выглядит непрофессионально
- **Изображение welcome screen** — визуальный хук для engagement
- **BotFather description** — SEO в Telegram поиске

**Should have (competitive advantage):**
- **AI-generated изображения знаков зодиака** — 12 изображений в едином стиле вместо stock photos, узнаваемость бренда
- **Визуальное разделение free vs premium** — решает pain point "непонятно за что платят"
- **Soft paywall после value delivery** — конверсия выше после демонстрации ценности
- **Progress bar/messages при длинных операциях** — UX сигнал что бот работает

**Defer (v2+):**
- **Onboarding с интерактивными slides** — HIGH complexity, можно добавить в v3+
- **Персонализированные изображения таро** — VERY HIGH cost (генерация для каждого запроса), defer
- **Детальная gamification** — отвлекает от core value

**Anti-features (не добавлять):**
- Real-time AI streaming в сообщения — Telegram rate limits делают это невозможным
- 78 custom таро-карт — overkill, фокус на интерпретации
- Ежедневные push с изображением — bandwidth cost explosion
- Детальная натальная карта inline — Telegram 4096 char limit, уже решено через Telegraph

### Architecture Approach

**Модульный монолит остаётся** — v2.0 добавляет новые сервисы и таблицы в существующую структуру, без выделения в микросервисы.

**Новые компоненты v2.0:**

1. **Image Storage** — PostgreSQL таблица `zodiac_images` с Telegram file_id (не blob storage)
   - Паттерн: Upload once → получить file_id → сохранить в БД → повторная отправка по file_id (бесплатно, мгновенно)

2. **Caching Layer** — PostgreSQL таблица `horoscope_cache` с TTL через expires_at (не Redis)
   - Fallback на in-memory при недоступности БД
   - Warm-up при старте из БД

3. **Background Jobs** — расширение APScheduler с новыми jobs:
   - `pregenerate_horoscopes` — каждые 12 часов генерировать все 12 знаков
   - `collect_daily_metrics` — snapshot метрик в БД

4. **Monitoring** — Prometheus metrics через `prometheus-fastapi-instrumentator`
   - Custom metrics: `horoscopes_generated_total`, `active_subscribers`, `api_cost_cents_total`
   - Extended `/health` endpoint с проверками DB, scheduler
   - PostgreSQL таблица `metric_snapshots` для historical data

**Модель данных:**
```python
# Новые таблицы
class ZodiacImage(Base):
    zodiac_sign: str (unique)
    telegram_file_id: str
    image_type: str

class HoroscopeCache(Base):
    zodiac_sign: str (primary key)
    cache_date: date
    horoscope_text: text
    generated_at: timestamp

class MetricSnapshot(Base):
    date: date
    metric_name: str
    value: float
    metadata: jsonb
```

**Интеграционные точки:**
- `src/services/ai/cache.py` — заменить in-memory на PostgreSQL (с fallback)
- `src/services/scheduler.py` — добавить pre-generation job
- `src/bot/handlers/horoscope.py` — интегрировать отправку с изображениями
- `src/main.py` — добавить Sentry init, Prometheus instrumentator

### Critical Pitfalls

1. **In-Memory Cache Lost on Railway Restart** — гороскопы генерируются заново после каждого deploy
   - **Как избежать:** PostgreSQL-backed cache с warm-up при старте, фоновая pre-generation

2. **Telegram file_id Not Cached** — повторная загрузка одних и тех же картинок
   - **Как избежать:** Сохранять file_id после первой отправки в БД/config, использовать cached ID для всех последующих

3. **APScheduler Jobs Lost After Redeploy** — pre-generation не работает после Railway restart
   - **Как избежать:** `misfire_grace_time=None`, startup check для missed jobs, verification job после generation

4. **Cache Race Condition** — два пользователя получают разные "сегодняшние" гороскопы
   - **Как избежать:** Lock per zodiac sign при генерации, timezone-aware expiration (Europe/Moscow)

5. **sendPhoto без Chat Action** — пользователь думает бот завис
   - **Как избежать:** `ChatActionSender.upload_photo()` context manager при отправке картинок

6. **Monitoring Cardinality Explosion** — Prometheus падает от метрик с user_id в labels
   - **Как избежать:** Только low-cardinality labels (zodiac, subscription_type), НЕ использовать user_id/session_id

7. **Картинки >10MB** — sendPhoto fails
   - **Как избежать:** PIL optimization (resize + quality=85), pre-check размера перед отправкой

## Implications for Roadmap

На основе исследования рекомендуется **5 фаз v2.0:**

### Phase 1: Performance & UX Quick Wins

**Rationale:** Критические UX исправления без новых зависимостей. Максимальный impact на user experience. Можно деплоить отдельно и быстро.

**Delivers:**
- Typing indicator во время AI generation
- Markdown/HTML корректное форматирование
- BotFather description для SEO
- Progress messages при AI операциях

**Addresses features:**
- Table stakes: typing indicator, markdown fix, BotFather (FEATURES.md)

**Avoids pitfalls:**
- Pitfall #5: sendPhoto без chat action (PITFALLS.md)

**Complexity:** LOW — только изменения в handlers, без новых таблиц

---

### Phase 2: Caching & Background Jobs

**Rationale:** Фундамент performance. Снижение latency и AI costs. Dependency для Phase 3 (изображения используют pre-generated кэш).

**Delivers:**
- PostgreSQL-backed cache для гороскопов
- Фоновая генерация 12 гороскопов каждые 12ч
- Warm cache при startup
- Lock для предотвращения race conditions

**Uses stack:**
- PostgreSQL (STACK.md: "достаточная скорость, persistence, дешевле Redis")
- APScheduler (STACK.md: "расширить существующий, не нужен Celery")

**Implements architecture:**
- Caching Layer (ARCHITECTURE.md: horoscope_cache table)
- Background Jobs (ARCHITECTURE.md: pregenerate_horoscopes job)

**Avoids pitfalls:**
- Pitfall #1: In-memory cache loss (PITFALLS.md)
- Pitfall #3: APScheduler jobs lost (PITFALLS.md)
- Pitfall #4: Cache race condition (PITFALLS.md)
- Pitfall #10: Timezone mismatch (PITFALLS.md)

**Complexity:** MEDIUM — миграция БД, scheduler setup, error handling

---

### Phase 3: Visual Enhancement

**Rationale:** Визуальное улучшение после performance fixes. Требует работающего кэша из Phase 2 (картинки отправляются с кэшированными гороскопами).

**Delivers:**
- 12 AI-generated zodiac images (Together.ai)
- Welcome screen image
- file_id caching для мгновенной отправки
- Premium vs free visual distinction
- Paywall image

**Uses stack:**
- Together.ai + FLUX.1 [schnell] (STACK.md: "бесплатно 3 месяца unlimited")
- PostgreSQL для file_id storage (ARCHITECTURE.md: zodiac_images table)

**Implements architecture:**
- Image Storage component (ARCHITECTURE.md: Upload once, serve by file_id)

**Addresses features:**
- Table stakes: welcome image (FEATURES.md)
- Differentiators: AI zodiac images, premium visual distinction (FEATURES.md)

**Avoids pitfalls:**
- Pitfall #2: file_id not cached (PITFALLS.md)
- Pitfall #6: Image size >10MB (PITFALLS.md)
- Pitfall #8: UI changes break flow (PITFALLS.md)

**Complexity:** HIGH — AI image generation, consistency, PIL optimization

---

### Phase 4: Monitoring

**Rationale:** Observability после основного функционала. Нужен работающий v2.0 чтобы собирать метрики.

**Delivers:**
- Sentry integration для errors & performance
- Prometheus metrics (horoscopes, costs, subscribers)
- Extended /health endpoint
- Metrics history в PostgreSQL

**Uses stack:**
- Sentry.io (STACK.md: "5K events бесплатно, FastAPI native")
- prometheus-fastapi-instrumentator (STACK.md)

**Implements architecture:**
- Monitoring component (ARCHITECTURE.md: Prometheus metrics, MetricSnapshot table)

**Avoids pitfalls:**
- Pitfall #7: Cardinality explosion (PITFALLS.md)
- Pitfall #9: Silent job failures (PITFALLS.md)

**Complexity:** MEDIUM — metrics design, cardinality control, alerting

---

### Phase 5: Testing & Validation

**Rationale:** Автоматизация тестирования финального v2.0. Включает интеграционные тесты через Telegram API.

**Delivers:**
- Telethon integration для Telegram testing
- Playwright для admin panel testing
- E2E тесты horoscope flow
- Image delivery тесты

**Uses stack:**
- Telethon (STACK.md: "активная разработка, StringSession для CI")
- Playwright (STACK.md: "для web testing админки")

**Complexity:** MEDIUM — StringSession generation, async test setup

---

### Phase Ordering Rationale

**Dependencies:**
- Phase 3 (Images) требует Phase 2 (Cache) — картинки отправляются с кэшированными гороскопами
- Phase 4 (Monitoring) требует Phase 2, 3 — нужны jobs и image delivery для метрик
- Phase 5 (Testing) требует все предыдущие — тестирует финальный функционал

**Grouping:**
- Phase 1 — quick wins, независимые изменения
- Phase 2 — foundation (cache + jobs), dependency для остальных
- Phase 3 — visuals, самостоятельная ценность
- Phase 4 — observability, критично но не блокирует UX
- Phase 5 — validation, финальная проверка

**Risk mitigation:**
- Phase 1 и 2 решают критичные pitfalls (#1, #3, #4, #5) до визуальных изменений
- Phase 3 внедряет картинки после performance fixes
- Phase 4 добавляет мониторинг для отслеживания проблем

### Research Flags

**Phases needing deeper research:**
- **Phase 3 (Visual Enhancement):** Требует `/gsd:research-phase` для Together.ai API нюансов, FLUX.1 prompt engineering, style consistency между 12 изображениями
- **Phase 5 (Testing):** Может потребовать исследование Telethon StringSession best practices, async test patterns

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (UX Quick Wins):** Стандартные aiogram patterns, документация полная
- **Phase 2 (Caching & Jobs):** APScheduler и PostgreSQL хорошо документированы, паттерны известны
- **Phase 4 (Monitoring):** Sentry и Prometheus имеют official FastAPI integrations

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | Все технологии имеют official docs, pricing verified, compatibility подтверждена |
| Features | **MEDIUM** | Основано на WebSearch + Telegram docs + codebase analysis. Нет direct user feedback для v2.0 prioritization |
| Architecture | **HIGH** | Расширение существующей v1.0 архитектуры, patterns проверены в production |
| Pitfalls | **HIGH** | Основано на official docs (aiogram, APScheduler, Telegram API) + community experience (GitHub issues, blog posts) |

**Overall confidence:** **HIGH**

### Gaps to Address

**Performance baseline unknown:**
- Текущая latency гороскопов не измерена — нужно добавить baseline metrics перед Phase 2
- AI costs per day неизвестны — tracking в Phase 4 покажет, но может потребовать adjustment budget

**Image generation consistency:**
- Together.ai FLUX.1 prompt consistency для 12 знаков нужно протестировать
- Может потребоваться несколько итераций для единого стиля
- Рекомендация: Генерировать все 12 в одной сессии с одним seed/reference image

**User timezone handling:**
- Гороскопы "сегодня" для пользователей в разных timezone не продуман
- Текущая архитектура: один кэш для всех, expires в 00:00 Moscow
- Gap: Пользователь в Владивостоке (+7 часов) получает "вчерашний" гороскоп утром
- Решение: Defer to v3.0 (добавить timezone detection) или принять limitation для MVP

**Railway cost projection:**
- v2.0 добавляет image storage, metrics history — рост БД не оценён
- Recommendation: Monitor Railway usage в Phase 4, set alert при 80% quota

## Sources

### Primary (HIGH confidence)
- **Together.ai:**
  - [Together.ai Flux Blog](https://www.together.ai/blog/flux-api-is-now-available-on-together-ai-new-pro-free-access-to-flux-schnell) — free tier info
  - [Together.ai Pricing](https://www.together.ai/pricing) — verified 3 months unlimited

- **Sentry:**
  - [Sentry FastAPI Docs](https://docs.sentry.io/platforms/python/integrations/fastapi/)
  - [Sentry Pricing](https://sentry.io/pricing/) — 5K events confirmed

- **Telegram Bot API:**
  - [sendPhoto documentation](https://docs.aiogram.dev/en/dev-3.x/api/methods/send_photo.html)
  - [File upload & file_id](https://core.telegram.org/bots/api#sending-files)
  - [Chat Actions](https://docs.aiogram.dev/en/latest/api/methods/send_chat_action.html)
  - [Telegram file size limits](https://limits.tginfo.me/en)

- **APScheduler:**
  - [User guide — misfire handling](https://apscheduler.readthedocs.io/en/3.x/userguide.html)
  - [SQLAlchemyJobStore](https://apscheduler.readthedocs.io/en/3.x/userguide.html#configuring-the-scheduler)

- **Telethon:**
  - [Telethon GitHub](https://github.com/LonamiWebs/Telethon)
  - [Telethon Docs](https://docs.telethon.dev/en/stable/)

### Secondary (MEDIUM confidence)
- **Image Generation Comparison:**
  - [WaveSpeedAI Guide](https://wavespeed.ai/blog/posts/complete-guide-ai-image-apis-2026/) — API comparison
  - [CGDream Tarot Generator](https://cgdream.ai/features/ai-tarot-card-generator)

- **Performance & Caching:**
  - [Redis vs PostgreSQL caching](https://dizzy.zone/2025/09/24/Redis-is-fast-Ill-cache-in-Postgres/)
  - [Optimising Telegram Bot Response Times](https://dev.to/imthedeveloper/optimising-telegram-bot-response-times-1a64)

- **Monitoring:**
  - [Prometheus cardinality management](https://last9.io/blog/how-to-manage-high-cardinality-metrics-in-prometheus/)
  - [Telegram Bot Analytics Metrics](https://bazucompany.com/blog/telegram-bot-analytics-metrics-you-must-track/)

### Tertiary (LOW confidence)
- **Onboarding patterns:**
  - [Telegram Onboarding Kit](https://github.com/Easterok/telegram-onboarding-kit) — needs validation for AdtroBot use case

---
*Research completed: 2026-01-23*
*Ready for roadmap: yes*
