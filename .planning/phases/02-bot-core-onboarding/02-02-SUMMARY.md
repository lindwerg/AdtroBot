---
phase: 02-bot-core-onboarding
plan: 02
subsystem: bot
tags: [aiogram, fsm, onboarding, telegram, handlers]

# Dependency graph
requires:
  - phase: 02-bot-core-onboarding
    plan: 01
    provides: Bot/Dispatcher, DbSessionMiddleware, User birth fields
provides:
  - Complete /start onboarding flow
  - FSM birthdate collection
  - Zodiac determination and mock horoscope
  - Main menu with 4 buttons
affects: [03-horoscope-generation, 04-tarot-generation]

# Tech tracking
tech-stack:
  added: []
  patterns: [fsm-onboarding, router-organization, mock-content-for-mvp]

key-files:
  created:
    - src/bot/states/__init__.py
    - src/bot/states/onboarding.py
    - src/bot/keyboards/__init__.py
    - src/bot/keyboards/main_menu.py
    - src/bot/utils/__init__.py
    - src/bot/utils/zodiac.py
    - src/bot/utils/date_parser.py
    - src/bot/utils/horoscope.py
    - src/bot/handlers/__init__.py
    - src/bot/handlers/start.py
    - src/bot/handlers/menu.py
    - src/bot/handlers/common.py
  modified:
    - src/bot/bot.py

key-decisions:
  - "Mock horoscopes for immediate value - 12 hardcoded texts, AI integration in Phase 3"
  - "explicit session.commit() in handler - DbSessionMiddleware does NOT auto-commit"
  - "Router order: start -> menu -> common (catch-all last)"

patterns-established:
  - "FSM for multi-step dialogs (birthdate collection)"
  - "Mock content pattern for MVP phases"
  - "Router organization by feature area"

# Metrics
duration: 4min
completed: 2026-01-22
---

# Phase 2 Plan 2: Onboarding Flow Summary

**Complete /start -> birthdate -> zodiac -> mock-horoscope -> menu flow with FSM**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-22T20:36:37Z
- **Completed:** 2026-01-22T20:40:23Z
- **Tasks:** 3
- **Files created:** 12
- **Files modified:** 1

## Accomplishments

- FSM OnboardingStates with waiting_birthdate state
- Keyboards: get_main_menu_keyboard (2x2), get_start_keyboard (inline)
- Zodiac calculation from birth date (all 12 signs, boundary-correct)
- Russian date parsing via dateparser (DD.MM.YYYY, "15 марта 1990", etc.)
- Mock horoscopes for all 12 zodiac signs (immediate value)
- /start handler: welcome for new users, menu for returning
- Birthdate collection via FSM with validation
- User update with explicit session.commit()
- Menu handlers: Гороскоп (shows mock), Таро/Подписка (teasers), Профиль (user info)
- Common handler for unknown messages
- All routers registered in Dispatcher

## Task Commits

Each task was committed atomically:

1. **Task 1: FSM States + Keyboards + Utils** - `2616a89` (feat)
2. **Task 2: Handlers + Router Registration** - `486add9` (feat)
3. **Task 3: Integration Test** - No commit (verification only)

## Files Created/Modified

**States:**
- `src/bot/states/__init__.py` - FSM states exports
- `src/bot/states/onboarding.py` - OnboardingStates group

**Keyboards:**
- `src/bot/keyboards/__init__.py` - Keyboard exports
- `src/bot/keyboards/main_menu.py` - get_main_menu_keyboard, get_start_keyboard

**Utils:**
- `src/bot/utils/__init__.py` - Utility exports
- `src/bot/utils/zodiac.py` - ZodiacSign dataclass, get_zodiac_sign
- `src/bot/utils/date_parser.py` - parse_russian_date
- `src/bot/utils/horoscope.py` - MOCK_HOROSCOPES, get_mock_horoscope

**Handlers:**
- `src/bot/handlers/__init__.py` - Handler router exports
- `src/bot/handlers/start.py` - /start, get_first_forecast, process_birthdate
- `src/bot/handlers/menu.py` - Гороскоп, Таро, Подписка, Профиль handlers
- `src/bot/handlers/common.py` - Catch-all for unknown messages

**Modified:**
- `src/bot/bot.py` - Added router imports and dp.include_routers()

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Mock horoscopes (12 hardcoded texts) | Immediate value for MVP, AI generation in Phase 3 |
| Explicit session.commit() | DbSessionMiddleware doesn't auto-commit, handler controls transaction |
| Router order: start -> menu -> common | Common router is catch-all, must be last |
| dateparser with DMY | Russian date format is day-first |

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Verification Results

All verifications passed:
- FSM state imports correctly
- Keyboards have correct structure (2x2 menu, 1 button start)
- Zodiac calculation correct for all edge cases (boundaries tested)
- Date parsing handles DD.MM.YYYY, DD/MM/YYYY, Russian text
- Mock horoscopes return content for all 12 signs
- All routers registered in Dispatcher
- session.commit() present in start handler

## Next Phase Readiness

- Onboarding flow complete
- Mock horoscopes ready to be replaced with AI generation (Phase 3)
- Tarot handler ready for implementation (Phase 4)
- User data persisted: telegram_id, birth_date, zodiac_sign

---
*Phase: 02-bot-core-onboarding*
*Plan: 02*
*Completed: 2026-01-22*
