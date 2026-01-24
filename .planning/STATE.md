# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-23)

**Core value:** Качественная AI интерпретация астрологии и таро, которая конвертирует бесплатных пользователей в платных подписчиков
**Current focus:** Phase 16 - Testing & Polish

## Current Position

Phase: 16 of 16 (Testing & Polish)
Plan: 1 of 5 in current phase
Status: In progress
Last activity: 2026-01-24 — Completed 16-01-PLAN.md

Progress: [█████████░] 83% (v2.0: 5/6 phases in progress)

## Performance Metrics

**Velocity (v1.0 baseline):**
- Total plans completed: 37
- Average duration: 7 min
- Total execution time: 271 min (~4.5 hours)

**By Phase (v1.0):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1-10 | 37/37 | 271 min | 7 min |

**v2.0 metrics will be tracked separately.**

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v2.0 Research]: PostgreSQL для кэша вместо Redis (достаточная скорость, persistence, дешевле)
- [v2.0 Research]: Pexels stock images вместо AI-генерации (бесплатно, легально, разнообразие)
- [v2.0 Research]: Telethon для Telegram API тестов (активная разработка, StringSession для CI)
- [v2.0 Research]: Prometheus metrics + custom counters (не Sentry - свой стек)
- [12-02]: Fixed dict of 12 asyncio.Lock (no defaultdict) для per-key locking
- [13-01]: 43 космических изображения для рандомной отправки вместо 17 специфических
- [14-01]: file_id caching в PostgreSQL, asset_key формат "cosmic/{filename}"
- [14-02]: callback.bot для callback handlers, bot: Bot injection для message handlers
- [15-01]: AIUsage.user_id nullable для system operations (scheduled horoscope generation)
- [15-01]: Health checks run in parallel via asyncio.gather
- [15-01]: /health returns 503 if any check fails (load balancer integration)
- [15-02]: Cost tracking embedded in AIService._generate for accurate latency
- [15-02]: DAU/WAU/MAU from TarotSpread (not ai_usage) - active intent signal
- [15-03]: Recharts for dashboard charts (AreaChart, BarChart)
- [15-03]: 60s auto-refresh for near real-time monitoring
- [16-01]: StringSession for Telethon (CI-friendly authentication)
- [16-01]: Page Object Model for Playwright (maintainable selectors)
- [16-01]: Faker ru_RU locale for realistic Russian test data

### Pending Todos

None yet.

### Blockers/Concerns

**Production deployment (from v1.0):**
- Configure Railway environment variables
- Run migrations: `alembic upgrade head`
- Configure YooKassa webhook URL
- Add GEONAMES_USERNAME for geocoding

## Session Continuity

Last session: 2026-01-24
Stopped at: Completed 16-01-PLAN.md (Test Infrastructure Setup)
Resume file: None

## v1.0 Reference

**Shipped:** 2026-01-23
**Stats:** 10 phases, 37 plans, 74 requirements
**Full details:** `.planning/milestones/v1.0-ROADMAP.md`
