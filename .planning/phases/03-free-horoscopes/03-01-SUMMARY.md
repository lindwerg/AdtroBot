---
phase: 03-free-horoscopes
plan: 01
subsystem: bot-ui
tags: [aiogram, formatting, callbacks, inline-keyboard]

dependency_graph:
  requires:
    - "02-01: bot module structure"
    - "02-02: menu handlers, zodiac utils"
  provides:
    - "Entity-based horoscope formatting"
    - "Zodiac inline keyboard navigation"
    - "Callback handler for sign switching"
  affects:
    - "03-02: daily push notifications will use formatting"
    - "05-xx: AI horoscopes will use same formatting"

tech_stack:
  added: []
  patterns:
    - "aiogram.utils.formatting for entity-based messages"
    - "CallbackData factory with short prefix"
    - "InlineKeyboardBuilder with adjust()"

key_files:
  created:
    - "src/bot/utils/formatting.py"
    - "src/bot/callbacks/__init__.py"
    - "src/bot/callbacks/horoscope.py"
    - "src/bot/keyboards/horoscope.py"
    - "src/bot/handlers/horoscope.py"
  modified:
    - "src/bot/utils/__init__.py"
    - "src/bot/keyboards/__init__.py"
    - "src/bot/handlers/__init__.py"
    - "src/bot/handlers/menu.py"
    - "src/bot/bot.py"

decisions:
  - id: "0301-01"
    decision: "Use aiogram.utils.formatting instead of HTML strings"
    rationale: "Entity-based formatting auto-escapes user input, safer and cleaner"
  - id: "0301-02"
    decision: "Short CallbackData prefix 'z' and field 's'"
    rationale: "Telegram 64-byte limit for callback_data"
  - id: "0301-03"
    decision: "Classical zodiac order in keyboard (Aries -> Pisces)"
    rationale: "More intuitive for users than ZODIAC_SIGNS dict order (Capricorn first)"

metrics:
  duration: "3 min"
  completed: "2026-01-22"
---

# Phase 3 Plan 1: Horoscope Formatting & Navigation Summary

Entity-based horoscope formatting with Bold/BlockQuote and 4x3 zodiac inline keyboard for sign switching.

## What Was Built

### Entity-Based Formatting (`src/bot/utils/formatting.py`)

`format_daily_horoscope()` function using `aiogram.utils.formatting`:
- Header: `{emoji} {sign_name_ru} | {DD} {месяц_ru}`
- Bold section: `🔮 Общий прогноз`
- Bold section: `💡 Совет дня`
- BlockQuote for daily tip

Usage: `await message.answer(**content.as_kwargs())`

### Zodiac Callback (`src/bot/callbacks/horoscope.py`)

```python
class ZodiacCallback(CallbackData, prefix="z"):
    s: str  # English sign name
```

Short prefix and field name to stay under 64-byte Telegram limit.

### Zodiac Keyboard (`src/bot/keyboards/horoscope.py`)

`build_zodiac_keyboard(current_sign)`:
- 4x3 grid (3 rows of 4 buttons)
- Classical zodiac order: Aries -> Pisces
- Checkmark indicator for current/user sign

### Horoscope Handler (`src/bot/handlers/horoscope.py`)

- `show_zodiac_horoscope()` - callback handler for sign switching, edits message
- `show_horoscope_message()` - reusable function for initial display
- `_parse_mock_horoscope()` - splits mock text into forecast/tip

### Menu Integration

`menu_horoscope` now uses `show_horoscope_message()` instead of plain `get_mock_horoscope()`.

## Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| 0301-01 | aiogram.utils.formatting | Auto-escapes user input, entity-based safer than HTML strings |
| 0301-02 | Short prefix "z", field "s" | Telegram 64-byte callback_data limit |
| 0301-03 | Classical zodiac order | Aries -> Pisces more intuitive than dict order |

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

| Check | Result |
|-------|--------|
| format_daily_horoscope returns entities | PASS |
| build_zodiac_keyboard returns 4x3 grid | PASS (3 rows, 12 buttons) |
| horoscope router registered | PASS |
| Import chain works | PASS |

## Next Phase Readiness

**Ready for 03-02 (Daily Push Notifications):**
- Formatting utility available for push messages
- Horoscope display pattern established
- Need to add APScheduler and timezone handling

**Dependencies satisfied:**
- User model has zodiac_sign (Phase 2)
- Mock horoscopes available (Phase 2)
- Entity formatting ready for AI horoscopes (Phase 5)
