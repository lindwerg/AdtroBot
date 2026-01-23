---
phase: 05-ai-integration
plan: 01
subsystem: ai
tags: [openrouter, gpt-4o-mini, openai-sdk, prompts, validation, caching]

# Dependency graph
requires:
  - phase: 04-free-tarot
    provides: Tarot cards data (78 cards with meanings)
  - phase: 03-free-horoscopes
    provides: Horoscope formatting and zodiac data
provides:
  - AIService class for OpenRouter/GPT-4o-mini integration
  - Prompt templates for horoscope, tarot spread, card of day
  - Output validation with length, structure, AI self-reference filter
  - In-memory TTL cache for horoscopes and card of day
affects: [05-02, phase-6, phase-7]

# Tech tracking
tech-stack:
  added: [openai>=1.50.0, tenacity>=8.2.0]
  patterns: [singleton-service, validation-retry, ttl-cache]

key-files:
  created:
    - src/services/ai/__init__.py
    - src/services/ai/client.py
    - src/services/ai/prompts.py
    - src/services/ai/validators.py
    - src/services/ai/cache.py
  modified:
    - pyproject.toml
    - src/config.py

key-decisions:
  - "GPT-4o-mini via OpenRouter (50x cheaper than Claude 3.5 Sonnet)"
  - "In-memory TTL cache (sufficient for MVP, clears on restart)"
  - "MAX_VALIDATION_RETRIES=2 for malformed outputs"
  - "30s timeout (GPT-4o-mini is fast)"
  - "Zodiac-specific greeting based on grammatical gender"

patterns-established:
  - "AI Service singleton via get_ai_service()"
  - "Validation retry loop with MAX_VALIDATION_RETRIES"
  - "System/user prompt separation for injection protection"
  - "Date-based TTL cache with expires_date"

# Metrics
duration: 5min
completed: 2026-01-23
---

# Phase 5 Plan 1: AI Service Module Summary

**GPT-4o-mini integration via OpenRouter with prompt templates, Pydantic validation, and TTL caching**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-23T08:19:01Z
- **Completed:** 2026-01-23T08:24:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- AIService class with generate_horoscope, generate_tarot_interpretation, generate_card_of_day methods
- Russian prompt templates with Barnum effect, friendly tone, zodiac-specific greetings
- Pydantic validators checking length, structure, filtering AI self-references
- In-memory TTL cache for horoscopes (by zodiac) and card of day (by user)
- OpenRouter API integration with 30s timeout, 3 retries, extra headers

## Task Commits

Each task was committed atomically:

1. **Task 1: Dependencies + Config** - `1192e87` (chore)
2. **Task 2: AI Service Module** - `811523a` (feat)

## Files Created/Modified
- `pyproject.toml` - Added openai>=1.50.0, tenacity>=8.2.0
- `src/config.py` - Added OPENROUTER_API_KEY field
- `src/services/ai/__init__.py` - Module exports
- `src/services/ai/client.py` - AIService class with generate methods
- `src/services/ai/prompts.py` - HoroscopePrompt, TarotSpreadPrompt, CardOfDayPrompt
- `src/services/ai/validators.py` - Pydantic models, validate_* functions
- `src/services/ai/cache.py` - TTL cache functions

## Decisions Made
- **GPT-4o-mini model:** $0.15/$0.60 per M tokens vs Claude's $6/$30 (50x savings)
- **Zodiac gender mapping:** Russian grammar requires "Дорогой Овен" (m) vs "Дорогая Дева" (f)
- **Validation retry:** Up to 2 retries with same prompt if output fails validation
- **Cache expiry:** Date-based (expires_date), not TTL seconds (simpler for daily content)
- **Forbidden patterns:** Regex filter for "как AI", "языковая модель", "я не могу" etc.

## Deviations from Plan

None - plan executed exactly as written.

## User Setup Required

**External services require manual configuration:**

Environment variable needed:
- `OPENROUTER_API_KEY` - Get from https://openrouter.ai/settings/keys -> Create New Key

Add to Railway:
```bash
railway variables set OPENROUTER_API_KEY=<your-key>
```

## Next Phase Readiness

**Ready:**
- AIService module complete with all 3 generate methods
- Prompts, validators, cache ready for handler integration
- Dependencies installed (openai, tenacity)

**Next step (05-02):**
- Integrate AIService into horoscope and tarot handlers
- Replace mock content with AI-generated
- Add fallback messages for errors

---
*Phase: 05-ai-integration*
*Completed: 2026-01-23*
