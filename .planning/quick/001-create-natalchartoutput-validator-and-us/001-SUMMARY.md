---
phase: quick
plan: 001
subsystem: ai
tags: [validation, natal-chart, bugfix]
dependency-graph:
  requires: [08-02]
  provides: [natal-chart-validation]
  affects: []
tech-stack:
  added: []
  patterns: [pydantic-validator]
key-files:
  created:
    - tests/services/ai/test_validators.py
  modified:
    - src/services/ai/validators.py
    - src/services/ai/client.py
decisions:
  - id: quick-001-001
    choice: "Section keywords: большая тройка, личность, развити, аспект, итог"
    reason: "Match NatalChartPrompt emoji-header sections"
metrics:
  duration: 5 min
  completed: 2026-01-23
---

# Quick Task 001: NatalChartOutput Validator

**One-liner:** Fix natal chart validation to match NatalChartPrompt sections (emoji headers).

## Problem

`generate_natal_interpretation()` used `validate_horoscope()` which checked for horoscope sections: `["любовь", "карьер", "здоровь", "финанс"]`.

But `NatalChartPrompt` generates different sections:
- 🌟 БОЛЬШАЯ ТРОЙКА
- 💫 ЛИЧНОСТЬ
- 🎯 ПУТЬ РАЗВИТИЯ
- ⚡ КЛЮЧЕВЫЕ АСПЕКТЫ
- 💎 ИТОГ

Result: All natal interpretations failed with "Отсутствуют разделы гороскопа (найдено 0/4)".

## Solution

1. Added `NatalChartOutput` Pydantic model with correct section keywords
2. Added `validate_natal_chart()` function
3. Updated `generate_natal_interpretation()` to use new validator

## Files Changed

### src/services/ai/validators.py
- Added `NatalChartOutput(BaseModel)` class with section validation
- Added `validate_natal_chart()` function
- Section keywords: `["большая тройка", "личность", "развити", "аспект", "итог"]`
- Requires 3/5 sections (flexible matching like horoscope validator)
- Length: 800-3000 chars

### src/services/ai/client.py
- Updated import to include `validate_natal_chart`
- Changed line 389: `validate_horoscope(text)` -> `validate_natal_chart(text)`

### tests/services/ai/test_validators.py (new)
- `test_validate_natal_chart_valid`: valid text passes
- `test_validate_natal_chart_invalid_sections`: horoscope-style fails
- `test_validate_natal_chart_too_short`: short text fails
- `test_validate_natal_chart_ai_pattern`: AI self-reference fails

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 8ef7b27 | fix | Add NatalChartOutput validator |
| 5f669f6 | fix | Use validate_natal_chart in client |
| 6a2fed8 | test | Add tests for validate_natal_chart |

## Verification

```bash
# Import works
python3 -c "from src.services.ai.validators import validate_natal_chart; print('OK')"
# OK

# Client imports updated
grep "validate_natal_chart" src/services/ai/client.py
# from src.services.ai.validators import validate_card_of_day, validate_horoscope, validate_natal_chart, validate_tarot
# is_valid, error = validate_natal_chart(text)

# Tests pass
pytest tests/services/ai/test_validators.py -v -k "natal"
# 4 passed
```

## Deviations from Plan

None - plan executed exactly as written.
