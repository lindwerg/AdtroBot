---
phase: 15-monitoring-observability
plan: 01
subsystem: infra
tags: [prometheus, metrics, health-check, monitoring, cost-tracking]

# Dependency graph
requires:
  - phase: 12-performance-layer
    provides: caching foundation, database engine
provides:
  - AIUsage model for AI cost tracking
  - Prometheus custom metrics (adtrobot_*)
  - Comprehensive /health endpoint with 4 checks
  - /metrics endpoint for Prometheus scraping
affects: [15-02-cost-tracking, 15-03-alerts, production-monitoring]

# Tech tracking
tech-stack:
  added: [prometheus-fastapi-instrumentator, prometheus-client, httpx]
  patterns: [health check pattern with parallel execution, Prometheus gauge/counter/histogram metrics]

key-files:
  created:
    - src/db/models/ai_usage.py
    - src/monitoring/__init__.py
    - src/monitoring/metrics.py
    - src/monitoring/health.py
    - migrations/versions/2026_01_24_bb3aea586917_add_ai_usage_table.py
  modified:
    - src/db/models/__init__.py
    - src/main.py
    - pyproject.toml

key-decisions:
  - "AIUsage.user_id nullable for system operations (e.g., scheduled horoscope generation)"
  - "Health checks run in parallel with asyncio.gather for faster response"
  - "/metrics excluded from instrumentation to avoid recursive metrics"

patterns-established:
  - "Health check pattern: HealthCheckResult dataclass + individual async check functions + run_all_checks orchestrator"
  - "Prometheus naming: adtrobot_ prefix for all custom metrics"
  - "Health endpoint returns 503 if any check fails (not just 200 with status field)"

# Metrics
duration: 5min
completed: 2026-01-24
---

# Phase 15 Plan 01: Monitoring Infrastructure Summary

**AIUsage model + Prometheus metrics (adtrobot_*) + comprehensive /health endpoint with database/scheduler/openrouter/telegram checks**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-24T04:00:00Z
- **Completed:** 2026-01-24T04:05:00Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- AIUsage SQLAlchemy model for tracking AI API costs per operation
- 11 custom Prometheus metrics covering requests, AI usage, users, revenue, queue, health
- Comprehensive /health endpoint checking database, scheduler, OpenRouter, Telegram
- Prometheus FastAPI instrumentator with automatic HTTP request metrics

## Task Commits

Each task was committed atomically:

1. **Task 1: AIUsage model + Alembic migration** - `a68985d` (feat)
2. **Task 2: Prometheus metrics module + instrumentator** - `6ced346` (feat)
3. **Task 3: Расширенный /health endpoint с checks** - `b93d15a` (feat)

## Files Created/Modified
- `src/db/models/ai_usage.py` - AIUsage model for cost tracking (user_id, operation, model, tokens, cost, latency)
- `src/monitoring/__init__.py` - Module init
- `src/monitoring/metrics.py` - 11 custom Prometheus metrics with adtrobot_ prefix
- `src/monitoring/health.py` - 4 health check functions + run_all_checks orchestrator
- `src/main.py` - Instrumentator setup, /metrics mount, enhanced /health endpoint
- `src/db/models/__init__.py` - AIUsage export
- `pyproject.toml` - prometheus-fastapi-instrumentator, prometheus-client, httpx deps
- `migrations/versions/2026_01_24_bb3aea586917_add_ai_usage_table.py` - Alembic migration

## Decisions Made
- AIUsage.user_id nullable - allows tracking system-level AI operations (scheduled horoscope generation) without a user context
- Health checks run in parallel via asyncio.gather - total latency is max of individual checks, not sum
- /health returns 503 HTTP status if any check fails - allows load balancers to detect unhealthy instances

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
- DATABASE_URL in .env was placeholder - started local PostgreSQL container on port 5433, updated .env
- Missing svgwrite dependency for import chain - installed via pip

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- AIUsage model ready for recording in AI service calls (Plan 15-02)
- /metrics endpoint ready for Prometheus scraping
- /health endpoint ready for load balancer health checks

---
*Phase: 15-monitoring-observability*
*Completed: 2026-01-24*
