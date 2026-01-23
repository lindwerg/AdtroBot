---
phase: "07"
plan: "02"
subsystem: bot-handlers
tags: [fsm, birth-data, geocoding, premium, aiogram]
dependency-graph:
  requires: ["07-01"]
  provides: ["birth data collection UI", "profile natal setup button"]
  affects: ["07-03"]
tech-stack:
  added: []
  patterns: ["FSM for multi-step input", "Geocoding city search with selection"]
key-files:
  created:
    - src/bot/states/birth_data.py
    - src/bot/callbacks/birth_data.py
    - src/bot/keyboards/birth_data.py
    - src/bot/handlers/birth_data.py
  modified:
    - src/bot/handlers/__init__.py
    - src/bot/keyboards/profile.py
    - src/bot/handlers/menu.py
    - src/bot/bot.py
decisions: []
metrics:
  duration: "4 min"
  completed: "2026-01-23"
---

# Phase 7 Plan 2: Birth Data Collection UI Summary

**One-liner:** FSM flow для ввода времени/города рождения с geocoding и сохранением в User

## What Was Built

### 1. FSM States (src/bot/states/birth_data.py)
- `BirthDataStates.waiting_birth_time` - ожидание ввода времени HH:MM
- `BirthDataStates.waiting_birth_city` - ожидание ввода названия города
- `BirthDataStates.selecting_city` - выбор города из результатов поиска

### 2. Callbacks (src/bot/callbacks/birth_data.py)
- `CitySelectCallback(prefix="bcity")` - выбор города по индексу (idx: 0-4)
- `SkipTimeCallback(prefix="bskip")` - пропуск ввода времени

### 3. Keyboards (src/bot/keyboards/birth_data.py)
- `build_skip_time_keyboard()` - кнопка "Не знаю время" + отмена
- `build_city_selection_keyboard(cities)` - список городов (max 5) + retry/cancel
- `build_birth_data_complete_keyboard()` - навигация после успешного сохранения

### 4. Handlers (src/bot/handlers/birth_data.py)
- `start_birth_data_setup` - точка входа (callback="setup_birth_data")
- `skip_birth_time` - пропуск времени (используется 12:00)
- `process_birth_time` - парсинг HH:MM с валидацией
- `process_birth_city` - поиск через GeoNames, сохранение в state
- `select_city` - выбор из списка, сохранение в User
- `retry_city_search` - повторный ввод города
- `cancel_birth_data` - отмена с очисткой state

### 5. Profile Integration
- `build_profile_actions_keyboard()` - новая функция в profile.py
- Кнопка "Настроить натальную карту" для premium без birth_data
- Кнопка "Изменить данные рождения" для premium с birth_data
- Профиль показывает город и время рождения для premium

## Key Files

| File | Purpose |
|------|---------|
| `src/bot/states/birth_data.py` | 3 FSM состояния |
| `src/bot/callbacks/birth_data.py` | CitySelectCallback, SkipTimeCallback |
| `src/bot/keyboards/birth_data.py` | skip_time, city_selection, complete |
| `src/bot/handlers/birth_data.py` | 7 handlers (240 строк) |
| `src/bot/keyboards/profile.py` | build_profile_actions_keyboard |
| `src/bot/handlers/menu.py` | Показ birth data в профиле |
| `src/bot/bot.py` | birth_data_router в dispatcher |

## Commits

| Hash | Description |
|------|-------------|
| cc21645 | Add FSM states and callbacks for birth data |
| 14aac1d | Add keyboards for birth data collection |
| 256e6da | Add birth data collection handlers |

## Deviations from Plan

None - план выполнен точно как написано.

## Verification Results

| Check | Result |
|-------|--------|
| FSM states count | 3 |
| Callback handlers | 5 |
| Message handlers | 2 |
| Router in __init__ | birth_data |
| Dispatcher routers | 8 (includes birth_data) |

## User Flow

```
Профиль -> "Настроить натальную карту"
  -> Ввод времени (HH:MM или "Не знаю")
  -> Ввод города
  -> Выбор из списка GeoNames
  -> Сохранение в User (birth_time, birth_city, birth_lat, birth_lon)
  -> "Данные сохранены!"
```

## Next Phase Readiness

**Ready for 07-03:**
- Birth data сохраняется в User
- Natal chart service готов (из 07-01)
- Можно интегрировать в premium horoscope generation

**Blockers:**
- None

**Pending:**
- None
