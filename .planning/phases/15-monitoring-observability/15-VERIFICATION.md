---
phase: 15-monitoring-observability
verified: 2026-01-24T12:21:17Z
status: gaps_found
score: 10/11 must-haves verified
gaps:
  - truth: "Dashboard показывает DAU/WAU/MAU в реальном времени"
    status: failed
    reason: "API endpoint в frontend клиенте некорректный - вызывает /monitoring вместо /admin/monitoring"
    artifacts:
      - path: "admin-frontend/src/api/monitoring.ts"
        issue: "Line 56: api.get<MonitoringData>(`/monitoring?range=${range}`) должно быть `/admin/monitoring?range=${range}`"
    missing:
      - "Исправить API endpoint в getMonitoringData() на /admin/monitoring"
---

# Phase 15: Monitoring & Observability Verification Report

**Phase Goal:** Полная видимость состояния бота, затрат и метрик в реальном времени  
**Verified:** 2026-01-24T12:21:17Z  
**Status:** gaps_found  
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | /health endpoint возвращает JSON со статусом всех сервисов | ✓ VERIFIED | src/main.py:169 вызывает run_all_checks, возвращает JSON с 4 checks (database, scheduler, openrouter, telegram) |
| 2 | /metrics endpoint возвращает Prometheus format | ✓ VERIFIED | src/main.py:101-112 настроен Instrumentator, /metrics endpoint смонтирован с make_asgi_app() |
| 3 | AIUsage таблица существует в БД для записи cost data | ✓ VERIFIED | src/db/models/ai_usage.py существует, миграция migrations/versions/2026_01_24_bb3aea586917_add_ai_usage_table.py создана |
| 4 | Каждый AI запрос записывает usage data в AIUsage таблицу | ✓ VERIFIED | src/services/ai/client.py:108 вызывает record_ai_usage после каждого AI запроса |
| 5 | Admin API /monitoring endpoint возвращает Bot Health и API Costs | ✓ VERIFIED | src/admin/router.py:622 возвращает get_monitoring_data с active_users, api_costs, unit_economics |
| 6 | DAU/WAU/MAU рассчитываются корректно | ✓ VERIFIED | src/admin/services/monitoring.py:28-59 корректно считает DAU/WAU/MAU из TarotSpread activity |
| 7 | Страница /monitoring доступна в админке | ✓ VERIFIED | admin-frontend/src/routes/index.tsx:57 route определён, Layout.tsx:27 menu item добавлен |
| 8 | Dashboard показывает DAU/WAU/MAU в реальном времени | ✗ FAILED | API endpoint некорректный - вызывает /monitoring вместо /admin/monitoring (см. gaps) |
| 9 | API Costs breakdown отображается по операциям | ✓ VERIFIED | Monitoring.tsx:219-243 рендерит таблицу с операциями из data.api_costs.by_operation |
| 10 | Unit Economics показывает cost per user | ✓ VERIFIED | Monitoring.tsx:267-291 отображает cost_per_active_user и cost_per_paying_user |
| 11 | Time filter (24h/7d/30d) работает | ✓ VERIFIED | Monitoring.tsx:92-100 Segmented меняет range state, useMonitoringData(range) обновляет запрос |

**Score:** 10/11 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/db/models/ai_usage.py` | AIUsage model | ✓ VERIFIED | 29 lines, класс AIUsage с 9 полями (user_id, operation, tokens, cost, latency) |
| `src/monitoring/metrics.py` | Prometheus metrics definitions | ✓ VERIFIED | 74 lines, 11 метрик с префиксом adtrobot_* (AI_COST_TOTAL, AI_TOKENS_TOTAL, etc.) |
| `src/monitoring/health.py` | Health check functions | ✓ VERIFIED | 115 lines, 4 check функции + run_all_checks orchestrator |
| `src/monitoring/cost_tracking.py` | Cost tracking utilities | ✓ VERIFIED | 132 lines, record_ai_usage и record_ai_error функции |
| `src/admin/services/monitoring.py` | Monitoring data aggregation | ✓ VERIFIED | 230 lines, get_monitoring_data, get_api_costs_data, get_active_users, get_unit_economics |
| `src/admin/schemas.py` | MonitoringResponse schema | ✓ VERIFIED | MonitoringResponse class на line 579-586 с active_users, api_costs, unit_economics, error_stats |
| `admin-frontend/src/pages/Monitoring.tsx` | Monitoring dashboard page | ✓ VERIFIED | 306 lines, полный dashboard с DAU/WAU/MAU, charts, tables |
| `admin-frontend/src/hooks/useMonitoring.ts` | React Query hook | ✓ VERIFIED | 11 lines, useMonitoringData с refetch каждые 60 сек |
| `admin-frontend/src/api/monitoring.ts` | API client | ⚠️ PARTIAL | 58 lines, TypeScript типы корректны, но API endpoint некорректный (см. gaps) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| src/main.py | src/monitoring/metrics.py | instrumentator setup | ✓ WIRED | Line 101: Instrumentator импортирован и настроен, /metrics mounted на line 112 |
| src/main.py | src/monitoring/health.py | health endpoint import | ✓ WIRED | Line 21: run_all_checks импортирован, line 169: вызывается в /health endpoint |
| src/services/ai/client.py | src/monitoring/cost_tracking.py | record_ai_usage call | ✓ WIRED | Line 9: импорт record_ai_usage, line 108: вызов после AI response |
| src/admin/router.py | src/admin/services/monitoring.py | GET /admin/monitoring | ✓ WIRED | Line 43: импорт get_monitoring_data, line 622: вызов в endpoint |
| admin-frontend/src/routes/index.tsx | admin-frontend/src/pages/Monitoring.tsx | route definition | ✓ WIRED | Line 57: route 'monitoring' → MonitoringPage |
| admin-frontend/src/components/Layout.tsx | /monitoring | menu item | ✓ WIRED | Line 27: menu item с path '/monitoring' и MonitorOutlined icon |

### Requirements Coverage

**Phase 15 Requirements (из REQUIREMENTS.md):**

| Requirement | Status | Blocking Issue |
|-------------|--------|---------------|
| MON-02: Bot Health metrics (uptime, errors, response time) | ✓ SATISFIED | /health endpoint работает с 4 checks |
| MON-03: API Costs tracking (OpenRouter spending по операциям) | ✓ SATISFIED | Cost tracking записывает все AI запросы, /admin/monitoring показывает breakdown |
| MON-04: Unit economics dashboard в админке | ⚠️ BLOCKED | Dashboard создан, но API endpoint некорректный |
| MON-05: Prometheus metrics интеграция | ✓ SATISFIED | 11 кастомных метрик определены, instrumentator настроен |
| MON-06: Расширенный /health endpoint | ✓ SATISFIED | 4 health checks (database, scheduler, openrouter, telegram) |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| src/admin/services/monitoring.py | 202 | TODO comment | ℹ️ Info | get_error_stats возвращает placeholder zeros - не критично, функция рабочая |
| admin-frontend/src/api/monitoring.ts | 56 | Incorrect API path | 🛑 Blocker | Вызывает /monitoring вместо /admin/monitoring - frontend не получит данные |

### Gaps Summary

**1 критический gap блокирует truth #8:**

Frontend клиент вызывает неправильный API endpoint. Backend endpoint `/admin/monitoring` работает корректно (проверено в router.py), но frontend API client вызывает `/monitoring?range=...` вместо `/admin/monitoring?range=...`.

**Impact:** Dashboard страница откроется, но не получит данные от backend (404 ошибка).

**Fix:** В файле `admin-frontend/src/api/monitoring.ts` line 56 изменить:
```typescript
const response = await api.get<MonitoringData>(`/monitoring?range=${range}`)
```
на:
```typescript
const response = await api.get<MonitoringData>(`/admin/monitoring?range=${range}`)
```

Все остальные компоненты (backend API, monitoring service, health checks, cost tracking, Prometheus metrics, frontend UI) реализованы корректно и substantive.

---

_Verified: 2026-01-24T12:21:17Z_  
_Verifier: Claude (gsd-verifier)_
