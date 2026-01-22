---
phase: 04-free-tarot
plan: 02
subsystem: tarot
tags: [aiogram, fsm, callbacks, tarot-handlers, rate-limiting]

# Dependency graph
requires:
  - phase: 04-free-tarot plan 01
    provides: tarot cards utilities, formatting, User tarot fields
  - phase: 02-bot-core
    provides: bot infrastructure, menu handlers
provides:
  - TarotStates FSM for question collection
  - TarotCallback with short prefix for 64-byte limit
  - Tarot keyboards (menu, draw_card, draw_three)
  - Card of the day handler with daily cache
  - 3-card spread handler with FSM and limits
  - Menu "Tarot" leads to tarot submenu
affects: [06-premium, 08-premium-tarot]

# Tech tracking
tech-stack:
  added: []
  patterns: [FSM for multi-step tarot reading, daily limits per user timezone]

key-files:
  created:
    - src/bot/states/tarot.py
    - src/bot/callbacks/tarot.py
    - src/bot/keyboards/tarot.py
    - src/bot/handlers/tarot.py
  modified:
    - src/bot/handlers/menu.py
    - src/bot/handlers/__init__.py
    - src/bot/bot.py

key-decisions:
  - "Card of day is free and unlimited (no limits)"
  - "3-card spread has 1/day limit for free users (premium 20/day placeholder)"
  - "Limits reset at 00:00 in user's timezone"
  - "Short callback prefix 't' for Telegram 64-byte limit"

patterns-established:
  - "FSM for multi-step tarot flow (question -> ritual -> cards)"
  - "Daily limit tracking per user timezone with reset date"

# Metrics
duration: 3min
completed: 2026-01-22
---

# Phase 4 Plan 2: Tarot Handlers Summary

**Full tarot functionality: card of day with caching, 3-card spread with FSM question collection and daily limits, ritual animations, image display**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-22T22:55:51Z
- **Completed:** 2026-01-22T22:58:46Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- TarotStates FSM with waiting_question state
- TarotCallback with short action codes (cod, 3c, dcod, d3, back)
- Tarot keyboards: menu, draw_card, draw_three
- Card of day handler: ritual + cache until 00:00 + image + interpretation (no limits)
- 3-card spread handler: FSM question + limit check + ritual + 3 cards + interpretation + limit display
- Daily spread limit 1/day for free users (reset at 00:00 user timezone)
- Menu "Tarot" now opens tarot submenu (replaced stub)
- Expired session handling in draw_three_cards

## Task Commits

Each task was committed atomically:

1. **Task 1: States, Callbacks, Keyboards** - `2c50817` (feat)
2. **Task 2: Handlers + router registration** - `466893c` (feat)

## Files Created/Modified
- `src/bot/states/tarot.py` - TarotStates FSM with waiting_question
- `src/bot/callbacks/tarot.py` - TarotCallback with short prefix "t"
- `src/bot/keyboards/tarot.py` - 3 keyboard builders
- `src/bot/handlers/tarot.py` - All tarot handlers (card of day + 3-card spread)
- `src/bot/handlers/menu.py` - menu_tarot now shows tarot submenu
- `src/bot/handlers/__init__.py` - Added tarot_router export
- `src/bot/bot.py` - Registered tarot_router in dispatcher

## Decisions Made
- Card of day is free and unlimited - no limits shown after card of day
- 3-card spread has 1/day limit for free (20/day for premium placeholder)
- Limits reset at 00:00 in user's timezone (using spread_reset_date field)
- Ritual uses asyncio.sleep for dramatic effect (1.5s shuffle, 1s between cards)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 4 complete - all tarot functionality implemented
- Migration needs to be applied on Railway: `alembic upgrade head`
- Ready for Phase 5: AI Integration

---
*Phase: 04-free-tarot*
*Completed: 2026-01-22*
