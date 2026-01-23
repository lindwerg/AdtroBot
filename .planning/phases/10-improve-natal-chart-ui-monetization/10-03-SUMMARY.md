---
phase: 10-improve-natal-chart-ui-monetization
plan: 03
subsystem: ai
tags: [ai, prompts, validation, caching, natal-chart]

dependency_graph:
  requires: [10-02]
  provides:
    - DetailedNatalPrompt with 8 sections
    - generate_detailed_natal_interpretation method
    - 7-day cache for detailed interpretations
  affects: [10-04]

tech_stack:
  added: []
  patterns:
    - sectioned-generation
    - in-memory-ttl-cache

files:
  created: []
  modified:
    - src/services/ai/prompts.py
    - src/services/ai/validators.py
    - src/services/ai/client.py

decisions:
  - id: sectioned-generation
    choice: "Generate each section independently with validation"
    reason: "Reliable long-form output (3000-5000 words)"
  - id: cache-ttl-7-days
    choice: "604800 seconds (7 days) TTL"
    reason: "Natal chart doesn't change, premium content worth caching"
  - id: section-tolerance
    choice: "20% tolerance on min_words"
    reason: "Allow slight variations in AI output"

metrics:
  duration: 3 min
  completed: 2026-01-23
---

# Phase 10 Plan 03: AI Prompt & Generator for Detailed Natal Summary

**One-liner:** DetailedNatalPrompt 8-секционная генерация 3600+ слов с 7-дневным кэшем

## What Was Done

### Task 1: DetailedNatalPrompt (fdf5c8d)
- Добавлен класс `DetailedNatalPrompt` в `prompts.py`
- 8 секций: core, mind, love, drive, growth, lessons, transformation, summary
- Общий минимум: 3600 слов (600+400+500+400+400+400+400+500)
- `format_natal_for_prompt()` форматирует данные натальной карты
- `section_prompt()` генерирует промпт для каждой секции

### Task 2: Валидаторы (04ec1b9)
- `validate_detailed_natal(text, min_chars=15000)` - полная валидация
  - Минимум 15000 символов (~3000 русских слов)
  - Проверка AI-паттернов
  - Проверка наличия секций (минимум 5 разделителей)
- `validate_detailed_natal_section(text, min_words)` - валидация секции
  - 20% толерантность на min_words
  - Проверка AI-паттернов

### Task 3: generate_detailed_natal_interpretation (0d79856)
- Секционная генерация: 8 секций независимо
- 3 попытки на секцию с валидацией
- 7-дневный кэш (`_detailed_natal_cache`, `DETAILED_NATAL_CACHE_TTL = 604800`)
- Использует `self._generate()` для API вызовов
- Логирование: cache_hit, generating, section_short, section_error, generated

## Files Modified

| File | Changes |
|------|---------|
| `src/services/ai/prompts.py` | +131 lines: DetailedNatalPrompt class |
| `src/services/ai/validators.py` | +59 lines: validate_detailed_natal, validate_detailed_natal_section |
| `src/services/ai/client.py` | +97 lines: cache vars, generate_detailed_natal_interpretation |

## Deviations from Plan

None - план выполнен точно как написано.

## Verification Results

```
1. Sections count: 8 == 8: True
2. Total min words: 3600 >= 3600: True
3. validate_detailed_natal checks min chars: True
4. Section 80% tolerance works: True
5. Method exists: True
6. Cache TTL = 604800: True
7. _generate() exists: True
```

## Next Phase Readiness

**Ready for 10-04:** UI handler для покупки детальной натальной интерпретации

**What 10-04 needs:**
- `generate_detailed_natal_interpretation(user_id, natal_data)` - ready
- DetailedNatal model (from 10-02) - ready
- Payment flow (from 10-02) - ready

## Commits

| Hash | Message |
|------|---------|
| fdf5c8d | feat(10-03): add DetailedNatalPrompt for 3000-5000 word interpretations |
| 04ec1b9 | feat(10-03): add validators for detailed natal interpretation |
| 0d79856 | feat(10-03): add generate_detailed_natal_interpretation method |
