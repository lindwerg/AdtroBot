# Phase 16: Testing & Polish - Context

**Gathered:** 2026-01-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Автоматизированное тестирование критических flows (Playwright для админки, Telethon для бота) с полным покрытием функционала. Все найденные баги документируются в BUGS.md для последующего исправления в отдельной фазе. Polish включает максимальное улучшение UX на основе findings.

**Это НЕ добавление нового функционала** — это проверка и полировка того, что уже существует.

</domain>

<decisions>
## Implementation Decisions

### Test Coverage Scope

**Bot (Telethon E2E):**
- Полное покрытие: все команды, все стейты, все едж-кейсы
- Все 12 знаков зодиака протестированы
- Все типы расклядов таро покрыты
- Real API calls для AI (OpenRouter) — не mock, реальная интеграция
- Mock для платежей (YooKassa webhooks) — эмуляция webhook'ов для проверки логики
- Production bot используется для тестов (тестовые данные с cleanup)

**Admin (Playwright):**
- Полное покрытие: все страницы, все формы, все взаимодействия
- Login, dashboard, messaging, payments
- Monitoring: графики, фильтры, metrics (новый функционал v2.0)
- Все критические и некритические flows

**Performance:**
- Полный load testing для всех endpoints
- Проверка SLA из success criteria:
  - Кэшированные гороскопы: <500ms
  - /start: <1s
  - Другие критичные операции

**CI Integration:**
- "Все пушится потом смотрим на продукте" — manual deployment verification
- Тесты запускаются локально перед push
- Production verification после deployment

### Test Data Strategy

**Test Users & Data:**
- Максимальный подход: DB seed script + Factories (Faker) для разнообразия
- SQL скрипт для базовых сценариев
- Faker для генерации вариативных данных на лету

**Isolation:**
- Manual cleanup в tearDown
- Production bot использует production DB
- Cleanup тестовых данных после каждого теста

**Test Secrets:**
- Claude's discretion: выбор стандартного подхода (.env.test или env vars)

**Data Coverage:**
- Полное покрытие: все 12 знаков зодиака
- Все типы таро расклядов
- Все edge cases и error scenarios

### Bug Triage Approach

**Bug Discovery:**
- Все найденные баги записываются в BUGS.md
- НЕ фиксим в этой фазе — документируем для следующей фазы

**Bug Format (BUGS.md):**
- Таблица с полями:
  - ID
  - Category (Bot/Admin/Backend/Frontend)
  - Severity (P0/P1/P2)
  - Status (Open/Fixed/Deferred)
  - Component
  - Description
  - Steps to Reproduce

**Bug Categories:**
- Bot — Telegram bot issues
- Admin — Admin panel issues
- Backend — API/database/services
- Frontend — React UI issues

**Handling Strategy:**
- Minor bugs (typos, мелкие UX) → BUGS.md
- Regression bugs (работало в v1.0, сломалось в v2.0) → BUGS.md
- Flaky tests → немедленно чиним (flaky test = баг в тесте)

### Polish Criteria

**Bot Polish (максимальное качество):**
- Быстрые ответы
- Четкие сообщения
- Изображения
- Smooth UX

**Admin Polish (максимальное качество):**
- Четкая навигация
- Loading states
- Графики работают быстро
- Filters responsive

**UX Improvements (все максимально):**
- Error messages — понятные сообщения об ошибках
- Loading states — spinners, skeletons, progress indicators
- Validation feedback — мгновенный feedback на ввод
- Empty states — полезные подсказки при пустых данных

**Done Criteria:**
- Claude's discretion: определит разумный критерий завершения (вероятно "все тесты pass + основные UX improvements применены")

</decisions>

<specifics>
## Specific Ideas

**Real API Testing:**
- "Все реально смотрим" — использовать real OpenRouter API для проверки интеграции
- Не mock AI responses — реальные вызовы для confidence

**Production Bot Testing:**
- "Используем production bot" — тестовые данные в production DB с cleanup
- Осторожный подход: cleanup critical

**Максимальный подход:**
- "Все максимально" появляется в ответах на bot polish, admin polish, UX improvements
- Пользователь хочет максимального качества, не компромиссов

</specifics>

<deferred>
## Deferred Ideas

Баг фиксы — отдельная фаза после этой. Phase 16 документирует баги в BUGS.md, Phase 17 (или позже) займется их исправлением.

</deferred>

---

*Phase: 16-testing-and-polish*
*Context gathered: 2026-01-24*
