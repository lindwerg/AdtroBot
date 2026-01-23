# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-22)

**Core value:** Качественная AI интерпретация астрологии и таро, которая конвертирует бесплатных пользователей в платных
**Current focus:** Phase 5 - AI Integration (COMPLETE)

## Current Position

Phase: 5 of 9 (AI Integration)
Plan: 2 of 2 completed in Phase 5 (PHASE COMPLETE)
Status: Phase complete
Last activity: 2026-01-23 08:38 — Completed 05-02-PLAN.md (Handler Integration)

Progress: [██████████] 100% (Phase 5)

## Performance Metrics

**Velocity:**
- Total plans completed: 10
- Average duration: 10 min
- Total execution time: 101 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 2/2 | 49 min | 25 min |
| 2 | 2/2 | 16 min | 8 min |
| 3 | 2/2 | 10 min | 5 min |
| 4 | 2/2 | 13 min | 7 min |
| 5 | 2/2 | 13 min | 7 min |

**Recent Trend:**
- Last 5 plans: 04-01 (10 min), 04-02 (3 min), 05-01 (5 min), 05-02 (8 min)
- Trend: Consistent fast execution

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

**Phase 1 (Infrastructure):**
- expire_on_commit=False для async SQLAlchemy sessions
- naming_convention для всех constraints (pk_, uq_, fk_, ix_, ck_)
- async_database_url property для Railway URL transform
- Procfile wrapper для миграций вместо release command
- Railway CLI вместо non-existent GitHub Action
- DATABASE_URL через Railway reference для internal networking
- structlog с JSON logs для production, console для dev

**Phase 2 (Bot Core):**
- Lazy Bot creation via get_bot() — aiogram validates token at import
- DbSessionMiddleware injects session directly (handler controls commit)
- Mock horoscopes for immediate value — 12 hardcoded texts, AI in Phase 3
- explicit session.commit() in handler — DbSessionMiddleware does NOT auto-commit
- Router order: start -> menu -> common (catch-all last)

**Phase 3 (Free Horoscopes):**
- aiogram.utils.formatting for entity-based messages (auto-escaping)
- Short CallbackData prefix "z" and field "s" (64-byte Telegram limit)
- Classical zodiac order in keyboard (Aries -> Pisces)
- APScheduler SQLAlchemyJobStore with psycopg2-binary for persistent jobs
- Notification defaults: Europe/Moscow, 9:00, opt-in

**Phase 4 (Free Tarot):**
- Card images from xiaodeaux/tarot-image-grabber (Wikipedia public domain)
- Card data from ekelen/tarot-api (78 cards with meanings)
- Image rotation 180 degrees for reversed cards via Pillow
- Singleton deck loading via get_deck() with lazy initialization

**Phase 5 (AI Integration):**
- GPT-4o-mini via OpenRouter (50x cheaper than Claude 3.5 Sonnet)
- In-memory TTL cache (sufficient for MVP, clears on restart)
- MAX_VALIDATION_RETRIES=2 for malformed outputs
- 30s timeout (GPT-4o-mini is fast)
- Zodiac-specific greeting based on grammatical gender
- AI text displayed directly with minimal header formatting
- Fallback to error message for horoscopes, static meanings for tarot

### Pending Todos

- Add TELEGRAM_BOT_TOKEN and WEBHOOK_BASE_URL to Railway environment
- Run tarot migration on Railway: `alembic upgrade head`
- Add OPENROUTER_API_KEY to Railway environment

### Blockers/Concerns

From research:
- kerykeion AGPL лицензия — требует проверки перед Phase 8 (натальная карта)
- AI costs unit economics — замерить после деплоя с OPENROUTER_API_KEY

## Session Continuity

Last session: 2026-01-23 08:38
Stopped at: Completed 05-02-PLAN.md (Phase 5 complete!)
Resume file: None

**What's Ready:**
- Railway deployment: https://adtrobot-production.up.railway.app
- PostgreSQL database configured and migrated
- CI/CD pipeline: push to main -> test -> deploy
- User model with birth_date, zodiac_sign, timezone, notification_hour, notifications_enabled
- Health endpoint: /health returns {"status":"ok"}
- Bot module: src/bot/bot.py with get_bot() lazy creation
- Webhook endpoint: /webhook with secret validation
- DbSessionMiddleware for handler DB access
- **Onboarding flow complete:**
  - /start shows welcome for new users, menu for returning
  - FSM birthdate collection with Russian date parsing
  - Zodiac determination and DB save
  - Mock horoscope shown after registration (immediate value)
  - Onboarding notification prompt after first horoscope
  - Main menu 2x2: Гороскоп, Таро, Подписка, Профиль
  - Menu handlers with mock content / teasers
- **Horoscope formatting complete (03-01):**
  - Entity-based formatting with Bold + BlockQuote
  - 4x3 inline keyboard for zodiac navigation
  - ZodiacCallback handler for sign switching
  - show_horoscope_message() reusable function
- **Daily notifications complete (03-02):**
  - APScheduler with SQLAlchemyJobStore (persistent jobs)
  - schedule_user_notification / remove_user_notification
  - Profile settings UI: toggle, time, timezone
  - 8 Russian timezones, 6 time slots (07:00-12:00)
  - Migration for notification fields ready
- **Tarot infrastructure complete (04-01):**
  - 78-card Rider-Waite deck (JSON + images)
  - tarot_cards.py: get_deck, get_random_card, get_three_cards, get_card_image
  - tarot_formatting.py: format_card_of_day, format_three_card_spread
  - User model with card_of_day cache and spread limit fields
  - Migration for tarot fields ready
- **Tarot handlers complete (04-02):**
  - TarotStates FSM, TarotCallback, tarot keyboards
  - Card of day: ritual, cache, image, interpretation (no limits)
  - 3-card spread: FSM question, 1/day limit, ritual, cards, interpretation
  - Menu "Tarot" leads to tarot submenu
- **AI Integration complete (05-01, 05-02):**
  - AIService class with generate_horoscope, generate_tarot_interpretation, generate_card_of_day
  - Prompt templates: HoroscopePrompt, TarotSpreadPrompt, CardOfDayPrompt
  - Validators: length, structure, AI self-reference filter
  - Cache: in-memory TTL for horoscopes and card of day
  - Horoscope handlers use AI with fallback to error message
  - Card of day uses AI interpretation with fallback to static meaning
  - 3-card spread uses AI interpretation with fallback to static meanings

**Next Steps:**
- Add OPENROUTER_API_KEY to Railway environment
- Phase 6: Subscription System
