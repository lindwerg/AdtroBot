---
phase: 10-improve-natal-chart-ui-monetization
plan: 04
subsystem: bot-handlers
tags: [telegram, payments, yookassa, natal-chart, monetization]
depends_on:
  requires: ["10-01", "10-02", "10-03"]
  provides: ["complete-natal-purchase-flow", "detailed-natal-ui"]
  affects: []
tech-stack:
  added: []
  patterns: ["user-state-based-keyboards", "payment-flow", "telegraph-publishing"]
key-files:
  created: []
  modified:
    - src/services/ai/prompts.py
    - src/bot/callbacks/natal.py
    - src/bot/keyboards/natal.py
    - src/bot/handlers/natal.py
decisions:
  - id: brief-prompt-250-350
    choice: "Shorten NatalChartPrompt to 250-350 words as teaser"
    reason: "Free brief version encourages purchase of detailed 3000-5000 word version"
  - id: button-under-photo
    choice: "reply_markup on answer_photo for button under image"
    reason: "Telegram only supports clickable buttons under photos via reply_markup"
  - id: 15s-telegraph-timeout
    choice: "15 second timeout for detailed natal Telegraph publishing"
    reason: "Longer content (3000-5000 words) needs more time to publish"
metrics:
  duration: 4 min
  completed: 2026-01-23
---

# Phase 10 Plan 04: Detailed Natal Purchase UI Summary

Complete flow for free/premium/purchased natal chart display with YooKassa payment integration.

## One-Liner

UI handlers for detailed natal purchase: buy button (199 RUB), payment creation, and Telegraph-based display.

## What Was Built

### 1. NatalChartPrompt Update
- Shortened from 400-500 to 250-350 words
- Brief teaser format to encourage detailed purchase
- Simplified user() method with only key planets

### 2. NatalAction Extensions
- `BUY_DETAILED = "buy"` - trigger purchase flow
- `SHOW_DETAILED = "detailed"` - view purchased content

### 3. Three-State Keyboards
- `get_natal_with_buy_keyboard()` - premium users without purchase (shows 199 RUB price)
- `get_natal_with_open_keyboard()` - users who purchased
- `get_free_natal_keyboard()` - free users (subscription teaser)

### 4. Updated show_natal_chart
- Sends photo WITH reply_markup (button appears under image)
- Keyboard selection based on user.detailed_natal_purchased_at and user.is_premium
- Brief interpretation sent as separate message

### 5. buy_detailed_natal Handler
- Creates YooKassa payment for 199 RUB
- Double-buy protection (checks detailed_natal_purchased_at)
- Premium check before purchase
- Returns payment URL button

### 6. show_detailed_natal Handler
- Checks DetailedNatal cache for existing interpretation
- Generates via AI if not cached (generate_detailed_natal_interpretation)
- Publishes to Telegraph with 15s timeout
- Saves to DetailedNatal model with telegraph_url
- Fallback to text chunks if Telegraph fails

## Commits

| Hash | Type | Description |
|------|------|-------------|
| bd321d8 | feat | Update NatalChartPrompt and add BUY/SHOW_DETAILED actions |
| 558182d | feat | Add keyboards for detailed natal purchase flow |
| b5b87e3 | feat | Update show_natal_chart with button under photo |
| 7891190 | feat | Add buy_detailed_natal handler |
| cb433fc | feat | Add show_detailed_natal handler |

## Verification Results

All success criteria met:
- [x] NatalChartPrompt shortened to 250-350 words
- [x] NatalAction.BUY_DETAILED and SHOW_DETAILED added
- [x] Keyboards for all three flows created
- [x] Photo has reply_markup with button
- [x] buy_detailed_natal creates payment
- [x] show_detailed_natal generates and shows detailed interpretation
- [x] Telegraph integration for long text
- [x] Double-buy protection

## User Flow Summary

1. **Free User**: Sees natal chart PNG + "Получить полный разбор" -> subscription
2. **Premium (not purchased)**: Sees natal chart PNG + "Детальный разбор личности - 199.00 руб." -> payment
3. **Premium (purchased)**: Sees natal chart PNG + "Открыть детальный разбор" -> Telegraph article

## Deviations from Plan

None - plan executed exactly as written.

## Dependencies

- 10-01: Professional SVG visualization (for PNG generation)
- 10-02: Payment infrastructure (User.detailed_natal_purchased_at, DetailedNatal model)
- 10-03: AI prompt and generator (generate_detailed_natal_interpretation)

## Next Phase Readiness

Phase 10 complete. Full natal chart monetization flow implemented:
- Visual: Professional SVG with gradients and cosmic background
- Free: Brief 250-350 word teaser
- Paid: 3000-5000 word detailed interpretation for 199 RUB
- Storage: DetailedNatal cache with Telegraph URL
