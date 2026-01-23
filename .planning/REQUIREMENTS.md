# Requirements: AdtroBot

**Defined:** 2026-01-23
**Core Value:** Качественная AI интерпретация астрологии и таро, которая конвертирует бесплатных пользователей в платных подписчиков

## v2.0 Requirements

Requirements для v2.0: Production Polish & Visual Enhancement

### Performance Optimizations

- [ ] **PERF-01**: Typing indicator при AI генерации (horoscope, tarot, natal chart)
- [ ] **PERF-02**: PostgreSQL-backed cache для гороскопов
- [ ] **PERF-03**: Фоновая генерация 12 общих гороскопов каждые 12ч (APScheduler job)
- [ ] **PERF-04**: Оптимизация /start — быстрая загрузка меню
- [ ] **PERF-05**: file_id caching для изображений в PostgreSQL
- [ ] **PERF-06**: Cache race condition prevention (lock per zodiac sign)
- [ ] **PERF-07**: Cache warming при старте приложения (preload активных гороскопов)

### Visual Enhancement

- [ ] **VIS-01**: Welcome screen изображение
- [ ] **VIS-02**: 12 изображений для знаков зодиака
- [ ] **VIS-03**: Изображения для раскладов таро
- [ ] **VIS-04**: Изображение для натальной карты
- [ ] **VIS-05**: Изображение для paywall/premium offer
- [ ] **VIS-06**: file_id хранение в PostgreSQL (image_assets таблица)
- [ ] **VIS-07**: Автоматическая отправка изображений по file_id

### UX Improvements

- [ ] **UX-01**: Визуальное разделение общий vs персональный гороскоп
- [ ] **UX-02**: Исправление Markdown форматирования (разметка не должна быть видна)
- [ ] **UX-03**: Понятная воронка free → premium
- [ ] **UX-04**: Улучшение первого прогноза после ввода даты

### Welcome Flow

- [ ] **WEL-01**: Engaging текст приветствия /start
- [ ] **WEL-02**: BotFather description обновление
- [ ] **WEL-03**: Onboarding tutorial для новичков
- [ ] **WEL-04**: About/FAQ команда

### Monitoring & Metrics

- [ ] **MON-01**: horoscopes_today tracking таблица
- [ ] **MON-02**: Bot Health metrics (uptime, errors, response time)
- [ ] **MON-03**: API Costs tracking (OpenRouter spending по операциям)
- [ ] **MON-04**: Unit economics dashboard в админке
- [ ] **MON-05**: Prometheus metrics интеграция (custom counters/gauges)
- [ ] **MON-06**: Расширенный /health endpoint

### Testing & QA

- [ ] **TEST-01**: Playwright setup для админки
- [ ] **TEST-02**: Playwright тесты критических admin flows
- [ ] **TEST-03**: Playwright setup для бота (через браузер)
- [ ] **TEST-04**: Telethon setup для Telegram API тестирования
- [ ] **TEST-05**: Telethon тесты основных bot flows
- [ ] **TEST-06**: Исправление найденных багов админки
- [ ] **TEST-07**: Исправление найденных багов бота

### Admin Panel Improvements

- [ ] **ADMIN-01**: Улучшение UX админки после анализа Playwright findings
- [ ] **ADMIN-02**: Оптимизация загрузки dashboard (если медленно)
- [ ] **ADMIN-03**: Улучшение навигации между разделами

### Image Generation Process

- [ ] **IMG-01**: Исследование и выбор бесплатного AI генератора (Grok/Gemini/Leonardo/Playground/Ideogram)
- [ ] **IMG-02**: Разработка промптов для единого стиля всех изображений
- [ ] **IMG-03**: Генерация welcome screen изображения
- [ ] **IMG-04**: Генерация 12 изображений для знаков зодиака
- [ ] **IMG-05**: Генерация изображений для таро раскладов
- [ ] **IMG-06**: Генерация изображения для натальной карты
- [ ] **IMG-07**: Генерация изображения для paywall

## Future Requirements

Deferred to v2.1 or later.

### Retention & Engagement

- **RET-01**: Streak tracking (ежедневные заходы)
- **RET-02**: Gamification элементы
- **RET-03**: Персонализированные push уведомления
- **RET-04**: Реферальная программа

### New Astro Features

- **ASTRO-01**: Транзиты планет
- **ASTRO-02**: Прогрессии
- **ASTRO-03**: Синастрия (совместимость)
- **ASTRO-04**: Лунный календарь

## Out of Scope

Explicitly excluded from all versions. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Мобильное приложение (iOS/Android) | Фокус на Telegram боте |
| Живые тарологи и консультанты | Только AI, избегаем операционной сложности |
| Интеграция с соцсетями (Instagram, VK, Facebook) | Только Telegram |
| Групповые расклады или совместные консультации | Только личные |
| Обучающие курсы по астрологии/таро | Бот для прогнозов, не образовательный контент |
| Real-time streaming AI responses | Telegram rate limits, complexity |
| 78 custom tarot card images | Overkill, 5-7 spread images достаточно |
| Mini App для всего функционала | Telegram bot достаточен |
| Redis addon (v2.0) | PostgreSQL-backed cache достаточно для текущего масштаба |
| Sentry.io | Custom Prometheus metrics + PostgreSQL достаточно |

## Traceability

Which phases cover which requirements.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PERF-01 | Phase 11 | Complete |
| PERF-02 | Phase 12 | Pending |
| PERF-03 | Phase 12 | Pending |
| PERF-04 | Phase 11 | Complete |
| PERF-05 | Phase 14 | Pending |
| PERF-06 | Phase 12 | Pending |
| PERF-07 | Phase 12 | Pending |
| VIS-01 | Phase 14 | Pending |
| VIS-02 | Phase 14 | Pending |
| VIS-03 | Phase 14 | Pending |
| VIS-04 | Phase 14 | Pending |
| VIS-05 | Phase 14 | Pending |
| VIS-06 | Phase 14 | Pending |
| VIS-07 | Phase 14 | Pending |
| UX-01 | Phase 11 | Complete |
| UX-02 | Phase 11 | Complete |
| UX-03 | Phase 11 | Complete |
| UX-04 | Phase 11 | Complete |
| WEL-01 | Phase 11 | Complete |
| WEL-02 | Phase 11 | Complete |
| WEL-03 | Phase 14 | Pending |
| WEL-04 | Phase 11 | Complete |
| MON-01 | Phase 12 | Pending |
| MON-02 | Phase 15 | Pending |
| MON-03 | Phase 15 | Pending |
| MON-04 | Phase 15 | Pending |
| MON-05 | Phase 15 | Pending |
| MON-06 | Phase 15 | Pending |
| TEST-01 | Phase 16 | Pending |
| TEST-02 | Phase 16 | Pending |
| TEST-03 | Phase 16 | Pending |
| TEST-04 | Phase 16 | Pending |
| TEST-05 | Phase 16 | Pending |
| TEST-06 | Phase 16 | Pending |
| TEST-07 | Phase 16 | Pending |
| ADMIN-01 | Phase 16 | Pending |
| ADMIN-02 | Phase 16 | Pending |
| ADMIN-03 | Phase 16 | Pending |
| IMG-01 | Phase 13 | Pending |
| IMG-02 | Phase 13 | Pending |
| IMG-03 | Phase 13 | Pending |
| IMG-04 | Phase 13 | Pending |
| IMG-05 | Phase 13 | Pending |
| IMG-06 | Phase 13 | Pending |
| IMG-07 | Phase 13 | Pending |

**Coverage:**
- v2.0 requirements: 36 total
- Mapped to phases: 36/36 (100%)
- Unmapped: 0

---
*Requirements defined: 2026-01-23*
*Last updated: 2026-01-23 — traceability added*
