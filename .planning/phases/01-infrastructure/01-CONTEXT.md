# Phase 1: Infrastructure - Context

**Gathered:** 2026-01-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Настройка foundation для Telegram бота — PostgreSQL база данных, SQLAlchemy async ORM, Alembic миграции, Railway deployment с автоматическим CI/CD через GitHub Actions. Создаётся минимальная инфраструктура для запуска бота, без избыточных компонентов.

</domain>

<decisions>
## Implementation Decisions

### Database schema scope
- Создавать таблицы **поэтапно по фазам** — только то, что нужно сейчас
- Phase 1: базовая структура для users (telegram_id, registration basics)
- Subscriptions, payments, readings — добавятся в соответствующих фазах
- Никаких "на будущее" полей — строго по requirements текущей фазы

### Deployment workflow
- **Полная автоматизация:** GitHub push в main → автоматический deploy на Railway
- Никакого staging environment (пока не нужен)
- Никаких manual approvals — fast iterations
- Railway logs для мониторинга и отладки

### Local development setup
- **Minimal setup:** Poetry для dependencies + local PostgreSQL
- `.env` файл для локальных secrets (в `.gitignore`)
- Docker Compose — только если понадобится, не сейчас
- Простая команда `poetry install && alembic upgrade head` для старта

### Secrets management
- **Local:** `.env` файл (TELEGRAM_TOKEN, DATABASE_URL, etc.) в `.gitignore`
- **Production:** Railway environment variables через dashboard
- Sync вручную через Railway UI — просто и понятно
- Environments: только dev (local) и production (Railway)

### Claude's Discretion
- Точная структура Alembic migrations (naming, автогенерация)
- Logging format и levels (structlog или аналог)
- SQLAlchemy session management patterns
- GitHub Actions YAML structure для CI/CD

</decisions>

<specifics>
## Specific Ideas

- "Делай всё идеально и автоматически" — фокус на automation и simple workflows
- "Базы данных по фазам" — никакого big upfront design, только что нужно сейчас
- "Push → deploy автоматом" — максимальная скорость итераций

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-infrastructure*
*Context gathered: 2026-01-22*
