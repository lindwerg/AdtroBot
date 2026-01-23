---
phase: 09-admin-panel
plan: 08
subsystem: admin-panel
tags: [admin, payments, subscriptions, react, api]
dependency-graph:
  requires: [09-02, 09-04]
  provides: [payments-management, subscriptions-management]
  affects: []
tech-stack:
  added: []
  patterns: [ProTable-pagination, useMutation-table-reload]
key-files:
  created:
    - src/admin/services/payments.py
    - admin-frontend/src/api/endpoints/payments.ts
    - admin-frontend/src/pages/Payments.tsx
    - admin-frontend/src/pages/Subscriptions.tsx
  modified:
    - src/admin/schemas.py
    - src/admin/router.py
    - admin-frontend/src/routes/index.tsx
decisions:
  - key: table-reload-pattern
    choice: key-based-reload
    reason: actionRef.reload() has type issues, key-based remount more reliable
metrics:
  duration: 5 min
  completed: 2026-01-23
---

# Phase 9 Plan 08: Payments and Subscriptions Management Summary

**One-liner:** Payments list with status filters and total amount, subscriptions list with status change modal via ProTable

## What Was Built

### Backend (Python/FastAPI)

1. **Schemas** (`src/admin/schemas.py`):
   - `PaymentListItem`: payment details with joined user info (telegram_id, username)
   - `PaymentListResponse`: paginated list with `total_amount` (sum of succeeded payments)
   - `SubscriptionListItem`: subscription details with user info
   - `SubscriptionListResponse`: paginated list
   - `UpdateSubscriptionStatusRequest`: status change request

2. **Payments Service** (`src/admin/services/payments.py`):
   - `list_payments()`: paginated list with filters (status, user_search, date_from/to)
   - `list_subscriptions()`: paginated list with filters (status, plan, user_search)
   - `update_subscription_status()`: changes status + syncs user premium flags

3. **API Endpoints** (`src/admin/router.py`):
   - `GET /admin/payments`: list payments with filters
   - `GET /admin/subscriptions`: list subscriptions with filters
   - `PATCH /admin/subscriptions/{id}`: update subscription status

### Frontend (React/TypeScript)

1. **API Client** (`admin-frontend/src/api/endpoints/payments.ts`):
   - TypeScript interfaces for all response types
   - `getPayments()`, `getSubscriptions()`, `updateSubscriptionStatus()`

2. **Payments Page** (`admin-frontend/src/pages/Payments.tsx`):
   - ProTable with columns: ID, user, amount (RUB), status (colored tags), recurring, description, dates
   - Status filter (pending/waiting_for_capture/succeeded/canceled)
   - User search filter
   - Total amount stat card (sum of succeeded payments)

3. **Subscriptions Page** (`admin-frontend/src/pages/Subscriptions.tsx`):
   - ProTable with columns: ID, user link, plan, status, period end, canceled_at, created_at
   - Filters: status (trial/active/past_due/canceled/expired), plan (monthly/yearly), user search
   - Edit button opens modal to change status
   - useMutation with key-based table reload on success

4. **Routes** (`admin-frontend/src/routes/index.tsx`):
   - `/subscriptions` -> SubscriptionsPage
   - `/payments` -> PaymentsPage

## Verification Results

- GET /admin/payments endpoint defined
- GET /admin/subscriptions endpoint defined
- PATCH /admin/subscriptions/{id} endpoint defined
- TypeScript compiles without errors
- Frontend build succeeds

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Table reload pattern | key-based remount | ActionType.reload() has TypeScript signature issues, key prop remount is cleaner |
| Total amount calculation | Sum succeeded payments | More useful metric than sum of all payments |
| User link in subscriptions | Link to /users/{user_id} | Quick navigation to user detail page |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed TypeScript type imports**
- **Found during:** Task 3
- **Issue:** verbatimModuleSyntax requires type-only imports
- **Fix:** Changed `import { ProColumns }` to `import type { ProColumns }`
- **Files modified:** Payments.tsx, Subscriptions.tsx
- **Commit:** e77efe6

**2. [Rule 3 - Blocking] Fixed actionRef.reload() type error**
- **Found during:** Task 3
- **Issue:** reload() method expects argument
- **Fix:** Changed to key-based table remount pattern
- **Files modified:** Subscriptions.tsx
- **Commit:** e77efe6

**3. [Rule 1 - Bug] Fixed TarotSpreads.tsx type import**
- **Found during:** Task 3 build verification
- **Issue:** Type import in separate line caused verbatimModuleSyntax error
- **Fix:** Linter auto-fixed to inline type import
- **Files modified:** TarotSpreads.tsx
- **Commit:** e77efe6

## Next Phase Readiness

**Ready for:**
- 09-09: Messaging system
- 09-10: Promo codes management

**No blockers identified.**
