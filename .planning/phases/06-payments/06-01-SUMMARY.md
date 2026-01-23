---
phase: 06-payments
plan: 01
subsystem: payments
tags: [yookassa, subscription, postgresql, alembic]

# Dependency graph
requires:
  - phase: 01-infrastructure
    provides: Base SQLAlchemy models, alembic setup
  - phase: 02-bot-core
    provides: User model with telegram_id
provides:
  - yookassa SDK integration
  - Subscription model with status state machine
  - Payment model with YooKassa ID as PK
  - PromoCode model for partner program
  - User premium fields (is_premium, premium_until, daily_spread_limit)
affects: [06-02-payment-service, 06-03-subscription-handlers]

# Tech tracking
tech-stack:
  added: [yookassa 3.9.0]
  patterns: [denormalized is_premium for quick access, YooKassa payment ID as PK, kopeks for amounts]

key-files:
  created:
    - src/db/models/subscription.py
    - src/db/models/payment.py
    - src/db/models/promo.py
    - migrations/versions/2026_01_23_c6bc722b76ba_add_subscription_models.py
  modified:
    - pyproject.toml
    - src/config.py
    - src/db/models/user.py
    - src/db/models/__init__.py

key-decisions:
  - "YooKassa payment ID as primary key (natural key from payment provider)"
  - "Amount stored in kopeks (29900 = 299.00 RUB)"
  - "Denormalized is_premium on User for quick access checks"
  - "PromoCode.partner_id as Integer (no FK yet, for future partner program)"

patterns-established:
  - "SubscriptionStatus enum: trial -> active -> past_due -> canceled/expired"
  - "webhook_processed flag for idempotent webhook handling"

# Metrics
duration: 4min
completed: 2026-01-23
---

# Phase 06 Plan 01: Payment Infrastructure Summary

**YooKassa SDK, Subscription/Payment/PromoCode models, User premium fields with alembic migration**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-23T09:42:32Z
- **Completed:** 2026-01-23T09:46:37Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- yookassa 3.9.0 SDK installed and configured
- Subscription model with status state machine (trial, active, past_due, canceled, expired)
- Payment model using YooKassa payment ID as primary key
- PromoCode model ready for partner program (partner_id, commission fields)
- User model extended with is_premium, premium_until, daily_spread_limit
- Migration for all new tables and fields

## Task Commits

Each task was committed atomically:

1. **Task 1: Dependencies + Config + DB Models** - `a891b11` (feat)
2. **Task 2: Migration** - `5e79709` (feat)

## Files Created/Modified
- `pyproject.toml` - Added yookassa dependency
- `poetry.lock` - Updated lockfile
- `src/config.py` - Added YooKassa config fields
- `src/db/models/subscription.py` - Subscription model with status enums
- `src/db/models/payment.py` - Payment model with YooKassa ID as PK
- `src/db/models/promo.py` - PromoCode model with partner fields
- `src/db/models/user.py` - Added is_premium, premium_until, daily_spread_limit
- `src/db/models/__init__.py` - Exported new models
- `migrations/versions/2026_01_23_c6bc722b76ba_add_subscription_models.py` - Full migration

## Decisions Made
- **YooKassa payment ID as primary key:** Natural key from payment provider, ensures uniqueness without generating own IDs
- **Amount in kopeks:** Standard practice for payment systems, avoids floating point issues (29900 = 299.00 RUB)
- **Denormalized is_premium:** Quick access check without joining subscriptions table
- **PromoCode.partner_id as Integer:** No FK constraint yet, will add when partner model is created

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Started temporary PostgreSQL container**
- **Found during:** Task 2 (Migration generation)
- **Issue:** Local PostgreSQL not running, .env has placeholder DATABASE_URL
- **Fix:** Started Docker container `postgres:15-alpine` on port 5433
- **Verification:** Migration generated and applied successfully
- **Impact:** None - container removed after verification

**2. [Rule 1 - Bug] Removed unused import in subscription.py**
- **Found during:** Task 2 verification (ruff check)
- **Issue:** `Integer` imported but not used
- **Fix:** Removed unused import
- **Verification:** ruff check passes
- **Committed in:** 5e79709 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both auto-fixes necessary for execution. No scope creep.

## Issues Encountered
None

## User Setup Required

**External services require manual configuration:**
- Add `YOOKASSA_SHOP_ID` to Railway (from YooKassa Dashboard -> Settings -> Shop ID)
- Add `YOOKASSA_SECRET_KEY` to Railway (from YooKassa Dashboard -> Settings -> Secret Key)
- Run `alembic upgrade head` on Railway after deploy

## Next Phase Readiness
- Payment models ready for PaymentService implementation (06-02)
- Config has YooKassa credentials fields (empty by default)
- Migration ready for Railway deploy

---
*Phase: 06-payments*
*Completed: 2026-01-23*
