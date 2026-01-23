---
phase: 12
plan: 03
subsystem: horoscope-integration
tags: [postgresql, cache, dashboard, metrics]
dependency-graph:
  requires: ["12-02"]
  provides: ["horoscope-cache-integration"]
  affects: ["admin-dashboard", "bot-handlers"]
tech-stack:
  added: []
  patterns: ["service-layer-integration", "view-tracking"]
key-files:
  created: []
  modified:
    - src/bot/utils/horoscope.py
    - src/admin/services/analytics.py
decisions: []
metrics:
  duration: "2 min"
  completed: "2026-01-23"
---

# Phase 12 Plan 03: Horoscope Cache Integration Summary

**One-liner:** Интеграция HoroscopeCacheService в bot handlers и admin dashboard с реальным подсчётом просмотров

## What Changed

### src/bot/utils/horoscope.py
- **Было:** Прямой вызов AI service для каждого запроса гороскопа
- **Стало:** Делегирование HoroscopeCacheService через async_session_maker
- Функция `get_horoscope_text` теперь:
  1. Получает singleton HoroscopeCacheService
  2. Открывает сессию через async_session_maker
  3. Вызывает `cache_service.get_horoscope()` (который обрабатывает кэш, генерацию, view tracking)
  4. Возвращает fallback message если кэш пуст и генерация не удалась

### src/admin/services/analytics.py
- **Было:** `horoscopes_today = 0` (хардкод, TODO комментарий)
- **Стало:** Реальный запрос к `horoscope_views` таблице
- Добавлен импорт `HoroscopeView` модели
- Запрос суммирует `view_count` за сегодня
- Добавлен расчёт тренда vs вчера

## Commits

| Hash | Message |
|------|---------|
| 91b2080 | feat(12-03): update get_horoscope_text to use HoroscopeCacheService |
| d268f82 | feat(12-03): show real horoscope views in admin dashboard |

## Key Links Verified

- `src/bot/utils/horoscope.py` -> `src/services/horoscope_cache.py` via `from src.services.horoscope_cache import get_horoscope_cache_service`
- `src/admin/services/analytics.py` -> `src/db/models/horoscope_cache.py` via `from src.db.models import HoroscopeView`

## Deviations from Plan

None - план выполнен точно как написано.

## Verification Results

1. get_horoscope_text imports get_horoscope_cache_service - OK
2. get_horoscope_text uses async_session_maker - OK
3. No direct AI service call in horoscope.py - OK (delegated to cache service)
4. Admin analytics imports HoroscopeView - OK
5. horoscopes_today query sums view_count WHERE view_date = today - OK
6. Trend calculation compares today vs yesterday - OK

## Data Flow (Complete Picture)

```
User requests horoscope
    |
    v
get_horoscope_text(zodiac_name, zodiac_name_ru)
    |
    v
HoroscopeCacheService.get_horoscope()
    |
    +--> Cache HIT: Return content, increment view
    |
    +--> Cache MISS: Generate via AI, save to cache, increment view
    |
    v
horoscope_views table (view_count++)
    |
    v
Admin dashboard queries horoscope_views for metrics
```

## Phase 12 Completion Status

With this plan complete:
- [x] 12-01: Database models and migrations (horoscope_cache, horoscope_views tables)
- [x] 12-02: HoroscopeCacheService with cache warming and scheduled generation
- [x] 12-03: Integration into bot handlers and admin dashboard

**Phase 12 complete.** PostgreSQL-backed horoscope caching fully integrated.

## Next Phase Readiness

Phase 12 завершена. Готовность к Phase 13 (AI Image Generation):
- Horoscope система полностью готова
- Можно добавлять изображения к гороскопам в следующей фазе
