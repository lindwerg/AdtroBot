---
phase: 09-admin-panel
plan: 11
subsystem: admin-analytics
tags: [ab-testing, utm-tracking, experiments, analytics]
depends_on: ["09-01", "09-03"]
provides:
  - A/B experiment CRUD
  - Variant assignment (hash-based)
  - Experiment results with conversion stats
  - UTM source analytics
  - Admin frontend for experiments
affects: []
tech-stack:
  added: []
  patterns:
    - Hash-based deterministic variant assignment
    - Conversion tracking per variant
    - UTM attribution analytics
key-files:
  created:
    - src/admin/services/experiments.py
    - migrations/versions/2026_01_23_g7b8c9d0e1f2_add_ab_experiments_utm.py
    - admin-frontend/src/api/endpoints/experiments.ts
    - admin-frontend/src/pages/ABTests.tsx
  modified:
    - src/admin/models.py
    - src/admin/schemas.py
    - src/admin/router.py
    - src/db/models/user.py
    - admin-frontend/src/routes/index.tsx
decisions:
  - MD5 hash for deterministic variant assignment (user_id:experiment_id)
  - Winner detection requires 100+ users per variant and >5% difference
  - UTM fields on User model (source, medium, campaign)
metrics:
  duration: 5 min
  completed: 2026-01-23
---

# Phase 09 Plan 11: A/B Testing and UTM Tracking Summary

**One-liner:** A/B testing framework with hash-based variant assignment and UTM source analytics for traffic attribution.

## What Was Built

### Backend

1. **ABExperiment Model** (`src/admin/models.py`)
   - Fields: name, description, metric, variant_b_percent, status
   - Status: draft -> running -> completed
   - Timestamps: started_at, ended_at, created_at

2. **ABAssignment Model** (`src/admin/models.py`)
   - Links user to experiment with variant (A/B)
   - Tracks conversion (converted, converted_at)
   - Unique constraint: one assignment per user per experiment

3. **UTM Fields on User** (`src/db/models/user.py`)
   - utm_source, utm_medium, utm_campaign
   - Enables traffic source attribution

4. **Experiments Service** (`src/admin/services/experiments.py`)
   - `create_experiment()` - create new A/B test
   - `list_experiments()` - paginated list
   - `start_experiment()` / `stop_experiment()` - lifecycle
   - `get_experiment_results()` - stats per variant with winner detection
   - `get_utm_analytics()` - source breakdown with conversion and revenue
   - `assign_variant()` - deterministic hash-based assignment

5. **API Endpoints** (`src/admin/router.py`)
   - POST `/admin/experiments` - create experiment
   - GET `/admin/experiments` - list experiments
   - POST `/admin/experiments/{id}/start` - start
   - POST `/admin/experiments/{id}/stop` - stop
   - GET `/admin/experiments/{id}/results` - results with stats
   - GET `/admin/utm-analytics` - UTM source breakdown

### Frontend

1. **ABTests Page** (`admin-frontend/src/pages/ABTests.tsx`)
   - Experiments table with status, metrics, actions
   - Create experiment modal (name, description, metric, variant split)
   - Results modal with variant comparison
   - Winner badge with trophy icon
   - UTM sources table with conversion and revenue

2. **API Client** (`admin-frontend/src/api/endpoints/experiments.ts`)
   - Full TypeScript interfaces
   - All CRUD functions

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| MD5 hash for variant assignment | Deterministic - same user always gets same variant |
| 100 users + 5% difference for winner | Simple threshold, avoids premature conclusions |
| UTM on User model | Direct attribution, no separate tracking table |
| Kopeks for revenue | Consistent with Payment model |

## Variant Assignment Algorithm

```python
def assign_variant(user_id: int, experiment_id: int, variant_b_percent: int) -> str:
    hash_input = f"{user_id}:{experiment_id}"
    hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16) % 100
    return "B" if hash_value < variant_b_percent else "A"
```

- Deterministic: same user always gets same variant
- No database lookup needed during runtime
- Distribution controlled by variant_b_percent

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Hash | Message |
|------|---------|
| c9acadd | feat(09-11): add A/B experiment models and UTM tracking fields |
| 477b3a7 | feat(09-11): add experiments service and schemas |
| 5482608 | feat(09-11): add A/B tests API endpoints and frontend page |

## Usage

### Creating an Experiment

1. Navigate to A/B Tests page in admin panel
2. Click "Создать"
3. Fill in name, description, metric, variant split
4. Click OK to create (status: draft)
5. Click "Запустить" to start collecting data

### Tracking UTM Sources

Add UTM parameters to bot links:
```
https://t.me/your_bot?start=utm_source=instagram&utm_medium=post&utm_campaign=launch
```

Parse in /start handler and save to User model.

### Viewing Results

1. Click "Результаты" on any experiment
2. See users, conversions, conversion rate per variant
3. Winner shown if significant difference detected

## Next Phase Readiness

- [ ] Add UTM parsing in /start handler (bot-side)
- [ ] Implement experiment assignment on user actions
- [ ] Add conversion tracking (e.g., on payment success)
