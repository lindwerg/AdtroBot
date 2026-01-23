---
phase: 09
plan: 07
subsystem: admin-messaging
tags: [messaging, broadcast, telegram, scheduling]

dependency-graph:
  requires: ["09-01", "09-04"]
  provides: ["messaging-api", "broadcast", "scheduled-messages"]
  affects: ["09-08"]

tech-stack:
  added: []
  patterns: ["batch-sending", "rate-limiting"]

file-tracking:
  key-files:
    created:
      - src/admin/services/messaging.py
      - migrations/versions/2026_01_23_e5f6a7b8c9d0_add_scheduled_messages.py
      - admin-frontend/src/api/endpoints/messages.ts
      - admin-frontend/src/pages/Messages.tsx
    modified:
      - src/admin/models.py
      - src/admin/schemas.py
      - src/admin/router.py
      - admin-frontend/src/routes/index.tsx

decisions:
  - id: msg-rate-limit
    choice: "25 messages/second with 1s delay between batches"
    why: "Telegram rate limit ~30 msg/sec for bots"

metrics:
  duration: 5 min
  completed: 2026-01-23
---

# Phase 9 Plan 7: Messaging System Summary

Messaging service with batch rate-limiting and scheduled message support.

## What Was Built

### ScheduledMessage Model
- `text`: Message content
- `filters`: JSON for broadcast targeting (is_premium, zodiac_sign, etc.)
- `target_user_id`: For single-user messages
- `scheduled_at`/`sent_at`: Scheduling timestamps
- `total_recipients`/`delivered_count`/`failed_count`: Stats
- `status`: pending/sending/sent/canceled

### Messaging Service (`src/admin/services/messaging.py`)
- `send_message_to_user()`: Single Telegram message via bot
- `broadcast_message()`: Batch send to filtered users with rate limiting
- `send_or_schedule_message()`: Immediate or scheduled delivery
- `get_message_history()`: Paginated history with stats
- `cancel_scheduled_message()`: Cancel pending messages

### API Endpoints
- `POST /admin/messages`: Send or schedule message
- `GET /admin/messages`: Paginated history
- `DELETE /admin/messages/{id}`: Cancel scheduled

### Frontend (`admin-frontend/src/pages/Messages.tsx`)
- Send form with text, target selection
- Broadcast mode with filters (premium status, zodiac sign)
- Single user mode with user ID
- Scheduled mode with date picker
- History table with delivery stats

## Key Implementation Details

### Rate Limiting
```python
batch_size = 25
delay_between_batches = 1.0  # seconds
```
Batched sending prevents hitting Telegram's ~30 msg/sec limit.

### Filter Query Building
```python
def build_user_query(filters: dict[str, Any]):
    query = select(User.telegram_id)
    if filters.get("is_premium") is not None:
        query = query.where(User.is_premium == filters["is_premium"])
    if filters.get("zodiac_sign"):
        query = query.where(User.zodiac_sign == filters["zodiac_sign"])
    # ...
```

### Bot Dependency
Messaging service uses `get_bot()` which requires FastAPI lifespan to have initialized the bot. Documented in code.

## Commits

| Hash | Description |
|------|-------------|
| d87edc4 | Add ScheduledMessage model and migration |
| d54318b | Add messaging service for sending and broadcasting |
| ceb7d0c | Add messaging API endpoints and frontend page |

## Deviations from Plan

None - plan executed as written.

## Next Phase Readiness

Dependencies met for:
- 09-08 (Promo Codes): Can now notify users about promo codes via messaging
