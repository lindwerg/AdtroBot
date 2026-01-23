# Phase 12: Caching & Background Jobs - Context

**Gathered:** 2026-01-23
**Status:** Ready for planning

<domain>
## Phase Boundary

PostgreSQL-backed кэширование гороскопов с автоматической фоновой генерацией каждые 24 часа (в 00:00). Гороскопы возвращаются мгновенно из кэша (<500ms), AI генерация происходит в фоне. После restart приложения кэш восстанавливается из PostgreSQL.

</domain>

<decisions>
## Implementation Decisions

### Cache invalidation strategy
- **TTL:** 24 часа (daily invalidation)
- **Время генерации:** 00:00 (midnight) — генерация новых гороскопов на следующий день
- **Error handling:** Retry с backoff (5/10/30 мин) — 3 попытки, затем skip
- **Total failure:** Показать error message пользователю если все retry провалились

### Background job scheduling
- **Scheduler:** Claude выбирает решение (APScheduler или альтернатива)
- **Execution mode:** Sequential (один за другим) — 12 гороскопов генерируются по очереди
- **Retry logic:** 3 попытки с backoff (5/10/30 мин)
- **Restart behavior:** Timezone-aware — проверять актуальность гороскопов для текущих суток пользователя (не перегенерировать если кэш свежий)

### Cache miss handling
- **Cache miss action:** Generate on-demand (wait) — пользователь ждёт генерации
- **Race condition protection:** Асинхронная генерация — несколько пользователей не блокируют друг друга, но дублирование предотвращается
- **In-progress generation:** Гороскопы генерируются заранее в фоне (00:00), cache miss — редкий случай (первый запуск, после сбоя)
- **UX during wait:** Progress message («Генерирую гороскоп...»)

### Storage & persistence
- **Storage model:** Claude выбирает структуру (separate cache table или другое)
- **Retention:** Only current (24h) — хранить только сегодняшние гороскопы, удалять устаревшие
- **Cleanup strategy:** Claude выбирает подход (before generation или separate job)
- **Metrics tracking:** Separate analytics table для horoscopes_today (количество просмотров)

### Claude's Discretion
- Конкретный scheduler (APScheduler, Celery, другое)
- Структура таблицы кэша
- Cleanup механизм для старых гороскопов
- Race condition protection механизм

</decisions>

<specifics>
## Specific Ideas

- Гороскопы привязаны к timezone пользователя — при restart проверять актуальность для текущих суток
- Асинхронность критична — много пользователей не должны блокировать друг друга
- Cache miss — редкий случай (первый запуск, после сбоя), основной flow — из кэша

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-caching-background-jobs*
*Context gathered: 2026-01-23*
