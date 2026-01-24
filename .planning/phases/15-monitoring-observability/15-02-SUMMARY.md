---
phase: 15-monitoring-observability
plan: 02
subsystem: monitoring
tags: [cost-tracking, prometheus, admin-api, unit-economics, dau-wau-mau]

# Dependency graph
requires:
  - phase: 15-01
    provides: AIUsage model, Prometheus metrics definitions
provides:
  - Cost tracking for all AI requests (record_ai_usage)
  - /admin/monitoring endpoint with DAU/WAU/MAU, API costs, unit economics
  - Prometheus metrics updates (tokens, cost, latency)
affects: [15-03-alerts, admin-dashboard-frontend]

# Tech tracking
tech-stack:
  added: []
  patterns: [cost tracking after AI response, unit economics calculation]

key-files:
  created:
    - src/monitoring/cost_tracking.py
    - src/admin/services/monitoring.py
  modified:
    - src/services/ai/client.py
    - src/admin/schemas.py
    - src/admin/router.py

key-decisions:
  - "Cost tracking runs inside AI service (not separate middleware) for accurate latency measurement"
  - "record_ai_usage wrapped in try/except - tracking failure doesn't break AI response"
  - "DAU/WAU/MAU calculated from TarotSpread activity (most reliable activity signal)"

patterns-established:
  - "AI method signature: operation and user_id params for cost attribution"
  - "Monitoring data aggregation with time range filter (24h/7d/30d)"
  - "Unit economics: cost_per_active_user, cost_per_paying_user metrics"

# Metrics
duration: 6min
completed: 2026-01-24
---

# Phase 15 Plan 02: Cost Tracking & Monitoring API Summary

**Cost tracking integration into AIService + /admin/monitoring endpoint with DAU/WAU/MAU, API costs breakdown, and unit economics**

## Performance

- **Duration:** 6 min
- **Started:** 2026-01-24T12:06:22Z
- **Completed:** 2026-01-24T12:12:32Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Cost tracking module recording every AI request to ai_usage table
- All AIService methods updated with operation and user_id parameters
- Prometheus metrics updated on each AI request (tokens, cost, latency)
- Monitoring service with DAU/WAU/MAU, API costs, unit economics aggregation
- /admin/monitoring endpoint with 24h/7d/30d time range filter

## Task Commits

Each task was committed atomically:

1. **Task 1: Cost tracking module + AIService integration** - `4364a15` (feat)
2. **Task 2: Admin monitoring service + schemas** - `44341ce` (feat)
3. **Task 3: Admin /monitoring endpoint** - `5921556` (feat)

## Files Created/Modified
- `src/monitoring/cost_tracking.py` - record_ai_usage, record_ai_error functions
- `src/services/ai/client.py` - All methods updated with operation, user_id params
- `src/admin/services/monitoring.py` - get_monitoring_data, get_api_costs_data, get_active_users, get_unit_economics
- `src/admin/schemas.py` - MonitoringResponse, ActiveUsersMetrics, APICostsData, UnitEconomicsData, ErrorStatsData
- `src/admin/router.py` - GET /admin/monitoring endpoint

## Decisions Made
- Cost tracking embedded in AIService._generate method - accurate latency measurement with time.monotonic()
- Tracking failure silently logged (warning) - doesn't break AI response to user
- DAU/WAU/MAU based on TarotSpread table (not ai_usage) - TarotSpread represents active user intent, ai_usage includes system operations
- Unit economics divides total_cost by max(users, 1) to avoid division by zero

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None.

## API Reference

### GET /admin/monitoring

**Parameters:**
- `range`: Time range (24h, 7d, 30d) - default: 7d

**Response:**
```json
{
  "range": "7d",
  "active_users": {"dau": 10, "wau": 50, "mau": 200},
  "api_costs": {
    "total_cost": 1.23,
    "total_tokens": 100000,
    "total_requests": 500,
    "by_operation": [{"operation": "tarot", "cost": 0.8, "tokens": 60000, "requests": 300}],
    "by_day": [{"date": "2026-01-24", "cost": 0.5, "tokens": 50000}]
  },
  "unit_economics": {
    "total_cost": 1.23,
    "active_users": 50,
    "paying_users": 5,
    "active_paying_users": 3,
    "cost_per_active_user": 0.0246,
    "cost_per_paying_user": 0.41
  },
  "error_stats": {"error_count": 0, "error_rate": 0.0, "avg_response_time_ms": 0}
}
```

## Next Phase Readiness
- Cost tracking active for all AI operations
- /admin/monitoring provides real-time monitoring data
- Ready for 15-03 alerts setup (can trigger on cost thresholds, error rates)

---
*Phase: 15-monitoring-observability*
*Completed: 2026-01-24*
