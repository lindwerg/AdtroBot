# Phase 15: Monitoring & Observability - Context

**Gathered:** 2026-01-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Полная видимость состояния бота, затрат и метрик в реальном времени. Включает Bot Health metrics, API Costs tracking, unit economics dashboard, /health endpoint, и Prometheus metrics для внешнего мониторинга.

</domain>

<decisions>
## Implementation Decisions

### Метрики Bot Health
- Расширенный набор: uptime, errors count, response time, requests/sec, active users (DAU/MAU/WAU), queue depth
- DAU (24h), WAU (7 days), MAU (30 days) — все три показателя
- Errors breakdown по handler + error type (детальная аналитика)
- Background queue: pending + failed + completed count (разделение по статусам)

### Dashboard и визуализация
- Отдельная страница `/monitoring` в админке (не на главной)
- Интерактивный dashboard с фильтрами по времени (day/week/month)
- По умолчанию: Last 7 days (фильтры: 24h/30d)
- Графики + таблицы для unit economics

### Health Checks
- Проверки: Database connection, APScheduler status, OpenRouter API, Telegram Bot API (все 4)
- Формат: JSON + HTTP status codes (200 OK / 503 Service Unavailable)
- Unhealthy критерий: любая проверка failed → система unhealthy
- Timeout разные по checks: DB 3s, scheduler 2s, API calls 10s

### Prometheus интеграция
- Endpoint: `/metrics` (стандартный Prometheus endpoint)
- Custom metrics экспортировать:
  - Request counters (total requests, by handler, by user)
  - Error counters (by type, by handler)
  - AI operation metrics (requests, tokens used, latency)
  - Business metrics (DAU/MAU/WAU, subscription conversions, revenue)
- Naming convention: `adtrobot_*` prefix (понятно и явно)
- Все metrics доступны и в Prometheus, и во встроенной админке

### API Cost Tracking
- Группировка по:
  - Типу операции (horoscope, tarot, natal chart)
  - User_id (cost per user)
  - Времени (тренды по дням/неделям/месяцам)
  - Model (OpenRouter: gpt-4, claude, etc.)
- Unit Economics: cost per DAU vs cost per paying user (разделение free/paid)
- OpenRouter spending: комбинированный подход (приоритет API cost field, fallback на вычисление по tokens)
- Alerts на превышение бюджета: visual warning в админке (banner)

### Claude's Discretion
- Exact dashboard layout и цветовая схема
- Детали визуализации графиков (line/bar/area)
- Форматирование чисел и единиц измерения
- Структура БД для хранения metrics history

</decisions>

<specifics>
## Specific Ideas

- Dashboard должен быть **интерактивным** с фильтрами — не просто статичные цифры
- Alerts в админке как **visual warning banner** — заметно, но не навязчиво
- Prometheus metrics доступны **без авторизации** (standard `/metrics`)
- Unit economics показывает **разницу между всеми юзерами и платящими** — ключевая бизнес-метрика

</specifics>

<deferred>
## Deferred Ideas

Нет — обсуждение осталось в рамках фазы.

</deferred>

---

*Phase: 15-monitoring-observability*
*Context gathered: 2026-01-24*
