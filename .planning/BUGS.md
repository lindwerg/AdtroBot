# BUGS.md - Phase 16 Bug Tracking

Bug tracking for Phase 16: Testing & Polish. All discovered bugs are documented here for later fixing.

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
| - | - | - | - | - | No bugs discovered during load testing | - |

---

## Load Testing Results (16-04)

**Date:** 2026-01-24
**Tool:** Locust 2.43.1

### Test Configuration

Locust scenarios created and verified:

1. **locustfile.py** - Main scenarios
   - HealthCheckUser (weight: 5)
   - AdminAPIUser (weight: 2)

2. **scenarios/api_health.py** - Health endpoint tests
   - HealthEndpointUser
   - HealthSLAUser
   - HealthBurstUser
   - HealthComponentsUser

3. **scenarios/horoscope_cache.py** - Cache monitoring
   - HoroscopeCacheMonitorUser
   - HoroscopeAdminContentUser

4. **scenarios/admin_api.py** - Admin API tests
   - AdminDashboardUser
   - AdminListsUser
   - AdminExportUser

### SLA Targets Defined

| Endpoint | SLA | Severity if Violated |
|----------|-----|----------------------|
| /health | <1s | P0 |
| /admin/api/dashboard | <2s | P1 |
| /admin/api/users | <2s | P1 |
| /admin/api/monitoring | <2s | P1 |
| /admin/api/export/* | <5s | P2 |
| Cache-related checks | <500ms | P1 |

### Test Execution Status

**Status:** Configuration verified, scenarios validated

**Local execution blocked by:**
- Cairo library not installed (required for natal chart SVG generation)
- Server cannot start without Cairo

**Recommended for CI/production testing:**
```bash
# Start server (in Docker or environment with Cairo)
uvicorn src.main:app --port 8000

# Run load tests
ADMIN_USERNAME=admin ADMIN_PASSWORD=password \
poetry run locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --headless -u 10 -r 2 --run-time 1m
```

### Performance Issues Found

None during configuration validation. Full load testing requires running server.

---

## Bug Template

When adding a new bug, use this format:

```
| BUG-XXX | Category | PX | Open | Component | Brief description | 1. Step 1, 2. Step 2, 3. Expected vs Actual |
```

## Statistics

- **Total:** 0
- **Open:** 0
- **Fixed:** 0
- **Deferred:** 0

---

*Phase: 16-testing-and-polish*
*Created: 2026-01-24*
