---
phase: "07"
plan: "01"
subsystem: astrology
tags: [natal-chart, geocoding, pyswisseph, geopy, user-model]
dependency-graph:
  requires: ["06-03"]
  provides: ["natal chart calculation", "geocoding service", "birth location fields"]
  affects: ["07-02", "07-03"]
tech-stack:
  added: ["pyswisseph@2.10.3.2", "geopy@2.4.1"]
  patterns: ["Swiss Ephemeris for astronomy", "GeoNames for geocoding"]
key-files:
  created:
    - src/services/astrology/__init__.py
    - src/services/astrology/natal_chart.py
    - src/services/astrology/geocoding.py
    - migrations/versions/2026_01_23_a1b2c3d4e5f6_add_birth_location_fields.py
  modified:
    - src/db/models/user.py
    - src/config.py
    - pyproject.toml
decisions:
  - id: "07-01-D1"
    what: "pyswisseph вместо flatlib"
    why: "flatlib требует устаревшую pyswisseph 2.08, несовместимую с современными версиями"
    impact: "Прямое использование Swiss Ephemeris API, более низкоуровневый код"
metrics:
  duration: "6 min"
  completed: "2026-01-23"
---

# Phase 7 Plan 1: Premium Horoscopes Infrastructure Summary

**One-liner:** User model с birth location + pyswisseph natal chart + GeoNames geocoding

## What Was Built

### 1. User Model Extension
- Добавлены поля: `birth_time`, `birth_city`, `birth_lat`, `birth_lon`
- Миграция создана (применить на Railway)
- Все поля nullable для постепенного сбора данных

### 2. Natal Chart Service
- `calculate_natal_chart()` - вычисляет Sun, Moon, Ascendant
- Использует Swiss Ephemeris (pyswisseph) напрямую
- Поддержка noon chart когда время неизвестно
- NatalChartResult TypedDict для type safety

### 3. Geocoding Service
- `search_city()` - поиск города по названию
- GeoNames API через geopy
- Возвращает координаты и IANA timezone
- Graceful degradation при ошибках API

## Key Files

| File | Purpose |
|------|---------|
| `src/services/astrology/natal_chart.py` | Swiss Ephemeris расчет позиций |
| `src/services/astrology/geocoding.py` | GeoNames интеграция |
| `src/db/models/user.py` | Birth location fields |
| `src/config.py` | GEONAMES_USERNAME setting |

## Commits

| Hash | Description |
|------|-------------|
| 62d1639 | Add birth location fields to User model |
| 341ce21 | Add natal chart service with pyswisseph |
| f4081b5 | Add geocoding service with GeoNames |

## Deviations from Plan

### [Rule 3 - Blocking] flatlib incompatible with modern pyswisseph

- **Found during:** Task 2
- **Issue:** flatlib 0.2.3 requires pyswisseph 2.08.00-1, версия не существует в PyPI
- **Fix:** Установил pyswisseph@2.10.3.2 напрямую и реализовал natal_chart.py через Swiss Ephemeris API
- **Files modified:** natal_chart.py (custom implementation)
- **Impact:** Немного больше кода, но более современная версия Swiss Ephemeris

## Verification Results

| Check | Result |
|-------|--------|
| User model has birth_time | True |
| calculate_natal_chart('1990-06-15') | sun_sign='Gemini' |
| search_city('Moscow') | Works (demo account rate limited) |

## Dependencies Installed

```
pyswisseph = "^2.10.3.2"  # Swiss Ephemeris
geopy = "^2.4.1"          # GeoNames geocoder
```

## Configuration Required

```bash
# GeoNames (required for geocoding)
GEONAMES_USERNAME=your_username  # Register at geonames.org
```

## Next Phase Readiness

**Ready for 07-02:**
- Birth data collection UI
- Profile settings for birth time/city

**Blockers:**
- None

**Pending:**
- Run migration on Railway: `alembic upgrade head`
- Add GEONAMES_USERNAME to Railway environment
