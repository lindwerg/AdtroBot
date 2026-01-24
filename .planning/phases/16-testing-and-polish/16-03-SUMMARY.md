---
phase: 16-testing-and-polish
plan: 03
subsystem: testing
tags: [telethon, e2e, telegram-bot, pytest, asyncio]

# Dependency graph
requires:
  - phase: 16-01
    provides: Telethon fixtures and test infrastructure
provides:
  - 45 E2E tests for Telegram bot flows
  - Parametrized tests for all 12 zodiac signs
  - Comprehensive coverage of /start, horoscope, tarot, natal, subscription
affects: [16-04, 16-05]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Telethon conversation pattern", "Parametrized zodiac tests", "Navigation helpers"]

key-files:
  created:
    - tests/e2e/conftest.py
    - tests/e2e/test_start.py
    - tests/e2e/test_profile.py
    - tests/e2e/test_horoscope.py
    - tests/e2e/test_tarot.py
    - tests/e2e/test_natal.py
    - tests/e2e/test_subscription.py
  modified:
    - pyproject.toml

key-decisions:
  - "ZODIAC_SIGNS_QUICK for CI (3 signs) vs ZODIAC_SIGNS_FULL (12 signs, marked slow)"
  - "Navigation helpers for consistent menu traversal"
  - "Timeout 60s for AI generation, 30s for standard responses"
  - "pytest.mark.slow for full zodiac coverage (run with -m slow)"

patterns-established:
  - "navigate_to_X_menu() helpers for consistent test navigation"
  - "Parametrized tests with @pytest.mark.parametrize for zodiac signs"
  - "Flexible assertions (multiple acceptable responses)"

# Metrics
duration: 5min
completed: 2026-01-24
---

# Phase 16 Plan 03: Bot E2E Tests Summary

**45 Telethon E2E tests covering /start, profile, horoscope (12 signs), tarot (card of day, 3-card, celtic cross), natal chart, and subscription flows**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-24T13:50:41Z
- **Completed:** 2026-01-24T13:55:41Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- 8 tests for /start and profile flows
- 19 tests for horoscope (3 quick + 12 full zodiac coverage + 4 additional)
- 6 tests for tarot (card of day, 3-card, celtic cross, history)
- 7 tests for natal chart (premium gate, birth data, generation)
- 6 tests for subscription (offer, plans, payment link)

## Task Commits

Each task was committed atomically:

1. **Task 1: E2E conftest and base tests** - `f1d029a` (feat)
2. **Task 2: Horoscope E2E tests for all 12 zodiac signs** - `7b88ebf` (feat)
3. **Task 3: Tarot, Natal, Subscription E2E tests** - `9345cfa` (feat)

## Files Created/Modified

- `tests/e2e/conftest.py` - E2E fixtures (conversation_timeout, cleanup_test_user)
- `tests/e2e/test_start.py` - /start command tests (4 tests)
- `tests/e2e/test_profile.py` - Profile navigation tests (4 tests)
- `tests/e2e/test_horoscope.py` - Horoscope tests with ZODIAC_SIGNS parametrization (19 tests)
- `tests/e2e/test_tarot.py` - Tarot spread tests (6 tests)
- `tests/e2e/test_natal.py` - Natal chart tests (7 tests)
- `tests/e2e/test_subscription.py` - Subscription flow tests (6 tests)
- `pyproject.toml` - Added 'slow' pytest marker

## Decisions Made

1. **Quick vs Full zodiac tests** - 3 signs (aries, leo, sagittarius) for CI, 12 for full coverage
2. **Slow marker** - Full zodiac tests marked as slow to save API costs in CI
3. **Flexible assertions** - Tests accept multiple valid responses (Russian/English, premium/free variations)
4. **Navigation helpers** - Reusable functions for menu navigation in each test file

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 45 E2E bot tests collected and ready to run
- To run quick tests: `pytest tests/e2e/ -m "not slow"`
- To run full coverage: `pytest tests/e2e/`
- Requires env vars: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELETHON_SESSION, BOT_USERNAME

---
*Phase: 16-testing-and-polish*
*Completed: 2026-01-24*
