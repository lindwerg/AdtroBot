---
phase: 01-infrastructure
plan: 02
subsystem: infra
tags: [ci-cd, github-actions, railway, deployment, postgres]

# Dependency graph
requires: [01]
provides:
  - GitHub Actions CI/CD pipeline
  - Railway deployment automation
  - PostgreSQL database connection
  - Automatic migrations on deploy
  - Production health endpoint
affects: [02-telegram-bot, 03-user-management]

# Tech tracking
tech-stack:
  added: [github-actions, railway, railway-cli]
  patterns: [ci-cd-pipeline, automatic-migrations, procfile-wrapper]

key-files:
  created:
    - .github/workflows/deploy.yml
    - Procfile
  modified: []

key-decisions:
  - "Procfile wrapper для миграций вместо release command"
  - "Railway CLI в GitHub Actions вместо non-existent action"
  - "DATABASE_URL через Railway reference для internal networking"
  - "Automatic migrations через alembic upgrade head в Procfile"

patterns-established:
  - "CI/CD: test (lint + pytest) -> deploy (only main branch)"
  - "Migrations: идемпотентные через alembic upgrade head при каждом старте"
  - "Railway: DATABASE_URL reference для автоматического internal networking"

# Metrics
duration: 45 min
completed: 2026-01-22
---

# Phase 1 Plan 2: CI/CD + Railway Deployment Summary

**GitHub Actions workflow для CI/CD, Railway deployment с автоматическими миграциями, PostgreSQL подключен**

## Performance

- **Duration:** 45 min
- **Started:** 2026-01-22T18:48:00Z
- **Completed:** 2026-01-22T19:38:00Z
- **Tasks:** 2 (1 auto, 1 checkpoint)
- **Files modified:** 2

## Accomplishments

- GitHub Actions workflow с test + deploy jobs
- Railway deployment через Railway CLI
- Procfile с автоматическими миграциями (`alembic upgrade head && uvicorn`)
- PostgreSQL подключен через DATABASE_URL reference
- Automatic migrations применяются при каждом deploy
- /health endpoint доступен по Railway URL
- CI проходит (lint + tests)

## Task Commits

1. **Task 1: GitHub Actions CI/CD workflow + Procfile** - `2c18b66` (feat)
2. **Bug fixes during deployment:**
   - `f472c07` - fix(ci): install dev dependencies for ruff
   - `ad54b7c` - fix(deps): use Poetry group syntax for dev dependencies
   - `18d6f21` - chore: update poetry.lock after pyproject changes
   - `322d6a0` - fix(ci): use Railway CLI directly instead of non-existent action
   - `0f9d814` - fix(config): add case-insensitive DATABASE_URL mapping for Railway
   - `d1d9659` - fix(logging): use logging.INFO instead of structlog.INFO

## Files Created/Modified

- `.github/workflows/deploy.yml` - CI/CD pipeline с test + deploy jobs
- `Procfile` - Railway startup command с автоматическими миграциями

## Decisions Made

1. **Procfile wrapper для миграций** - Railway release command может закэшироваться, Procfile wrapper гарантирует миграции перед каждым запуском
2. **Railway CLI вместо action** - railwayapp/cli-action не существует, используем npm install -g @railway/cli
3. **DATABASE_URL через reference** - Railway автоматически настраивает internal networking через reference
4. **Idempotent migrations** - alembic upgrade head идемпотентен, можно запускать при каждом старте

## Deviations from Plan

**Обнаруженные проблемы и исправления:**
1. Poetry dev dependencies требуют `[tool.poetry.group.dev.dependencies]` вместо `[project.optional-dependencies]`
2. Railway CLI action не существует - заменен на прямую установку CLI через npm
3. Pydantic Settings требует `validation_alias="DATABASE_URL"` для case-insensitive чтения env vars
4. structlog не имеет атрибута `INFO` - нужно использовать `logging.INFO`
5. Postgres сервис падал из-за internal networking проблем - пересоздан с правильным reference

## Issues Encountered

1. **ruff command not found** - решено через `poetry install --with dev`
2. **railwayapp/cli-action не существует** - решено установкой Railway CLI через npm
3. **DATABASE_URL case sensitivity** - решено через `validation_alias` в Pydantic
4. **structlog.INFO AttributeError** - решено через `import logging` и `logging.INFO`
5. **Postgres internal networking timeout** - решено пересозданием Postgres и использованием DATABASE_URL reference

## User Setup Required

**Railway Dashboard:**
- Project created: sincere-adaptation
- PostgreSQL plugin добавлен
- GitHub repo подключен: lindwerg/AdtroBot
- Wait for CI enabled
- DATABASE_URL reference настроен для AdtroBot service

**GitHub Secrets:**
- RAILWAY_TOKEN - настроен через gh CLI
- RAILWAY_SERVICE_ID - настроен через gh CLI

## Next Phase Readiness

- CI/CD pipeline работает: push в main -> test -> deploy
- Railway deployment автоматический с миграциями
- PostgreSQL готов для Phase 2 (User model уже мигрирована)
- Health endpoint доступен: https://adtrobot-production.up.railway.app/health
- Следующий шаг: Phase 2 (Telegram Bot - aiogram integration)

---
*Phase: 01-infrastructure*
*Completed: 2026-01-22*
