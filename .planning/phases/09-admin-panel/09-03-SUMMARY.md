---
phase: 09-admin-panel
plan: 03
subsystem: admin-api
tags: [analytics, dashboard, funnel, kpi]
completed: "2026-01-23"
duration: "3 min"
dependency-graph:
  requires: ["09-01"]
  provides: ["dashboard-metrics-api", "funnel-api"]
  affects: ["09-05"]
tech-stack:
  added: []
  patterns: ["analytics-service", "sparkline-data"]
key-files:
  created:
    - src/admin/services/analytics.py
  modified:
    - src/admin/schemas.py
    - src/admin/router.py
decisions:
  - key: "dau-calculation"
    choice: "TarotSpread activity as DAU proxy"
    reason: "No separate activity tracking table yet"
  - key: "retention-d7"
    choice: "Cohort-based retention (users registered 7 days ago who returned)"
    reason: "Standard retention metric"
  - key: "funnel-stages"
    choice: "6 stages: registered -> onboarded -> first_action -> saw_teaser -> started_payment -> paid"
    reason: "Covers full conversion path from registration to payment"
metrics:
  tasks: 3
  commits: 3
  files-changed: 3
---

# Phase 09 Plan 03: Dashboard Metrics API Summary

**One-liner:** Dashboard API endpoints returning KPI metrics (DAU, MAU, revenue, conversion) with sparklines and 6-stage conversion funnel.

## What Was Done

### Task 1: Dashboard Metrics Schemas
Added Pydantic schemas for dashboard responses:
- `SparklinePoint` - single data point for trend charts (date + value)
- `KPIMetric` - metric with value, trend percentage, and sparkline data
- `DashboardMetrics` - full dashboard response with 14 KPI metrics
- `FunnelStage` - single funnel stage with conversion rates
- `FunnelData` - complete funnel with stages and period

### Task 2: Analytics Service
Created `/src/admin/services/analytics.py` with:
- `calc_trend()` - percentage change calculator
- `get_sparkline_data()` - 7-day trend data for charts
- `get_dashboard_metrics()` - calculates all KPIs:
  - DAU/MAU (from TarotSpread activity)
  - New users today with trend
  - D7 retention (cohort-based)
  - Tarot spreads today
  - Revenue today/month (from succeeded payments)
  - Conversion rate (paid users / eligible users)
  - ARPU (revenue per user)
- `get_funnel_data()` - 6-stage conversion funnel:
  1. Registration (/start)
  2. Onboarding complete (has zodiac)
  3. First action (tarot spread)
  4. Saw premium teaser (2+ spreads)
  5. Started payment (payment record)
  6. Paid (succeeded payment)

### Task 3: Dashboard API Endpoints
Added endpoints to router:
- `GET /admin/dashboard` - returns `DashboardMetrics`
- `GET /admin/funnel?days=30` - returns `FunnelData`

Both endpoints protected by JWT authentication.

## Commits

| # | Hash | Message |
|---|------|---------|
| 1 | b98bdec | feat(09-03): add dashboard metrics schemas |
| 2 | 35bd0d1 | feat(09-03): add analytics service for dashboard metrics |
| 3 | 7ce6e18 | feat(09-03): add dashboard and funnel API endpoints |

## Key Files

**Created:**
- `src/admin/services/analytics.py` - analytics calculations (477 lines)

**Modified:**
- `src/admin/schemas.py` - added 65 lines of dashboard schemas
- `src/admin/router.py` - added 25 lines for dashboard endpoints

## Technical Details

### Metrics Calculation

| Metric | Source | Method |
|--------|--------|--------|
| DAU | TarotSpread | Distinct user_ids with spread today |
| MAU | TarotSpread | Distinct user_ids in last 30 days |
| New Users | User.created_at | Count with date filter |
| Retention D7 | User + TarotSpread | Cohort users returned after 7 days |
| Revenue | Payment.amount | Sum of succeeded payments (kopeks) |
| Conversion | Payment + User | Paid users / users registered 7+ days ago |
| ARPU | Revenue / Users | Monthly revenue per total users |

### Funnel Stages

```
Registered (100%)
    ↓ -X% (drop)
Onboarded (Y%)
    ↓ -X% (drop)
First Action (Y%)
    ↓ -X% (drop)
Saw Teaser (Y%)
    ↓ -X% (drop)
Started Payment (Y%)
    ↓ -X% (drop)
Paid (Y%)
```

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Dependencies satisfied:**
- Dashboard API ready for frontend (09-05)
- Schemas defined and documented

**Open items:**
- `horoscopes_today` returns 0 (needs tracking table)
- `error_rate`, `avg_response_time` are None (needs logging)
- `api_costs_today/month` are None (needs OpenRouter tracking)

---

*Phase: 09-admin-panel*
*Plan: 03*
*Completed: 2026-01-23*
