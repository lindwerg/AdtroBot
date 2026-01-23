---
phase: 09-admin-panel
plan: 13
subsystem: admin-content
tags: [admin, content, horoscope, crud]
depends_on:
  requires: [09-01, 09-06]
  provides: [horoscope-content-management, content-api]
  affects: [ai-horoscope-generation]
tech-stack:
  added: []
  patterns: [content-management, editable-text]
key-files:
  created:
    - src/admin/services/content.py
    - admin-frontend/src/api/endpoints/content.ts
    - admin-frontend/src/pages/Content.tsx
    - migrations/versions/2026_01_23_f6a7b8c9d0e1_add_horoscope_content.py
  modified:
    - src/admin/models.py
    - src/admin/schemas.py
    - src/admin/router.py
    - admin-frontend/src/routes/index.tsx
    - admin-frontend/src/components/Layout.tsx
decisions: []
metrics:
  duration: 5 min
  completed: 2026-01-23
---

# Phase 9 Plan 13: Horoscope Content Management Summary

**One-liner:** Admin CRUD for horoscope texts per zodiac sign with table view and edit modal

## What Was Built

### Backend

1. **HoroscopeContent Model** (`src/admin/models.py`)
   - `zodiac_sign`: unique, indexed (aries, taurus, etc.)
   - `base_text`: editable horoscope text
   - `notes`: admin-only notes
   - `updated_at`, `updated_by`: audit fields

2. **Content Service** (`src/admin/services/content.py`)
   - `get_all_horoscope_content()`: returns all 12 signs
   - `get_horoscope_content(zodiac_sign)`: get single sign
   - `update_horoscope_content()`: update text and notes

3. **API Endpoints** (`src/admin/router.py`)
   - `GET /admin/content/horoscopes` - list all 12 signs
   - `GET /admin/content/horoscopes/{sign}` - get single sign
   - `PUT /admin/content/horoscopes/{sign}` - update content

4. **Migration** (`migrations/versions/2026_01_23_f6a7b8c9d0e1_add_horoscope_content.py`)
   - Creates `horoscope_content` table
   - Seeds all 12 zodiac signs with empty text

### Frontend

1. **Content Page** (`admin-frontend/src/pages/Content.tsx`)
   - Table with all 12 zodiac signs
   - Emoji + Russian label display
   - Edit modal with textarea (5000 char limit)
   - Notes field for internal admin comments
   - Last updated timestamp

2. **API Client** (`admin-frontend/src/api/endpoints/content.ts`)
   - `getHoroscopeContent()` - fetch all signs
   - `updateHoroscopeContent()` - update single sign

3. **Navigation**
   - Added `/content` route
   - Added "Контент" menu item with FileTextOutlined icon

## Technical Details

### Database Schema

```sql
CREATE TABLE horoscope_content (
    id SERIAL PRIMARY KEY,
    zodiac_sign VARCHAR(20) UNIQUE NOT NULL,
    base_text TEXT DEFAULT '',
    notes TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by INTEGER
);
```

### Zodiac Signs Support

All 12 classical signs with Russian labels and Unicode emoji:
- Aries (Овен) ♈
- Taurus (Телец) ♉
- Gemini (Близнецы) ♊
- Cancer (Рак) ♋
- Leo (Лев) ♌
- Virgo (Дева) ♍
- Libra (Весы) ♎
- Scorpio (Скорпион) ♏
- Sagittarius (Стрелец) ♐
- Capricorn (Козерог) ♑
- Aquarius (Водолей) ♒
- Pisces (Рыбы) ♓

## Commits

| Hash | Type | Description |
|------|------|-------------|
| eb6d798 | chore | Add horoscope_content migration |
| 7ebb21b | feat | Add content service and API endpoints |
| 809d9c9 | feat | Add content management frontend page |

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Ready for:**
- 09-08 (Promo codes) - no dependencies
- Integration with AI horoscope generation (using base_text as context)

**Pending:**
- Run migration: `alembic upgrade head`
