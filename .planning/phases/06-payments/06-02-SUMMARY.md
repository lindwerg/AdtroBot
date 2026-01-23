---
phase: "06"
plan: "02"
name: "Payment Service + YooKassa Webhook"
status: complete
subsystem: payments

# Dependency tracking
requires:
  - "06-01"  # Payment infrastructure, models, config
provides:
  - YooKassa async client wrapper
  - Subscription activation/cancellation service
  - Webhook endpoint with idempotent processing
affects:
  - "06-03"  # Bot handlers will use payment service

# Tech tracking
tech-stack:
  added: []  # yookassa already added in 06-01
  patterns:
    - asyncio.to_thread for sync SDK
    - BackgroundTasks for webhook processing
    - IP whitelist for webhook security
    - Idempotent webhook via webhook_processed flag

# File tracking
key-files:
  created:
    - src/services/payment/__init__.py
    - src/services/payment/client.py
    - src/services/payment/schemas.py
    - src/services/payment/service.py
  modified:
    - src/main.py
    - src/bot/handlers/start.py (lint fix)

# Decisions made
decisions:
  - key: "asyncio-to-thread"
    choice: "Wrap YooKassa sync SDK with asyncio.to_thread"
    rationale: "YooKassa SDK is sync-only, to_thread preserves async event loop"
  - key: "webhook-background"
    choice: "Process webhook in BackgroundTasks, return 200 immediately"
    rationale: "YooKassa expects fast 200 response, retries on timeout"
  - key: "ip-whitelist-production"
    choice: "IP whitelist only in production (railway_environment set)"
    rationale: "Local testing needs to work without IP restrictions"

# Metrics
metrics:
  duration: 3 min
  completed: 2026-01-23
  tasks: 2/2

tags: [yookassa, webhook, subscription, payment, async]
---

# Phase 6 Plan 02: Payment Service + YooKassa Webhook Summary

Async YooKassa client wrapper + subscription service + webhook endpoint with IP whitelist and idempotent processing

## What Was Built

### 1. Payment Schemas (src/services/payment/schemas.py)
- `PaymentPlan` enum: MONTHLY, YEARLY
- `PLAN_PRICES` in kopeks: 29900 (299 RUB), 249900 (2499 RUB)
- `PLAN_PRICES_STR` for YooKassa API: "299.00", "2499.00"
- `PLAN_DURATION_DAYS`: 30, 365
- `TRIAL_DAYS`: 3

### 2. YooKassa Client (src/services/payment/client.py)
- `create_payment()` - первичный платеж с redirect confirmation
- `create_recurring_payment()` - автоплатеж по сохраненному payment_method_id
- `cancel_recurring()` - отключение автоплатежа (просто перестаем использовать method_id)
- Все функции async через `asyncio.to_thread`
- Idempotency key для каждого платежа
- structlog logging

### 3. Subscription Service (src/services/payment/service.py)
- `activate_subscription()` - создание/продление подписки
- `cancel_subscription()` - отмена (доступ до конца периода)
- `get_user_subscription()` - получение активной подписки по telegram_id
- `is_yookassa_ip()` - проверка IP из whitelist
- `process_webhook_event()` - idempotent обработка webhook'ов
- YooKassa IP whitelist: 185.71.76.0/27, 185.71.77.0/27, 77.75.153.0/25, 77.75.154.128/25, 2a02:5180::/32

### 4. Webhook Endpoint (src/main.py)
- `POST /webhook/yookassa`
- IP verification в production (railway_environment set)
- Возвращает 200 немедленно
- Обработка в BackgroundTasks

## Key Implementation Details

### Idempotent Webhook Processing
```python
existing = await session.get(Payment, payment_id)
if existing and existing.webhook_processed:
    return False  # Skip duplicate
```

### Async SDK Wrapper Pattern
```python
def _create():
    return YooPayment.create(payment_data, idempotency_key)
result = await asyncio.to_thread(_create)
```

### Background Webhook Processing
```python
async def process_event():
    async with AsyncSessionLocal() as session:
        await process_webhook_event(session, event)
background_tasks.add_task(process_event)
return Response(status_code=200)
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Lint] Removed unused imports in start.py**
- **Found during:** Task 2 verification (ruff check)
- **Issue:** `build_timezone_keyboard` and `schedule_user_notification` imported but unused
- **Fix:** Removed unused imports
- **Files modified:** src/bot/handlers/start.py
- **Commit:** e190da7

## Files Changed

| File | Action | Purpose |
|------|--------|---------|
| src/services/payment/__init__.py | created | Module exports |
| src/services/payment/schemas.py | created | Plan prices, durations, enums |
| src/services/payment/client.py | created | Async YooKassa wrapper |
| src/services/payment/service.py | created | Subscription business logic |
| src/main.py | modified | Added /webhook/yookassa endpoint |
| src/bot/handlers/start.py | modified | Lint fix: removed unused imports |

## Verification Results

- [x] `from src.services.payment import create_payment, activate_subscription` - OK
- [x] `/webhook/yookassa` route exists in app.routes
- [x] `poetry run ruff check src/` passes

## Next Phase Readiness

**Ready for 06-03 (Bot Handlers):**
- Payment client functions ready for handler integration
- Subscription service ready for /subscription commands
- Webhook endpoint deployed and ready

**Required before production:**
- Add YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY to Railway
- Configure YooKassa webhook URL: https://adtrobot-production.up.railway.app/webhook/yookassa
