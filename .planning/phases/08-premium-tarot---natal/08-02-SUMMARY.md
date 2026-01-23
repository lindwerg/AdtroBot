---
phase: 08-premium-tarot-natal
plan: 02
status: complete

dependency-graph:
  requires:
    - "07-01 (birth data collection)"
    - "07-02 (birth time/city FSM)"
    - "05-01 (AI integration)"
  provides:
    - "Full natal chart calculation with all planets"
    - "SVG natal chart visualization"
    - "NatalChartPrompt for 1000-1500 word AI interpretation"
    - "Natal chart handlers with premium/free logic"
    - "Expanded main menu with Natal button"
  affects:
    - "Phase 9 (admin panel may need natal chart stats)"

tech-stack:
  added:
    - "svgwrite 1.4.3 (MIT license)"
    - "cairosvg 2.8.2 (LGPLv3)"
  patterns:
    - "SVG to PNG conversion via asyncio.to_thread"
    - "UTC timezone conversion for accurate calculations"
    - "24-hour cache for natal interpretation"

key-files:
  created:
    - "src/services/astrology/natal_svg.py"
    - "src/bot/handlers/natal.py"
    - "src/bot/callbacks/natal.py"
    - "src/bot/keyboards/natal.py"
  modified:
    - "src/services/astrology/natal_chart.py"
    - "src/services/ai/prompts.py"
    - "src/services/ai/client.py"
    - "src/services/ai/cache.py"
    - "src/bot/keyboards/main_menu.py"
    - "src/bot/handlers/__init__.py"
    - "src/bot/handlers/birth_data.py"
    - "src/bot/bot.py"
    - "pyproject.toml"

decisions:
  - id: "NATAL-UTC-CONVERSION"
    description: "Convert local birth time to UTC for Swiss Ephemeris calculations"
    rationale: "Accurate planetary positions require UTC time"
  - id: "NATAL-CACHE-24H"
    description: "Natal interpretation cached for 24 hours"
    rationale: "Birth chart is static, longer cache reduces AI costs"
  - id: "SVG-MIT-LIBRARY"
    description: "Use svgwrite (MIT) instead of kerykeion (AGPL)"
    rationale: "Avoid AGPL license contamination for commercial project"

metrics:
  duration: "8 min"
  completed: "2026-01-23"
---

# Phase 8 Plan 02: Natal Chart Summary

Full natal chart with all planets, houses, aspects + SVG visualization + AI interpretation for premium users

## What Was Built

### Full Natal Chart Calculation
- `src/services/astrology/natal_chart.py` extended with `calculate_full_natal_chart()`
- Calculates 11 planets: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, North Node
- Calculates 12 houses using Placidus system
- Calculates aspects between all planet pairs with standard orbs
- Returns `FullNatalChartResult` TypedDict with planets, houses, angles, aspects
- CRITICAL: Converts local birth time to UTC using pytz for accurate calculations

### SVG Natal Chart Visualization
- `src/services/astrology/natal_svg.py` creates visual chart
- Dark theme matching bot style (#1a1a2e background)
- Outer zodiac wheel with 12 signs
- Planet positions as colored circles with abbreviations
- Aspect lines between planets (blue=harmonious, red=challenging)
- Ascendant and MC markers
- Uses `asyncio.to_thread()` for cairosvg conversion (CPU-bound)
- Output: PNG image (600x600 default)

### NatalChartPrompt
- Added to `src/services/ai/prompts.py`
- SYSTEM prompt for 1000-1500 word interpretation
- Sections:
  - Big Three (Sun, Moon, Ascendant)
  - Personal planets (Mercury, Venus, Mars)
  - Social planets (Jupiter, Saturn)
  - Outer planets (Uranus, Neptune, Pluto)
  - Major aspects
  - Life areas (personality, relationships, career, health)
  - Final message with recommendations
- Simple language suitable for beginners

### generate_natal_interpretation Method
- Added to AIService in `src/services/ai/client.py`
- max_tokens=4000 for longer response
- 24-hour TTL cache (natal chart doesn't change daily)
- Uses horoscope validation (length + no AI self-reference)

### Natal Handlers
- `src/bot/handlers/natal.py` with router
- `menu_natal_chart()`: Handles "Натальная карта" text button
- Premium user with birth data: Shows PNG chart + AI interpretation
- Premium user without birth data: Prompts to configure
- Free user: Shows premium teaser with subscription button
- Text splitting for messages > 4096 chars

### Main Menu Expansion
- Changed from 2x2 to 2x3 grid (5 buttons)
- Added "Натальная карта" button
- Layout: Гороскоп | Таро | Натальная карта | Подписка | Профиль

### Callbacks and Keyboards
- `NatalCallback` with prefix "n"
- `NatalAction` enum: SHOW_CHART, BACK_TO_MENU
- `get_natal_setup_keyboard()`: Links to birth data setup
- `get_natal_teaser_keyboard()`: Links to subscription

## Key Code Patterns

### UTC Timezone Conversion
```python
local_tz = pytz.timezone(timezone_str)
dt = datetime.combine(birth_date, birth_time)
dt_local = local_tz.localize(dt)
dt_utc = dt_local.astimezone(pytz.UTC)
hour_ut = dt_utc.hour + dt_utc.minute / 60.0
```

### Aspect Calculation
```python
for i, p1 in enumerate(planet_names):
    for p2 in planet_names[i + 1:]:
        diff = abs(lon1 - lon2)
        if diff > 180:
            diff = 360 - diff
        for angle, (name, name_ru, orb) in ASPECTS.items():
            if abs(diff - angle) <= orb:
                aspects.append({...})
```

### PNG Generation
```python
png_bytes = await asyncio.to_thread(
    cairosvg.svg2png,
    bytestring=svg_string.encode("utf-8"),
)
photo = BufferedInputFile(png_bytes, filename="natal_chart.png")
await message.answer_photo(photo=photo, caption="Твоя натальная карта")
```

## Commits

1. `8009ad3` - feat(08-02): add full natal chart calculation and SVG generation
2. `1c061b5` - feat(08-02): add NatalChartPrompt and generate_natal_interpretation
3. `c2b44b5` - feat(08-02): add natal chart handlers and expand main menu

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Timezone not saved when selecting birth city**
- **Found during:** Task 3
- **Issue:** Birth data handler saved city coordinates but not timezone
- **Fix:** Added `user.timezone = city["timezone"]` when saving birth city
- **Files modified:** src/bot/handlers/birth_data.py
- **Commit:** c2b44b5

## Next Phase Readiness

Ready for Phase 9 (Admin Panel):
- Full natal chart infrastructure complete
- All premium features (horoscopes, tarot, natal) implemented
- Subscription system operational
- History storage in place
