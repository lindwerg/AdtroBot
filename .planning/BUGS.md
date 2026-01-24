# BUGS.md - Phase 16 Bug Tracking

Bug tracking for Phase 16: Testing & Polish. All discovered bugs are documented here for later fixing.

## Summary

- **Total bugs discovered:** 0
- **P0 (Critical):** 0
- **P1 (High):** 0
- **P2 (Medium):** 0
- **P3 (Low):** 0

**Note:** All test suites were executed but couldn't discover runtime bugs due to infrastructure blockers (Cairo library, Telegram credentials). Tests compile and are ready for execution in proper environment.

## Bug Categories

- **Bot** - Telegram bot issues
- **Admin** - Admin panel issues
- **Backend** - API/database/services
- **Frontend** - React UI issues

## Severity Levels

- **P0** - Critical: App crashes, data loss, security vulnerability
- **P1** - High: Feature broken, major UX issue
- **P2** - Medium: Feature works but has issues
- **P3** - Low: Minor cosmetic/text issues

## Bug Table

| ID | Category | Severity | Status | Component | Description | Steps to Reproduce |
|----|----------|----------|--------|-----------|-------------|-------------------|
| - | - | - | - | - | No runtime bugs discovered (tests blocked by infrastructure) | - |

---

## Test Execution Results (16-05)

**Date:** 2026-01-24
**Executed by:** Automated test runner

### 1. Playwright E2E Tests (Admin Frontend)

**Status:** BLOCKED
**Reason:** Backend server cannot start without Cairo library

**Execution attempt:**
```bash
cd admin-frontend && ADMIN_USERNAME=admin ADMIN_PASSWORD=password npx playwright test --reporter=list
```

**Result:**
```
Error: Timed out waiting 120000ms from config.webServer.
```

**Blocker details:**
- Cairo library required for natal chart SVG generation
- Server import chain: main.py -> admin/router.py -> bot/handlers/natal.py -> services/astrology/natal_svg.py -> cairosvg
- Error: `OSError: no library called "cairo-2" was found`

**TypeScript compilation:** PASS (npx tsc --noEmit)

**Test coverage prepared:**
- 51 tests in 6 files
- 6 Page Object Models
- Full admin panel coverage

### 2. Telethon E2E Tests (Bot)

**Status:** SKIPPED
**Reason:** Missing Telegram API credentials

**Execution attempt:**
```bash
poetry run pytest tests/e2e/ -v --tb=short
```

**Result:**
```
4 skipped in 0.06s
SKIPPED (TELEGRAM_API_ID and TELEGRAM_API_HASH must be set for Telegram E2E tests)
```

**Required credentials:**
- TELEGRAM_API_ID
- TELEGRAM_API_HASH
- TELETHON_SESSION (StringSession for headless execution)
- BOT_USERNAME

**Test coverage prepared:**
- 45 tests in 6 files
- Covers: start, horoscope, tarot, natal, profile, subscription flows

### 3. Locust Load Tests

**Status:** EXECUTED (no server)
**Reason:** Server not running, all requests failed with connection refused

**Execution attempt:**
```bash
ADMIN_USERNAME=admin ADMIN_PASSWORD=password poetry run locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 --headless -u 5 -r 1 --run-time 10s
```

**Result:**
```
Total requests: 98
Failed requests: 98
Failure rate: 100.00%
Median response time: 1.1ms
95th percentile: 6ms

Error report:
- 97x GET /health: Health check failed: 0
- 1x POST /admin/api/token: ConnectionRefusedError(61, 'Connection refused')
```

**Note:** Locust framework works correctly. Response times (1-7ms) are connection refused latencies, not server response times.

**Test scenarios prepared:**
- locustfile.py (HealthCheckUser, AdminAPIUser)
- scenarios/api_health.py (4 SLA test users)
- scenarios/horoscope_cache.py (cache monitoring)
- scenarios/admin_api.py (dashboard, lists, export)

---

## Infrastructure Blockers

### Cairo Library (P0 Blocker)

**Impact:** Blocks all Playwright and Locust tests
**Component:** src/services/astrology/natal_svg.py

**Solution:**
```bash
# macOS
brew install cairo

# Ubuntu/Debian
apt-get install libcairo2-dev

# Docker (recommended)
# Use image with Cairo pre-installed
```

### Telegram Credentials (P1 Blocker)

**Impact:** Blocks all Telethon bot tests
**Required:** TELEGRAM_API_ID, TELEGRAM_API_HASH, TELETHON_SESSION

**Solution:**
1. Get API credentials from https://my.telegram.org
2. Generate StringSession for CI

---

## UX Polish Completed (16-05)

The following UX improvements were made in Tasks 1-2:

### Loading States (Task 1)
- Dashboard: Spin wrapper for metrics loading
- Users: Table loading state, skeleton rows
- Monitoring: Chart loading indicators

**Files modified:**
- admin-frontend/src/pages/Dashboard.tsx
- admin-frontend/src/pages/Users.tsx
- admin-frontend/src/pages/Monitoring.tsx

**Commit:** c040842

### Empty States & Error Messages (Task 2)
- Messages: Empty state with "Нет отправленных сообщений"
- Error alerts with human-readable messages
- "Повторить" button for retry functionality

**Files modified:**
- admin-frontend/src/pages/Messages.tsx

**Commit:** 71e114f

---

## Recommendations for Next Phase

1. **Install Cairo library** in development and CI environments
2. **Set up Telegram test account** with API credentials for bot E2E
3. **Create Docker compose** for local development with all dependencies
4. **Run full test suite** in CI environment after infrastructure setup

---

*Phase: 16-testing-and-polish*
*Generated: 2026-01-24*
*Test execution: Automated*
