# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-22)

**Core value:** Качественная AI интерпретация астрологии и таро, которая конвертирует бесплатных пользователей в платных
**Current focus:** Phase 2 - Bot Core + Onboarding (COMPLETE)

## Current Position

Phase: 2 of 9 (Bot Core + Onboarding) - COMPLETE
Plan: 2 of 2 completed in Phase 2
Status: Ready for Phase 3
Last activity: 2026-01-22 20:40 — Completed 02-02-PLAN.md (Onboarding Flow)

Progress: [████░░░░░░] 22%

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: 16 min
- Total execution time: 65 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 2/2 | 49 min | 25 min |
| 2 | 2/2 | 16 min | 8 min |

**Recent Trend:**
- Last 5 plans: 01-01 (4 min), 01-02 (45 min), 02-01 (12 min), 02-02 (4 min)
- Trend: Consistent fast execution for well-defined plans

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

### Pending Todos

- Add TELEGRAM_BOT_TOKEN and WEBHOOK_BASE_URL to Railway environment

### Blockers/Concerns

From research:
- kerykeion AGPL лицензия — требует проверки перед Phase 8 (натальная карта)
- AI costs unit economics — замерить в Phase 5

## Session Continuity

Last session: 2026-01-22 20:40
Stopped at: Completed 02-02-PLAN.md, Phase 2 complete
Resume file: None

**What's Ready:**
- Railway deployment: https://adtrobot-production.up.railway.app
- PostgreSQL database configured and migrated
- CI/CD pipeline: push to main -> test -> deploy
- User model with birth_date, zodiac_sign fields
- Health endpoint: /health returns {"status":"ok"}
- Bot module: src/bot/bot.py with get_bot() lazy creation
- Webhook endpoint: /webhook with secret validation
- DbSessionMiddleware for handler DB access
- **Onboarding flow complete:**
  - /start shows welcome for new users, menu for returning
  - FSM birthdate collection with Russian date parsing
  - Zodiac determination and DB save
  - Mock horoscope shown after registration (immediate value)
  - Main menu 2x2: Гороскоп, Таро, Подписка, Профиль
  - Menu handlers with mock content / teasers

**Next Steps:**
- Phase 3: Horoscope Generation (AI integration)
- Add TELEGRAM_BOT_TOKEN and WEBHOOK_BASE_URL to Railway before testing
- Replace mock horoscopes with AI-generated content
