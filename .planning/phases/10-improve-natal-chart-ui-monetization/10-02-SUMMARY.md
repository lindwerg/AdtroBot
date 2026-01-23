---
phase: 10
plan: 02
subsystem: payment
tags: [payment, yookassa, detailed-natal, one-time-purchase]
dependency-graph:
  requires: [06-01, 06-02]  # Payment infrastructure
  provides: [detailed-natal-payment, detailed-natal-model]
  affects: [10-03, 10-04]  # UI and generation plans
tech-stack:
  added: []
  patterns: [one-time-purchase-handling]
file-tracking:
  key-files:
    created:
      - src/db/models/detailed_natal.py
      - migrations/versions/2026_01_23_c2d3e4f5a6b7_add_detailed_natal.py
    modified:
      - src/services/payment/schemas.py
      - src/services/payment/service.py
      - src/db/models/user.py
      - src/db/models/__init__.py
decisions:
  - id: 10-02-01
    decision: "DETAILED_NATAL NOT added to PLAN_DURATION_DAYS"
    rationale: "One-time purchase, not subscription - access is permanent"
  - id: 10-02-02
    decision: "Webhook handles DETAILED_NATAL BEFORE activate_subscription"
    rationale: "Prevents creating subscription for one-time purchase"
metrics:
  duration: 6 min
  completed: 2026-01-23
---

# Phase 10 Plan 02: Payment Infrastructure for Detailed Natal Summary

**One-liner:** PaymentPlan.DETAILED_NATAL (199 RUB one-time) with User.detailed_natal_purchased_at tracking and webhook handling

## What Was Built

### 1. Payment Plan Addition
- `PaymentPlan.DETAILED_NATAL = "detailed_natal"` enum value
- Price: 19900 kopeks (199.00 RUB) - one-time, not subscription
- NOT in `PLAN_DURATION_DAYS` - purchase is permanent

### 2. Database Models
- `User.detailed_natal_purchased_at` - DateTime field tracking purchase timestamp
- `DetailedNatal` model for caching interpretations:
  - `id` (PK)
  - `user_id` (FK to users, indexed)
  - `interpretation` (Text - 3000-5000 word AI interpretation)
  - `telegraph_url` (optional - for long text publishing)
  - `created_at` (timestamp)

### 3. Migration
- `2026_01_23_c2d3e4f5a6b7_add_detailed_natal.py`
- Adds `detailed_natal_purchased_at` to users table
- Creates `detailed_natals` table with FK and index

### 4. Webhook Handling
- `process_webhook_event()` updated to handle DETAILED_NATAL
- Inserted BEFORE `activate_subscription()` call
- Sets `user.detailed_natal_purchased_at = now()`
- Returns early (doesn't create subscription)

## Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| 10-02-01 | DETAILED_NATAL not in PLAN_DURATION_DAYS | Permanent purchase, not time-limited subscription |
| 10-02-02 | Handle DETAILED_NATAL before activate_subscription | Prevents one-time purchase from creating subscription |

## Technical Details

### Payment Flow
```
User clicks "Buy Detailed Natal" (199 RUB)
    -> YooKassa payment created with plan_type="detailed_natal"
    -> Payment succeeds
    -> Webhook received
    -> process_webhook_event() checks plan == DETAILED_NATAL
    -> Sets user.detailed_natal_purchased_at
    -> Returns True (skips activate_subscription)
```

### Files Changed

| File | Change |
|------|--------|
| `src/services/payment/schemas.py` | Added DETAILED_NATAL to PaymentPlan, PLAN_PRICES, PLAN_PRICES_STR |
| `src/db/models/user.py` | Added detailed_natal_purchased_at field |
| `src/db/models/detailed_natal.py` | NEW - DetailedNatal model |
| `src/db/models/__init__.py` | Export DetailedNatal |
| `src/services/payment/service.py` | Handle DETAILED_NATAL in webhook |
| `migrations/versions/2026_01_23_c2d3e4f5a6b7_add_detailed_natal.py` | NEW - migration |

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Ready for:**
- 10-03: UI для покупки (кнопка, платежная страница)
- 10-04: AI генерация детального разбора (3000-5000 слов)

**Pending migration:** Run `alembic upgrade head` on Railway after deployment.
