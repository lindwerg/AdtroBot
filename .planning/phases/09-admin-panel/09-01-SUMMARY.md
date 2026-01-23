---
phase: 09-admin-panel
plan: 01
subsystem: auth
tags: [jwt, bcrypt, fastapi, cors, admin]

# Dependency graph
requires:
  - phase: 06-payments
    provides: User model with premium fields
provides:
  - Admin SQLAlchemy model with hashed password
  - JWT authentication module (verify_password, hash_password, create_access_token, get_current_admin)
  - Admin API router with /admin/token and /admin/me endpoints
  - CORS middleware for localhost development
affects: [09-admin-panel] # All other admin panel plans will use this auth

# Tech tracking
tech-stack:
  added: [python-jose, bcrypt, python-multipart]
  patterns: [OAuth2PasswordBearer for JWT auth, bcrypt direct usage]

key-files:
  created:
    - src/admin/__init__.py
    - src/admin/models.py
    - src/admin/auth.py
    - src/admin/schemas.py
    - src/admin/router.py
    - migrations/versions/2026_01_23_d4e5f6a7b8c9_add_admin_table.py
  modified:
    - src/config.py
    - src/main.py
    - migrations/env.py
    - pyproject.toml

key-decisions:
  - "bcrypt direct instead of passlib (passlib incompatible with bcrypt 5.x)"
  - "HS256 algorithm for JWT tokens"
  - "30 minute JWT expiration by default"

patterns-established:
  - "Admin auth via OAuth2PasswordBearer with /admin/token endpoint"
  - "get_current_admin dependency for protected routes"

# Metrics
duration: 8min
completed: 2026-01-23
---

# Phase 9 Plan 01: Backend foundation with JWT authentication Summary

**Admin model with bcrypt password hashing, JWT auth via python-jose, and FastAPI router with CORS for admin panel**

## Performance

- **Duration:** 8 min
- **Started:** 2026-01-23T09:00:00Z
- **Completed:** 2026-01-23T09:08:00Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments

- Admin SQLAlchemy model with username, hashed_password, is_active, created_at
- JWT authentication module with password verification and token creation
- Admin API router with /token (login) and /me (current admin) endpoints
- CORS middleware configured for localhost development servers

## Task Commits

Each task was committed atomically:

1. **Task 1: Admin model and config** - `936738e` (feat)
2. **Task 2: JWT authentication module** - `a79f84f` (feat)
3. **Task 3: Admin router and CORS setup** - `cbb255e` (feat)

## Files Created/Modified

- `src/admin/__init__.py` - Admin module init
- `src/admin/models.py` - Admin SQLAlchemy model
- `src/admin/auth.py` - JWT auth functions (verify_password, hash_password, create_access_token, get_current_admin)
- `src/admin/schemas.py` - Pydantic schemas (Token, AdminInfo)
- `src/admin/router.py` - FastAPI router with /admin/token and /admin/me
- `src/config.py` - Added admin_jwt_secret and admin_jwt_expire_minutes
- `src/main.py` - Added CORS middleware and admin_router include
- `migrations/env.py` - Import admin models for Alembic
- `migrations/versions/2026_01_23_d4e5f6a7b8c9_add_admin_table.py` - Migration for admins table
- `pyproject.toml` - Added python-jose, bcrypt, python-multipart dependencies

## Decisions Made

- **bcrypt direct usage:** passlib has compatibility issues with bcrypt 5.x (AttributeError on __about__). Using bcrypt library directly.
- **HS256 algorithm:** Standard symmetric algorithm for JWT, sufficient for admin auth
- **CORS origins:** localhost:5173 (Vite) and localhost:3000 (alternative dev server)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Replaced passlib with direct bcrypt**
- **Found during:** Task 2 (JWT authentication module)
- **Issue:** passlib incompatible with bcrypt 5.x - AttributeError: module 'bcrypt' has no attribute '__about__'
- **Fix:** Removed passlib, used bcrypt library directly for hash_password and verify_password
- **Files modified:** src/admin/auth.py, pyproject.toml
- **Verification:** hash_password("test") returns $2b$ prefixed hash
- **Committed in:** a79f84f

**2. [Rule 3 - Blocking] Added python-multipart dependency**
- **Found during:** Task 3 (Admin router)
- **Issue:** OAuth2PasswordRequestForm requires python-multipart for form data parsing
- **Fix:** Added python-multipart via poetry add
- **Files modified:** pyproject.toml, poetry.lock
- **Verification:** Router imports successfully
- **Committed in:** cbb255e

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes necessary for dependencies to work correctly. No scope creep.

## Issues Encountered

- Cairo library not installed locally (for SVG generation) - not related to admin panel, existing functionality for natal charts

## User Setup Required

After deployment:
1. Run migration: `alembic upgrade head`
2. Set ADMIN_JWT_SECRET in Railway (or use auto-generated)
3. Create initial admin user manually in database:
   ```sql
   INSERT INTO admins (username, hashed_password, is_active)
   VALUES ('admin', '$2b$12$...', true);
   ```
   Use `hash_password()` function to generate hash.

## Next Phase Readiness

- Admin authentication ready
- /admin/token returns JWT on valid credentials
- /admin/me returns current admin with get_current_admin dependency
- Ready for dashboard endpoints (09-02)

---
*Phase: 09-admin-panel*
*Completed: 2026-01-23*
