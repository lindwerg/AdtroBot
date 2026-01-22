---
phase: "03"
plan: "02"
subsystem: notifications
tags: [apscheduler, push-notifications, timezone, profile-settings]
requires:
  - "03-01"
provides:
  - Daily push notifications with user timezone support
  - Profile settings UI for notification management
  - Onboarding notification prompt
affects:
  - "05" # AI horoscope generation will use same notification infrastructure
  - "07" # Premium features may extend notification types
tech-stack:
  added:
    - apscheduler ^3.11.2
    - pytz ^2025.2
    - psycopg2-binary ^2.9.11
  patterns:
    - SQLAlchemyJobStore for persistent job scheduling
    - Lazy scheduler initialization with sync DB URL
key-files:
  created:
    - src/services/__init__.py
    - src/services/scheduler.py
    - src/bot/states/profile.py
    - src/bot/callbacks/profile.py
    - src/bot/keyboards/profile.py
    - src/bot/handlers/profile.py
    - migrations/versions/2026_01_22_5d5aadbabd72_add_user_notification_fields.py
  modified:
    - pyproject.toml
    - poetry.lock
    - src/db/models/user.py
    - src/config.py
    - src/main.py
    - src/bot/bot.py
    - src/bot/handlers/__init__.py
    - src/bot/handlers/menu.py
    - src/bot/handlers/start.py
    - src/bot/callbacks/__init__.py
    - src/bot/keyboards/__init__.py
decisions:
  - id: apscheduler-sync-jobstore
    choice: "SQLAlchemyJobStore with psycopg2-binary (sync driver)"
    rationale: "APScheduler 3.x jobstore requires sync connection; psycopg2-binary for PostgreSQL"
  - id: notification-defaults
    choice: "timezone=Europe/Moscow, hour=9, enabled=False"
    rationale: "Moscow timezone most popular in RU, 9:00 is morning, opt-in by default"
  - id: onboarding-notification-flow
    choice: "Ask after first horoscope, delegate time/timezone handlers to profile.py"
    rationale: "Reuse existing profile handlers, show main menu after complete flow"
metrics:
  duration: 7 min
  completed: "2026-01-22"
---

# Phase 03 Plan 02: Daily Push Notifications Summary

**One-liner:** APScheduler integration with timezone-aware daily horoscope notifications and profile settings UI.

## What Was Built

### 1. User Model Extension
Added notification fields to User model:
- `timezone` (String, default "Europe/Moscow")
- `notification_hour` (SmallInteger, default 9)
- `notifications_enabled` (Boolean, default False)

### 2. Scheduler Service (`src/services/scheduler.py`)
- `get_scheduler()` - Lazy AsyncIOScheduler with SQLAlchemyJobStore
- `schedule_user_notification()` - Schedule daily CronTrigger job
- `remove_user_notification()` - Remove scheduled job
- `send_daily_horoscope()` - Job function that sends formatted horoscope

### 3. Profile Settings UI
**Keyboards:**
- 8 Russian timezones (Kaliningrad to Vladivostok)
- 6 notification times (07:00 - 12:00)
- Toggle enable/disable button
- Onboarding Yes/No prompt

**Handlers:**
- `profile_notifications` callback in menu Profile
- Toggle, time selection, timezone selection flow
- Main menu shown after timezone selection

### 4. Onboarding Integration
After first horoscope in onboarding:
- Ask "Хотите получать ежедневный гороскоп каждое утро?"
- Yes: Enable notifications -> time -> timezone -> main menu
- No: Show main menu with hint about Profile settings

## Key Implementation Details

```python
# Scheduler with persistent jobstore
jobstores = {"default": SQLAlchemyJobStore(url=sync_url)}
_scheduler = AsyncIOScheduler(jobstores=jobstores, timezone=utc)

# Schedule user notification with CronTrigger
scheduler.add_job(
    send_daily_horoscope,
    CronTrigger(hour=hour, minute=0, timezone=timezone),
    args=[user_id, zodiac_sign],
    id=f"horoscope_{user_id}",
    replace_existing=True,
    misfire_grace_time=3600,
)
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing psycopg2-binary dependency**
- **Found during:** Task 2 verification
- **Issue:** APScheduler SQLAlchemyJobStore requires sync PostgreSQL driver
- **Fix:** Added psycopg2-binary ^2.9.11 dependency
- **Commit:** 6567c64

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 84b9621 | APScheduler deps + User model + migration |
| 2 | 6567c64 | Scheduler service + main.py integration |
| 3 | 46a01b2 | Profile settings handlers + keyboards |
| 4 | 60aa524 | Onboarding notification prompt |

## Verification Results

All checks passed:
- User model has timezone, notification_hour, notifications_enabled
- Scheduler creates with SQLAlchemyJobStore
- profile_settings router registered in Dispatcher
- Import chain works (main.py -> scheduler -> bot)
- Migration file exists
- Onboarding keyboards work

## Next Phase Readiness

**Ready for:**
- Phase 5: AI horoscope generation (will use same send_daily_horoscope infrastructure)
- Testing notifications on Railway after deploying and running migration

**Migration required:**
```bash
alembic upgrade head
```

**Environment:**
- TELEGRAM_BOT_TOKEN and WEBHOOK_BASE_URL must be set on Railway
