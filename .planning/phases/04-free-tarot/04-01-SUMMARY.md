---
phase: 04-free-tarot
plan: 01
subsystem: tarot
tags: [pillow, tarot, rider-waite, image-processing, json]

# Dependency graph
requires:
  - phase: 02-bot-core
    provides: User model, bot infrastructure
provides:
  - 78 tarot cards JSON dataset with meanings
  - 78 card images (public domain)
  - tarot_cards.py utilities (deck, random, images)
  - tarot_formatting.py (card_of_day, spread formatting)
  - User model tarot fields (card cache, spread limits)
affects: [04-02-tarot-handlers, 08-premium-tarot]

# Tech tracking
tech-stack:
  added: [pillow]
  patterns: [singleton deck loading, entity-based formatting for tarot]

key-files:
  created:
    - src/data/tarot/cards.json
    - src/data/tarot/images/*.jpg
    - src/bot/utils/tarot_cards.py
    - src/bot/utils/tarot_formatting.py
    - migrations/versions/2026_01_22_f93e1451536d_add_tarot_fields.py
  modified:
    - pyproject.toml
    - src/db/models/user.py

key-decisions:
  - "Card images from xiaodeaux/tarot-image-grabber (Wikipedia public domain)"
  - "Card data from ekelen/tarot-api (78 cards with meanings)"
  - "Image rotation 180 degrees for reversed cards via Pillow"

patterns-established:
  - "Singleton deck loading via get_deck() with lazy initialization"
  - "Entity-based formatting for tarot (Bold + BlockQuote)"

# Metrics
duration: 10min
completed: 2026-01-22
---

# Phase 4 Plan 1: Tarot Infrastructure Summary

**78-card Rider-Waite tarot deck with images, utilities for card selection and image rotation, User model fields for day card cache and spread limits**

## Performance

- **Duration:** 10 min
- **Started:** 2026-01-22T22:41:18Z
- **Completed:** 2026-01-22T22:51:44Z
- **Tasks:** 3
- **Files modified:** 82

## Accomplishments
- Full 78-card Rider-Waite deck dataset (JSON with meanings + images)
- Tarot utilities: get_deck, get_random_card, get_three_cards, get_card_image
- Image rotation for reversed cards via Pillow
- User model extended with 5 tarot fields
- Entity-based formatting for card of day and 3-card spread

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Pillow + create tarot dataset** - `4cf7546` (feat)
2. **Task 2: User model migration for tarot** - `719e4bf` (feat)
3. **Task 3: Tarot utilities** - `36604ba` (feat)

## Files Created/Modified
- `src/data/tarot/cards.json` - 78 cards with name, name_short, type, meaning_up, meaning_rev
- `src/data/tarot/images/*.jpg` - 78 card images (public domain)
- `src/bot/utils/tarot_cards.py` - Deck loading, random selection, image handling
- `src/bot/utils/tarot_formatting.py` - Message formatting for tarot readings
- `src/db/models/user.py` - Added 5 tarot fields
- `migrations/versions/2026_01_22_f93e1451536d_add_tarot_fields.py` - DB migration

## Decisions Made
- Card images sourced from xiaodeaux/tarot-image-grabber (Wikipedia public domain images)
- Card data from ekelen/tarot-api (JSON with all required fields)
- Image rotation 180 degrees for reversed cards using Pillow transpose

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- ekelen/tarot-api repo does not contain card images (only JSON) - used xiaodeaux/tarot-image-grabber as alternative source
- GitHub raw URL used master branch instead of main - adjusted URL accordingly

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Tarot infrastructure ready for Plan 02 handlers
- Migration needs to be applied on Railway: `alembic upgrade head`
- All utilities tested and working

---
*Phase: 04-free-tarot*
*Completed: 2026-01-22*
