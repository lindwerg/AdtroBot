---
phase: 12-caching-background-jobs
plan: 02
subsystem: services
tags: [caching, asyncio, apscheduler, postgresql, background-jobs]

dependency-graph:
  requires: [12-01]
  provides: [HoroscopeCacheService, generate_daily_horoscopes, warm_horoscope_cache]
  affects: [13-xx-image-cache]

tech-stack:
  added: []
  patterns: [per-key-locking, singleton-service, cron-trigger, upsert]

key-files:
  created:
    - src/services/horoscope_cache.py
  modified:
    - src/services/scheduler.py
    - src/main.py

decisions:
  - id: per-key-locks
    choice: "Fixed dict of 12 asyncio.Lock (no defaultdict)"
    reason: "Prevents memory leaks, 12 zodiac signs are fixed"

metrics:
  duration: 2 min
  completed: 2026-01-23
---

# Phase 12 Plan 02: Horoscope Cache Service Summary

**One-liner:** PostgreSQL-backed cache service with per-key locking, midnight generation job, and startup warming

## What Was Built

### HoroscopeCacheService (`src/services/horoscope_cache.py`)

- **Per-key asyncio.Lock:** 12 fixed locks (one per zodiac sign), acquired BEFORE cache check
- **get_horoscope():** Returns cached content or generates on-demand with retry (5/10/30 sec backoff)
- **_increment_view():** PostgreSQL UPSERT for atomic view count tracking
- **Singleton pattern:** `get_horoscope_cache_service()` getter

### Background Job (`src/services/scheduler.py`)

- **generate_daily_horoscopes():** Runs at 00:00 Moscow time via CronTrigger
- **Cleanup first:** DELETE FROM horoscope_cache WHERE date < today
- **Sequential generation:** All 12 signs via HoroscopeCacheService
- **Misfire handling:** 1 hour grace time for server downtime

### Cache Warming (`src/main.py`)

- **warm_horoscope_cache():** Preloads all 12 signs from PostgreSQL on startup
- **Graceful degradation:** Generates on-demand if cache miss
- **Per-sign try/except:** One failure doesn't block others

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Lock strategy | Fixed dict of 12 locks | No defaultdict to prevent memory leaks |
| Lock timing | Before cache check | Prevents race condition on cache miss |
| Retry backoff | 5/10/30 seconds | Progressive delay for AI API failures |
| View tracking | PostgreSQL UPSERT | Atomic increment, no application-level locking |
| Job schedule | CronTrigger hour='0' | Midnight only, 24-hour cycle |
| Cleanup | Explicit DELETE before generation | Ensures old data is removed |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 93f78e9 | feat | HoroscopeCacheService with per-key locking |
| eb402c4 | feat | Daily horoscope generation job at 00:00 Moscow |
| 2d7ee14 | feat | Cache warming on application startup |

## Files Changed

```
src/services/horoscope_cache.py  (new)    +164 lines
src/services/scheduler.py        (mod)    +49 lines
src/main.py                      (mod)    +26 lines
```

## Verification Results

| Check | Status |
|-------|--------|
| 12 fixed locks (no defaultdict) | PASS |
| Lock acquired before cache check | PASS |
| View count via UPSERT | PASS |
| CronTrigger(hour='0') - midnight only | PASS |
| Explicit DELETE before generation | PASS |
| Uses HoroscopeCacheService (not direct AI) | PASS |
| Cache warmed on startup | PASS |

## Deviations from Plan

None - plan executed exactly as written.

## Dependencies for Next Plans

- **12-03:** Can use same patterns for image cache service
- **Future:** HoroscopeCacheService ready for integration with bot handlers

## Next Phase Readiness

Phase 12-03 (image cache) can proceed. Same patterns:
- Per-key locking for image generation
- PostgreSQL-backed cache table
- Background cleanup job
