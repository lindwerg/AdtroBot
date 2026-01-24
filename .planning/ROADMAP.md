# Roadmap: AdtroBot

## Milestones

- **v1.0 MVP** - Phases 1-10 (shipped 2026-01-23)
- **v2.0 Production Polish & Visual Enhancement** - Phases 11-16 (in progress)

## Overview

v2.0 доводит MVP до production-ready состояния: критические UX-фиксы и performance optimization (Phase 11), PostgreSQL-backed кэширование гороскопов с фоновой генерацией (Phase 12), создание AI-изображений для всех ключевых моментов (Phase 13), интеграция визуалов в бот (Phase 14), полный monitoring stack (Phase 15), и автоматизированное тестирование с polish (Phase 16).

## Phases

**Phase Numbering:**
- Integer phases (11, 12, ...): Planned milestone work
- Decimal phases (12.1, 12.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 11: Performance & UX Quick Wins** - Критические UX-фиксы без новых зависимостей
- [x] **Phase 12: Caching & Background Jobs** - PostgreSQL cache + фоновая генерация гороскопов
- [x] **Phase 13: Image Generation** - Pexels stock images для рандомной отправки
- [x] **Phase 14: Visual Integration** - Интеграция изображений в бот + onboarding
- [ ] **Phase 15: Monitoring & Observability** - Prometheus metrics + health checks + dashboard
- [ ] **Phase 16: Testing & Polish** - Playwright + Telethon тесты + admin improvements

## Phase Details

### Phase 11: Performance & UX Quick Wins
**Goal**: Пользователи получают быстрые ответы с понятным feedback и профессиональным форматированием
**Depends on**: v1.0 (Phase 10)
**Requirements**: PERF-01, PERF-04, UX-01, UX-02, UX-03, UX-04, WEL-01, WEL-02, WEL-04
**Success Criteria** (what must be TRUE):
  1. Пользователь видит typing indicator во время AI генерации (гороскоп, таро, натальная карта)
  2. /start отвечает меньше чем за 1 секунду
  3. Markdown разметка не видна в сообщениях (корректный parse_mode)
  4. Пользователь понимает разницу между общим и персональным гороскопом
  5. BotFather description настроен для поиска бота
**Plans**: 3 plans

Plans:
- [x] 11-01-PLAN.md — Typing indicators + progress messages для AI операций
- [x] 11-02-PLAN.md — Welcome flow: engaging текст, /help, /about, BotFather setup
- [x] 11-03-PLAN.md — UX гороскопов: разделение общий/персональный, улучшенный onboarding

### Phase 12: Caching & Background Jobs
**Goal**: Гороскопы загружаются мгновенно из кэша, AI генерация происходит в фоне
**Depends on**: Phase 11
**Requirements**: PERF-02, PERF-03, PERF-06, PERF-07, MON-01
**Success Criteria** (what must be TRUE):
  1. Гороскоп для любого знака возвращается за <500ms (из кэша)
  2. 12 гороскопов автоматически генерируются каждые 24 часа (00:00) в фоне
  3. После restart приложения кэш восстанавливается из PostgreSQL
  4. horoscopes_today показывает реальное количество просмотров в админке
  5. Race condition при одновременных запросах не создает дубликатов генерации
**Plans**: 3 plans

Plans:
- [x] 12-01-PLAN.md — PostgreSQL schema: HoroscopeCache + HoroscopeView tables
- [x] 12-02-PLAN.md — HoroscopeCacheService с per-key locking + background job
- [x] 12-03-PLAN.md — Интеграция в handlers + admin dashboard

### Phase 13: Image Generation
**Goal**: Все изображения скачаны из Pexels и готовы к интеграции
**Depends on**: Phase 11 (независимо от Phase 12, но логически после UX fixes)
**Requirements**: IMG-01, IMG-02, IMG-03, IMG-04, IMG-05, IMG-06, IMG-07
**Success Criteria** (what must be TRUE):
  1. Выбран источник изображений (Pexels stock) и скачаны
  2. 43 космических изображения готовы для рандомной отправки
  3. Изображения в assets/images/cosmic/
**Plans**: 1 plan

Plans:
- [x] 13-01-PLAN.md — Скачивание 43 космических изображений с Pexels

### Phase 14: Visual Integration
**Goal**: Пользователи видят красивые изображения во всех ключевых моментах бота
**Depends on**: Phase 12, Phase 13 (нужен кэш + готовые изображения)
**Requirements**: VIS-01, VIS-02, VIS-03, VIS-04, VIS-05, VIS-06, VIS-07, PERF-05, WEL-03
**Success Criteria** (what must be TRUE):
  1. /start показывает космическое изображение
  2. Гороскоп сопровождается космическим изображением
  3. Расклады таро показывают космическое изображение перед раскладом
  4. Изображения отправляются по file_id (мгновенно, без повторной загрузки)
  5. ImageAsset model хранит file_id в PostgreSQL
**Plans**: 2 plans

Plans:
- [x] 14-01-PLAN.md — ImageAsset model + ImageAssetService с file_id кэшированием
- [x] 14-02-PLAN.md — Интеграция изображений в handlers (start, horoscope, tarot)

### Phase 15: Monitoring & Observability
**Goal**: Полная видимость состояния бота, затрат и метрик в реальном времени
**Depends on**: Phase 14 (мониторинг после основного функционала)
**Requirements**: MON-02, MON-03, MON-04, MON-05, MON-06
**Success Criteria** (what must be TRUE):
  1. Bot Health metrics (uptime, errors, response time) доступны в админке
  2. API Costs отслеживаются по операциям (OpenRouter spending)
  3. Unit economics dashboard показывает cost per user
  4. /health endpoint возвращает статус DB, scheduler, и основных сервисов
  5. Prometheus metrics доступны для внешнего мониторинга
**Plans**: 3 plans

Plans:
- [x] 15-01-PLAN.md — AIUsage model + Prometheus metrics + расширенный /health endpoint
- [x] 15-02-PLAN.md — Cost tracking интеграция в AIService + admin /monitoring API
- [x] 15-03-PLAN.md — Monitoring.tsx dashboard в админке с графиками и фильтрами

### Phase 16: Testing & Polish
**Goal**: Автоматизированные тесты покрывают критические flows, найденные баги исправлены
**Depends on**: Phase 15 (тестирование после всего функционала)
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07, ADMIN-01, ADMIN-02, ADMIN-03
**Success Criteria** (what must be TRUE):
  1. Playwright тесты проходят для критических admin flows (login, dashboard, messaging)
  2. Telethon тесты проверяют основные bot flows (/start, гороскоп, таро)
  3. Все найденные баги в админке исправлены
  4. Все найденные баги в боте исправлены
  5. Admin panel UX улучшен на основе findings (навигация, загрузка)
**Plans**: TBD

Plans:
- [ ] 16-01: TBD
- [ ] 16-02: TBD
- [ ] 16-03: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 11 -> 11.1 -> 11.2 -> 12 -> ... -> 16

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 11. Performance & UX Quick Wins | v2.0 | 3/3 | Complete | 2026-01-23 |
| 12. Caching & Background Jobs | v2.0 | 3/3 | Complete | 2026-01-23 |
| 13. Image Generation | v2.0 | 1/1 | Complete | 2026-01-24 |
| 14. Visual Integration | v2.0 | 2/2 | Complete | 2026-01-24 |
| 15. Monitoring & Observability | v2.0 | 3/3 | Gap found | 2026-01-24 |
| 16. Testing & Polish | v2.0 | 0/TBD | Not started | - |

---
*Roadmap created: 2026-01-23*
*Last updated: 2026-01-24 (Phase 15 planned)*
