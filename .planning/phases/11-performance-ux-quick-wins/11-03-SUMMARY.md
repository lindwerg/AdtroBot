---
phase: 11
plan: 03
subsystem: bot-ux
tags: [horoscope, onboarding, headers, premium-teaser, markdown]

dependency_graph:
  requires:
    - phase: 11-01
      provides: generate_with_feedback helper for typing indicator
  provides:
    - general-vs-personal-horoscope-headers
    - improved-first-forecast-flow
    - updated-premium-teaser
  affects:
    - phase-12 (may want to cache horoscope headers)

tech_stack:
  added: []
  patterns:
    - show_horoscope_message import for reuse
    - entity-based formatting with aiogram.utils.formatting

key_files:
  created: []
  modified:
    - src/bot/handlers/horoscope.py
    - src/bot/handlers/start.py

decisions:
  - "Entity-based formatting (Bold, BlockQuote) already handles formatting correctly - ParseMode not needed"
  - "AI prompts use [SECTION] plain text, not Markdown syntax"

metrics:
  duration: ~5 min
  completed: 2026-01-23
---

# Phase 11 Plan 03: Horoscope UX & Markdown Formatting Summary

**One-liner:** Визуальное разделение Общий/Персональный гороскоп в заголовках + улучшенный first forecast после onboarding

## Performance

- **Duration:** ~5 min
- **Started:** 2026-01-23T22:30:00Z
- **Completed:** 2026-01-23T22:35:00Z
- **Tasks:** 4 (2 with code changes, 2 verification-only)
- **Files modified:** 2

## Accomplishments

- Заголовки гороскопов четко различают "Общий" и "Персональный" тип
- PREMIUM_TEASER обновлен с объяснением разницы и призывом к действию
- После onboarding пользователь видит реальный гороскоп (не mock) с объяснением типов
- Проверена корректность entity-based formatting (ParseMode не требуется)

## Task Commits

Each task was committed atomically:

1. **Task 1: Обновить заголовки гороскопов** - `26a6a19` (feat)
2. **Task 2: Улучшить первый прогноз после onboarding** - `e2a6c52` (feat)
3. **Task 3: Проверить UX для premium пользователей** - no changes (verification)
4. **Task 4: Исправить Markdown форматирование** - no changes (verified entity-based approach works)

## Files Created/Modified

- `src/bot/handlers/horoscope.py` - Обновлены заголовки "Общий гороскоп" / "Персональный гороскоп", новый PREMIUM_TEASER
- `src/bot/handlers/start.py` - Импорт show_horoscope_message, реальный гороскоп после onboarding, объяснение типов

## Decisions Made

1. **Entity-based formatting достаточен** - aiogram.utils.formatting.Text с Bold/BlockQuote использует entities, не Markdown синтаксис. ParseMode не нужен.
2. **AI промпты не используют Markdown** - Они используют `[СЕКЦИЯ]` заголовки в plain text формате.
3. **Premium автоматически получает персональный** - Кнопки выбора типа гороскопа НЕ добавлены, чтобы не усложнять UX.

## Deviations from Plan

None - план выполнен точно. Task 3 и Task 4 были verification-only (без изменений кода).

## Issues Encountered

- `uv run python` не работает из-за конфигурации poetry - использовал `python3 -m py_compile` для проверки синтаксиса

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Blockers:** None
**Ready for:** Any Phase 11 plan (11-04+) or Phase 12

---
*Phase: 11-performance-ux-quick-wins*
*Completed: 2026-01-23*
