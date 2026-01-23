# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-22)

**Core value:** Качественная AI интерпретация астрологии и таро, которая конвертирует бесплатных пользователей в платных
**Current focus:** Phase 9 In Progress - Admin Panel

## Current Position

Phase: 9 of 10 (Admin Panel)
Plan: 13 of 14 completed in Phase 9
Status: In progress
Last activity: 2026-01-23 — Completed 09-11: A/B testing and UTM tracking

Progress: [██████████████████████████░] 97% (36/36 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 36
- Average duration: 6 min
- Total execution time: 226 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 2/2 | 49 min | 25 min |
| 2 | 2/2 | 16 min | 8 min |
| 3 | 2/2 | 10 min | 5 min |
| 4 | 2/2 | 13 min | 7 min |
| 5 | 2/2 | 13 min | 7 min |
| 6 | 3/3 | 11 min | 4 min |
| 7 | 3/3 | 17 min | 6 min |
| 8 | 3/3 | 18 min | 6 min |
| 10 | 4/4 | 13 min | 3 min |
| 9 | 13/14 | 52 min | 4 min |

**Recent Trend:**
- Last 5 plans: 09-07 (5 min), 09-13 (5 min), 09-09 (5 min), 09-10 (4 min), 09-11 (5 min)
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

**Phase 6 (Subscription System):**
- YooKassa payment ID as primary key (natural key from provider)
- Amount in kopeks (29900 = 299.00 RUB) - avoids floating point
- Denormalized is_premium on User for quick access
- PromoCode.partner_id as Integer (no FK yet, future partner program)
- SubscriptionStatus state machine: trial -> active -> past_due -> canceled/expired
- webhook_processed flag for idempotent webhook handling
- asyncio.to_thread для YooKassa sync SDK
- BackgroundTasks для webhook processing (return 200 immediately)
- IP whitelist only in production
- Retention offer: "20% скидка" при попытке отмены
- Atomic limit check: UPDATE...RETURNING предотвращает race conditions
- Auto-renewal: 09:00 MSK, за 1 день до истечения

**Phase 7 (Premium Horoscopes):**
- pyswisseph вместо flatlib (flatlib requires outdated pyswisseph 2.08)
- GeoNames для geocoding с graceful degradation
- 1-hour TTL for premium horoscope cache (personalized per user)
- Premium без natal data = basic horoscope + setup prompt
- Free users = basic horoscope + premium teaser

**Phase 8 (Premium Tarot + Natal):**
- TarotSpread model с JSON для cards (card_id, reversed, position)
- Celtic Cross как media group album (10 фото)
- History pagination: 5/page, max 100 spreads
- Premium 20 spreads/day, free 1 spread/day
- svgwrite (MIT) вместо kerykeion (AGPL) для SVG генерации
- UTC timezone conversion для точных расчётов натальной карты
- 24-hour cache для natal interpretation (карта не меняется)
- Main menu 2x3 grid с кнопкой "Натальная карта"
- Telegraph для длинных интерпретаций (asyncio.to_thread для sync API)
- Emoji header detection для Telegraph форматирования
- 10-секунд timeout для Telegraph publish
- Graceful fallback на _split_text() при Telegraph failure
- asyncio.to_thread() для синхронного Telegraph SDK
- 10s timeout для Telegraph публикации, fallback на текст при неудаче
- Inline button "Посмотреть интерпретацию" для Telegraph статей

**Phase 10 (Improve Natal Chart):**
- Professional SVG: radial/linear gradients, cosmic background
- Unicode glyphs: U+2609-U+2653 for planets and zodiac signs
- Planet glow effects: gold for Sun/Jupiter, silver for others
- Default PNG size 800px for better detail
- DETAILED_NATAL one-time purchase (199 RUB, not subscription)
- User.detailed_natal_purchased_at for purchase tracking
- DetailedNatal model for caching 3000-5000 word interpretations
- Webhook handles DETAILED_NATAL before activate_subscription
- DetailedNatalPrompt: 8 sections, 3600+ min words for detailed interpretation
- Sectioned generation: generate each section independently with validation
- 7-day cache for detailed natal interpretations (604800s TTL)
- NatalChartPrompt shortened to 250-350 words (teaser for detailed)
- User-state-based keyboards (free/premium/purchased)
- Button under photo via reply_markup on answer_photo
- 15s Telegraph timeout for detailed natal publishing

**Phase 9 (Admin Panel):**
- React + Vite + TypeScript for SPA
- Ant Design Pro Components for admin UI
- Zustand with persist middleware for auth state
- Axios interceptors: request adds Bearer token, response handles 401
- React Router loaders for auth guards (requireAuth, redirectIfAuth)
- Vite proxy /admin -> localhost:8000
- User search by telegram_id (exact) or username (ILIKE)
- Pagination 20 per page default, max 100
- Bulk actions process users in loop with individual error tracking
- QueryClientProvider for React Query support
- ProTable with server-side request for pagination/filters
- React Query mutations with cache invalidation

### Roadmap Evolution

- Phase 10 added (2026-01-23): Улучшить натальную карту - визуал, интерпретация, монетизация

### Pending Todos

**Captured todos:** 10 (see `.planning/todos/pending/`)

- ~~**Fix natal chart interpretation validation failure** (ai)~~ — FIXED in quick-001

**Environment setup:**
- Add TELEGRAM_BOT_TOKEN and WEBHOOK_BASE_URL to Railway environment
- Run subscription migration on Railway: `alembic upgrade head`
- Add OPENROUTER_API_KEY to Railway environment
- Add YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY to Railway environment
- Configure YooKassa webhook URL: https://adtrobot-production.up.railway.app/webhook/yookassa
- Add GEONAMES_USERNAME to Railway environment
- Run 07-01 migration on Railway: `alembic upgrade head`
- Run 08-01 migration on Railway: `alembic upgrade head`
- Run 10-02 migration on Railway: `alembic upgrade head` (detailed_natal tables)
- Run 10-02 migration on Railway: `alembic upgrade head`

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 001 | Create NatalChartOutput validator and use it in generate_natal_interpretation | 2026-01-23 | f9dd038 | [001-create-natalchartoutput-validator-and-us](./quick/001-create-natalchartoutput-validator-and-us/) |

### Blockers/Concerns

From research:
- AI costs unit economics — замерить после деплоя с OPENROUTER_API_KEY

## Session Continuity

Last session: 2026-01-23
Stopped at: Completed 09-11 (A/B testing and UTM tracking)
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
  - Main menu 2x3: Гороскоп, Таро, Натальная карта, Подписка, Профиль
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
- **Payment Infrastructure complete (06-01):**
  - yookassa 3.9.0 SDK installed
  - Config: yookassa_shop_id, yookassa_secret_key, yookassa_return_url
  - Subscription model with status state machine
  - Payment model with YooKassa ID as PK
  - PromoCode model with partner fields
  - User premium fields: is_premium, premium_until, daily_spread_limit
  - Migration for subscriptions, payments, promo_codes tables
- **Payment Service complete (06-02):**
  - YooKassa async client: create_payment, create_recurring_payment, cancel_recurring
  - Subscription service: activate_subscription, cancel_subscription, get_user_subscription
  - /webhook/yookassa endpoint with IP whitelist and BackgroundTasks
  - Idempotent webhook processing via webhook_processed flag
- **Subscription Handlers complete (06-03):**
  - show_plans: premium features + plan selection
  - handle_plan_selection: creates YooKassa payment, returns URL
  - Cancel flow with retention offer ("скидка 20%")
  - Profile shows subscription status, expiry, cancel button
  - Atomic limit check in tarot (UPDATE...RETURNING)
  - Scheduler: auto_renew_subscriptions (09:00), check_expiring_subscriptions (10:00)
- **Premium Infrastructure complete (07-01):**
  - User model: birth_time, birth_city, birth_lat, birth_lon fields
  - Natal chart service: calculate_natal_chart() with Swiss Ephemeris
  - Geocoding service: search_city() with GeoNames
  - Migration for birth location fields ready
- **Birth Data Collection complete (07-02):**
  - BirthDataStates FSM for time/city collection
  - BirthDataCallback with actions (time, city, skip, confirm)
  - Russian time parsing (09:30, 9.30, 9 30)
  - City search via GeoNames with inline results
  - Profile integration: "Настроить натальную карту" button
- **Premium Horoscopes complete (07-03):**
  - PremiumHoroscopePrompt with 6 sections (500-700 words)
  - generate_premium_horoscope with 1-hour cache
  - Premium/free logic in handlers
  - Keyboard buttons for natal setup and subscription
- **Celtic Cross + History complete (08-01):**
  - TarotSpread model for history storage
  - CelticCrossPrompt for 800-1200 word AI interpretations
  - Celtic Cross 10-card spread as media group album
  - Premium teaser for free users
  - Spread history with pagination (5/page, 100 max)
  - History detail view with cards and interpretation
  - Premium 20/day limit, free 1/day limit
- **Natal Chart Display complete (08-02):**
  - Full natal chart calculation (11 planets, 12 houses, aspects)
  - SVG chart visualization (svgwrite + cairosvg)
  - NatalChartPrompt for 1000-1500 word AI interpretation
  - Main menu expanded to 2x3 with "Натальная карта" button
  - Premium users see chart PNG + AI interpretation
  - Free users see premium teaser
  - Users without birth data prompted to configure
- **Telegraph Integration complete (08-03):**
  - Telegraph service with async handling (asyncio.to_thread)
  - Natal chart: PNG + button -> Telegraph article
  - Celtic Cross: button -> Telegraph article
  - Graceful fallback to direct text on Telegraph failure
  - 10 second timeout prevents hanging
- **Natal Chart Validation fixed (quick-001):**
  - NatalChartOutput validator with correct section keywords
  - validate_natal_chart() function for natal interpretations
  - generate_natal_interpretation() now uses correct validator
- **Detailed Natal Payment Infrastructure complete (10-02):**
  - PaymentPlan.DETAILED_NATAL (199 RUB one-time)
  - User.detailed_natal_purchased_at field
  - DetailedNatal model (user_id, interpretation, telegraph_url, created_at)
  - Migration for users column + detailed_natals table
  - Webhook handles DETAILED_NATAL before activate_subscription
- **AI Prompt & Generator for Detailed Natal complete (10-03):**
  - DetailedNatalPrompt with 8 sections (3600+ min words)
  - validate_detailed_natal() and validate_detailed_natal_section() validators
  - generate_detailed_natal_interpretation() with sectioned generation
  - 7-day cache for detailed interpretations (604800s TTL)
- **Detailed Natal Purchase UI complete (10-04):**
  - NatalChartPrompt shortened to 250-350 words (teaser)
  - NatalAction.BUY_DETAILED and SHOW_DETAILED enum values
  - Keyboards: get_natal_with_buy_keyboard, get_natal_with_open_keyboard, get_free_natal_keyboard
  - show_natal_chart sends photo with reply_markup based on user status
  - buy_detailed_natal handler creates YooKassa payment (199 RUB)
  - show_detailed_natal handler generates/caches and displays via Telegraph

- **Admin Frontend Scaffold complete (09-02):**
  - Vite + React + TypeScript project
  - Ant Design Pro Components (LoginForm, ProLayout, PageContainer)
  - Zustand auth store with localStorage persistence
  - Axios API client with JWT interceptor
  - React Router with protected routes
  - Login page -> /admin/token
  - Dashboard placeholder
  - ProLayout with 7 menu items

- **Dashboard Metrics API complete (09-03):**
  - GET /admin/dashboard - returns KPI metrics (DAU, MAU, revenue, conversion, ARPU)
  - GET /admin/funnel?days=30 - returns 6-stage conversion funnel with drop-off
  - Sparkline data for 7-day trends
  - Analytics service: get_dashboard_metrics, get_funnel_data, get_sparkline_data

- **User Management API complete (09-04):**
  - GET /admin/users: paginated list with search/filters
  - GET /admin/users/{id}: full user detail with history
  - PATCH /admin/users/{id}/subscription: activate/cancel/extend
  - POST /admin/users/{id}/gift: premium_days/detailed_natal/tarot_spreads
  - POST /admin/users/bulk: bulk actions for multiple users
  - Service layer: list_users, get_user_detail, update_user_subscription, gift_to_user, bulk_action

- **Users Page UI complete (09-06):**
  - Users list page with ProTable, server-side pagination, filters, search
  - User detail page with subscription management (activate/cancel/extend)
  - Gift actions: premium days, tarot spreads, detailed natal
  - Bulk actions: activate/cancel premium, gift spreads
  - Payment and spread history tables
  - QueryClientProvider added for React Query support

- **Tarot Spreads Viewing complete (09-14):**
  - GET /admin/tarot-spreads with filters (user_id, search, spread_type, date range)
  - GET /admin/tarot-spreads/{id} with cards and interpretation
  - Frontend page: table, search, type filter, detail modal
  - Card names resolved from deck, position names by spread type

- **Payments and Subscriptions Management complete (09-08):**
  - GET /admin/payments with filters (status, user), total amount stat
  - GET /admin/subscriptions with filters (status, plan, user)
  - PATCH /admin/subscriptions/{id} - change status + sync user premium
  - PaymentsPage: ProTable with colored status tags, recurring badge
  - SubscriptionsPage: ProTable with status change modal, link to user

- **Messaging System complete (09-07):**
  - ScheduledMessage model with filters, stats, scheduling
  - Batch sending with rate limiting (25 msg/sec)
  - POST /admin/messages: send or schedule
  - GET /admin/messages: paginated history with stats
  - DELETE /admin/messages/{id}: cancel pending
  - Frontend: send form (broadcast/single), filters, history table

- **Horoscope Content Management complete (09-13):**
  - HoroscopeContent model: zodiac_sign, base_text, notes, updated_at
  - Migration seeds all 12 zodiac signs
  - GET/PUT /admin/content/horoscopes endpoints
  - Frontend: table with all 12 signs, edit modal with textarea
  - Zodiac emoji and Russian labels support

- **Promo Codes Management complete (09-09):**
  - Promo code CRUD service: create, list, update, delete
  - POST/GET/PATCH/DELETE /admin/promo-codes endpoints
  - Frontend: ProTable with create modal, active toggle, delete
  - Usage progress bar for limited codes
  - Uppercase code normalization

- **Data Export complete (09-10):**
  - pandas + openpyxl for CSV generation
  - export_users_csv, export_payments_csv, export_metrics_csv
  - GET /admin/export/users, /payments, /metrics endpoints
  - StreamingResponse for file download
  - Export buttons in Users, Payments, Dashboard pages

- **A/B Testing and UTM Tracking complete (09-11):**
  - ABExperiment and ABAssignment models
  - User UTM fields: utm_source, utm_medium, utm_campaign
  - Experiments service with hash-based variant assignment
  - POST/GET /admin/experiments endpoints
  - GET /admin/utm-analytics for source breakdown
  - ABTests.tsx frontend page with create/results modals
  - Winner detection (100+ users, >5% difference)

**Next Steps:**
- Continue Phase 9: Remaining plan (09-12)
