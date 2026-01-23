---
phase: 08-premium-tarot-natal
plan: 01
status: complete

dependency-graph:
  requires:
    - "06-01 (payment infrastructure)"
    - "04-02 (tarot handlers)"
    - "05-01 (AI integration)"
  provides:
    - "TarotSpread model for history storage"
    - "Celtic Cross 10-card premium spread"
    - "CelticCrossPrompt for 800-1200 word AI interpretations"
    - "Spread history with pagination"
  affects:
    - "08-02 (natal chart display may use similar patterns)"

tech-stack:
  added: []
  patterns:
    - "Media group album for 10-card display"
    - "Pagination with offset/limit"
    - "JSON column for cards storage"

key-files:
  created:
    - "src/db/models/tarot_spread.py"
    - "migrations/versions/2026_01_23_b1c2d3e4f5a6_add_tarot_spreads_table.py"
  modified:
    - "src/db/models/__init__.py"
    - "src/services/ai/prompts.py"
    - "src/services/ai/client.py"
    - "src/bot/callbacks/tarot.py"
    - "src/bot/keyboards/tarot.py"
    - "src/bot/keyboards/subscription.py"
    - "src/bot/handlers/tarot.py"
    - "src/bot/states/tarot.py"
    - "src/bot/utils/tarot_cards.py"
    - "src/bot/utils/tarot_formatting.py"

decisions:
  - id: "TAROT-HISTORY-JSON"
    description: "Cards stored as JSON array with card_id, reversed, position"
    rationale: "Flexible schema, easy to query card details from deck"
  - id: "CELTIC-ALBUM"
    description: "Celtic Cross cards sent as media group (album)"
    rationale: "Telegram supports max 10 photos in album - perfect for Celtic Cross"
  - id: "HISTORY-PAGINATION"
    description: "5 spreads per page, max 100 total in history"
    rationale: "Balance between UI simplicity and storage"

metrics:
  duration: "7 min"
  completed: "2026-01-23"
---

# Phase 8 Plan 01: Celtic Cross + History Summary

TarotSpread model, CelticCrossPrompt, Celtic Cross 10-card premium spread, spread history with pagination

## What Was Built

### TarotSpread Model
- `src/db/models/tarot_spread.py`: Stores spread history
- Fields: user_id (FK), spread_type, question, cards (JSON), interpretation, created_at
- Index on user_id for fast history queries
- Migration creates tarot_spreads table

### CelticCrossPrompt
- Added to `src/services/ai/prompts.py`
- SYSTEM prompt for 800-1200 word interpretation
- Sections: Сердце вопроса, Временная ось, Сознание/Подсознание, Внешний мир, Путь к исходу, Общий посыл
- 10 Celtic Cross positions defined

### generate_celtic_cross Method
- Added to AIService in `src/services/ai/client.py`
- max_tokens=4000 for longer response
- Uses validate_tarot for output validation

### Celtic Cross Flow
- Premium-only check with teaser for free users
- Extended ritual ("Кельтский крест — древний расклад...")
- 10 cards sent as media group album
- "Читаю расклад..." thinking message during AI processing
- Full interpretation with all 10 positions

### Spread History
- History button in tarot menu
- Paginated list (5 per page, 100 max)
- Shows date, type (CC/3K), question preview
- Detail view with cards and interpretation
- Back navigation to list and tarot menu

### Spread Limits
- Premium: 20 spreads/day
- Free: 1 spread/day
- Both 3-card and Celtic Cross count toward limit
- Card of day remains unlimited

### Callbacks and Keyboards
- TarotAction extended: CELTIC_CROSS, DRAW_CELTIC, HISTORY
- HistoryCallback: LIST, VIEW, PAGE actions
- get_history_keyboard(): Paginated spread list
- get_spread_detail_keyboard(): Back navigation
- get_subscription_keyboard(): Navigate to premium

## Key Code Patterns

### Media Group for Album
```python
media_group = []
for i, (card, reversed_flag) in enumerate(cards):
    photo = get_card_image(card["name_short"], reversed_flag)
    caption = f"{i + 1}. {position}: {card['name']}{reversed_text}"
    media_group.append(InputMediaPhoto(media=photo, caption=caption))
await callback.message.answer_media_group(media_group)
```

### Save Spread to History
```python
cards_json = [
    {
        "card_id": card["name_short"],
        "reversed": reversed_flag,
        "position": i + 1,
    }
    for i, (card, reversed_flag) in enumerate(cards)
]
spread = TarotSpread(user_id=user_id, spread_type=spread_type, ...)
session.add(spread)
await session.commit()
```

### Limit Check with Premium
```python
def get_daily_limit(user: User) -> int:
    return DAILY_SPREAD_LIMIT_PREMIUM if user.is_premium else DAILY_SPREAD_LIMIT_FREE
```

## Commits

1. `47a4b81` - feat(08-01): add TarotSpread model and CelticCrossPrompt
2. `ee0f73f` - feat(08-01): add Celtic Cross spread and history UI

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] get_subscription_keyboard function**
- **Found during:** Task 2
- **Issue:** Celtic Cross premium teaser needed keyboard to navigate to subscription
- **Fix:** Added get_subscription_keyboard() to subscription keyboards using existing menu_subscription callback
- **Files modified:** src/bot/keyboards/subscription.py

## Next Phase Readiness

Ready for 08-02:
- TarotSpread model exists for any spread-related features
- History infrastructure can display natal chart history if needed
- Premium check pattern established for other premium features
