---
phase: 12-caching-background-jobs
plan: 01
subsystem: database
tags: [postgresql, sqlalchemy, alembic, caching]

dependency-graph:
  requires: [phase-10]
  provides: [horoscope-cache-schema, horoscope-views-schema]
  affects: [12-02, 12-03]

tech-stack:
  added: []
  patterns:
    - "Mapped[] type hints for SQLAlchemy 2.x"
    - "UniqueConstraint for composite keys"
    - "server_default for generated_at timestamps"

key-files:
  created:
    - src/db/models/horoscope_cache.py
    - migrations/versions/2026_01_23_h8c9d0e1f2g3_add_horoscope_cache_tables.py
  modified:
    - src/db/models/__init__.py

decisions:
  - key: "horoscope-cache-schema"
    choice: "Separate table horoscope_cache with zodiac_sign + horoscope_date unique constraint"
    rationale: "Follows RESEARCH.md Pattern 1, simple lookup by sign+date"
  - key: "horoscope-views-schema"
    choice: "Separate table horoscope_views with per-sign per-day counters"
    rationale: "Granular metrics for MON-01 admin dashboard"

metrics:
  duration: "3 min"
  completed: "2026-01-23"
---

# Phase 12 Plan 01: PostgreSQL Schema for Horoscope Caching Summary

**One-liner:** PostgreSQL таблицы horoscope_cache и horoscope_views с UniqueConstraint для persistent cache + метрики просмотров.

## What Was Built

### HoroscopeCache Model
- `id`: Integer PK
- `zodiac_sign`: String(20), indexed
- `horoscope_date`: Date, indexed
- `content`: Text (AI-generated horoscope)
- `generated_at`: DateTime(timezone=True), server_default=now()
- UniqueConstraint: `uq_horoscope_cache_sign_date` на (zodiac_sign, horoscope_date)

### HoroscopeView Model
- `id`: Integer PK
- `zodiac_sign`: String(20)
- `view_date`: Date
- `view_count`: Integer, server_default=0
- UniqueConstraint: `uq_horoscope_views_sign_date` на (zodiac_sign, view_date)

### Alembic Migration
- Revision: `h8c9d0e1f2g3`
- Down revision: `g7b8c9d0e1f2`
- Creates both tables with indexes и constraints

## Key Implementation Details

1. **Type hints:** Используется `Mapped[]` и `mapped_column()` по SQLAlchemy 2.x стандарту
2. **Indexes:** horoscope_date и zodiac_sign проиндексированы для быстрого поиска
3. **UniqueConstraint:** Предотвращает дублирование записей для одного знака в один день
4. **Export:** Модели доступны через `from src.db.models import HoroscopeCache, HoroscopeView`

## Verification Results

| Check | Result |
|-------|--------|
| Models import | OK |
| Table names correct | horoscope_cache, horoscope_views |
| Migration syntax | Valid Python |
| Revision chain | g7b8c9d0e1f2 → h8c9d0e1f2g3 |

## Deviations from Plan

None — план выполнен точно как написан.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | eaed054 | Create HoroscopeCache and HoroscopeView models |
| 2 | 0ed3264 | Export models from src.db.models |
| 3 | cf5faff | Add Alembic migration for cache tables |

## Next Phase Readiness

**Ready for 12-02:** Cache service implementation
- Models ready: HoroscopeCache, HoroscopeView
- Migration ready to run: `alembic upgrade head`
- Pattern from RESEARCH.md: Per-key asyncio.Lock для race condition prevention

**Blockers:** None
