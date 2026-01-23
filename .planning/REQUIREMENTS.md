# Requirements: AdtroBot

**Defined:** 2026-01-22
**Core Value:** Качественная AI интерпретация астрологии и таро, которая конвертирует бесплатных пользователей в платных

## v1 Requirements

### Authentication & Onboarding

- [x] **AUTH-01**: Пользователь регистрируется автоматически при /start
- [x] **AUTH-02**: Система автоматически определяет знак зодиака по дате рождения
- [x] **AUTH-03**: Пользователь вводит дату рождения (для гороскопов и натальной карты)
- [x] **AUTH-04**: Пользователь вводит время и место рождения (для натальной карты)
- [x] **AUTH-05**: Пользователь получает immediate value (первый прогноз) сразу после регистрации
- [x] **AUTH-06**: Данные пользователя сохраняются в БД (знак, дата/время/место рождения)

### Horoscopes

- [x] **HORO-01**: Пользователь получает ежедневный гороскоп для своего знака зодиака (бесплатно)
- [x] **HORO-02**: Гороскоп доступен для всех 12 знаков зодиака
- [x] **HORO-03**: Гороскоп красиво отформатирован с emoji и разметкой
- [x] **HORO-04**: Платный пользователь получает детальный гороскоп по сферам (любовь, карьера, здоровье, финансы)
- [x] **HORO-05**: Платный пользователь получает персональный прогноз на основе натальной карты
- [x] **HORO-06**: Пользователь получает push-уведомление о новом ежедневном гороскопе

### Tarot

- [x] **TAROT-01**: Пользователь получает карту дня с AI предсказанием (1 раз в день, бесплатно)
- [x] **TAROT-02**: Бесплатный пользователь может сделать 1 расклад в день (3 карты: прошлое-настоящее-будущее)
- [x] **TAROT-03**: Пользователь задаёт вопрос перед раскладом
- [x] **TAROT-04**: Бот случайно выбирает карты из колоды (78 карт Райдер-Уэйт)
- [x] **TAROT-05**: Бот учитывает прямые и перевёрнутые карты
- [x] **TAROT-06**: Бот показывает изображения выбранных карт
- [x] **TAROT-07**: Бот даёт AI интерпретацию расклада на основе вопроса и карт
- [x] **TAROT-08**: Платный пользователь может делать 20 раскладов в день
- [x] **TAROT-09**: Платный пользователь может выбрать Кельтский крест (10 карт)
- [x] **TAROT-10**: Платный пользователь видит историю своих раскладов
- [x] **TAROT-11**: Система лимитов отслеживает количество раскладов с атомарными операциями

### Natal Chart

- [x] **NATAL-01**: Платный пользователь может запросить натальную карту
- [x] **NATAL-02**: Система рассчитывает позиции планет в домах и знаках (Swiss Ephemeris)
- [x] **NATAL-03**: Система корректно обрабатывает timezone для места рождения
- [x] **NATAL-04**: AI генерирует интерпретацию понятную новичкам
- [x] **NATAL-05**: Интерпретация включает позиции планет, дома, основные аспекты
- [x] **NATAL-06**: Интерпретация разбита по сферам жизни (личность, отношения, карьера, здоровье)

### AI Integration

- [x] **AI-01**: Система интегрирована с OpenRouter API
- [x] **AI-02**: Для генерации используется Claude 3.5 Sonnet (modified: GPT-4o-mini — 50x дешевле, та же качество)
- [x] **AI-03**: Промпты структурированы для каждого типа расклада/гороскопа
- [x] **AI-04**: AI персонализирует ответы на основе данных пользователя (знак, дата рождения)
- [x] **AI-05**: Система валидирует output от AI
- [x] **AI-06**: Система обрабатывает timeout с fallback механизмом
- [x] **AI-07**: AI интерпретация качественная (не generic копипаста)

### Payments & Subscriptions

- [x] **PAY-01**: Система интегрирована с ЮКасса SDK (официальная библиотека)
- [x] **PAY-02**: Пользователь может оформить месячную подписку
- [x] **PAY-03**: Подписка автоматически продлевается каждый месяц
- [x] **PAY-04**: Пользователь может отменить подписку
- [x] **PAY-05**: Webhook от ЮКасса обрабатывается idempotent (HTTP 200 немедленно)
- [x] **PAY-06**: Webhook обновляет статус подписки в БД (активна/истекла/отменена)
- [x] **PAY-07**: Система отслеживает лимиты пользователя (бесплатный/платный)
- [x] **PAY-08**: Лимиты проверяются атомарными операциями в БД (защита от race conditions)
- [x] **PAY-09**: Пользователь видит оставшиеся лимиты (расклады таро)
- [x] **PAY-10**: Пользователь получает уведомление об истечении подписки

### Bot UX & Navigation

- [x] **BOT-01**: Бот показывает главное меню с кнопками навигации
- [x] **BOT-02**: Пользователь может выбрать действие через inline кнопки
- [x] **BOT-03**: Бот обрабатывает команды (/start, /help, /horoscope, /tarot, /natal, /subscribe)
- [x] **BOT-04**: Бот использует Finite State Machine для диалогов (aiogram FSM)
- [x] **BOT-05**: Все ответы красиво отформатированы (emoji, markdown, структура)
- [x] **BOT-06**: Бот работает через webhook (не polling) для Railway
- [x] **BOT-07**: Бот обрабатывает ошибки gracefully (понятные сообщения пользователю)

### Admin Panel

- [ ] **ADMIN-01**: Админ панель доступна через веб интерфейс
- [ ] **ADMIN-02**: Админ видит статистику пользователей (общее количество, активные, платные)
- [ ] **ADMIN-03**: Админ видит конверсию free → paid
- [ ] **ADMIN-04**: Админ видит воронку продаж (регистрация → использование → оплата) с визуализацией
- [ ] **ADMIN-05**: Админ видит список всех подписок (активные, истекшие, отменённые)
- [ ] **ADMIN-06**: Админ может изменить статус подписки вручную
- [ ] **ADMIN-07**: Админ видит историю платежей
- [ ] **ADMIN-08**: Админ может редактировать тексты гороскопов
- [ ] **ADMIN-09**: Админ может читать сообщения пользователей в таро (вопросы)
- [ ] **ADMIN-10**: Админ может отправить сообщение конкретному пользователю
- [ ] **ADMIN-11**: Админ может выдать бесплатные прогнозы/бонусы пользователю
- [ ] **ADMIN-12**: Админ видит retention метрики (возвращаемость пользователей)
- [ ] **ADMIN-13**: Админ может экспортировать данные для анализа

### Infrastructure

- [x] **INFRA-01**: Backend развёрнут на Railway
- [x] **INFRA-02**: PostgreSQL база данных настроена (Railway addon)
- [ ] **INFRA-03**: Один FastAPI сервер обслуживает Telegram webhook, ЮКасса webhook и админку
- [x] **INFRA-04**: Весь код асинхронный (aiogram 3.x + SQLAlchemy async + asyncpg)
- [x] **INFRA-05**: База данных использует миграции (Alembic)
- [x] **INFRA-06**: Переменные окружения настроены (токены, API ключи)
- [x] **INFRA-07**: Логирование настроено для мониторинга
- [x] **INFRA-08**: CI/CD настроен для автоматического деплоя на Railway (GitHub Actions)

## v2 Requirements

Отложены на будущее (после валидации v1):

### Extended Features
- **EXT-01**: Недельный/месячный гороскоп
- **EXT-02**: Совместимость знаков зодиака
- **EXT-03**: Транзиты планет
- **EXT-04**: Прогрессии
- **EXT-05**: Больше видов раскладов таро (5-7 типов)
- **EXT-06**: Telegram Stars как альтернатива ЮКасса
- **EXT-07**: Реферальная программа

## Out of Scope

Явно исключено, чтобы избежать scope creep:

| Feature | Reason |
|---------|--------|
| Мобильное приложение (iOS/Android) | Только Telegram бот — проще поддерживать и быстрее запускать |
| Живые тарологи/астрологи | Операционная сложность, фокус на AI качестве |
| Групповые расклады | Усложнение без очевидной ценности |
| Соцсети (Instagram, VK, Facebook) | Фокус на одной платформе (Telegram) |
| Обучающие курсы | Бот для прогнозов, не образовательная платформа |
| Геймификация с лидербордами | Отвлекает от core value |
| Чат между пользователями | Превращает бот в соцсеть |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 2 | Complete |
| AUTH-02 | Phase 2 | Complete |
| AUTH-03 | Phase 2 | Complete |
| AUTH-04 | Phase 7 | Complete |
| AUTH-05 | Phase 2 | Complete |
| AUTH-06 | Phase 2 | Complete |
| HORO-01 | Phase 3 | Pending |
| HORO-02 | Phase 3 | Pending |
| HORO-03 | Phase 3 | Pending |
| HORO-04 | Phase 7 | Complete |
| HORO-05 | Phase 7 | Complete |
| HORO-06 | Phase 3 | Pending |
| TAROT-01 | Phase 4 | Pending |
| TAROT-02 | Phase 4 | Pending |
| TAROT-03 | Phase 4 | Pending |
| TAROT-04 | Phase 4 | Pending |
| TAROT-05 | Phase 4 | Pending |
| TAROT-06 | Phase 4 | Pending |
| TAROT-07 | Phase 5 | Pending |
| TAROT-08 | Phase 8 | Complete |
| TAROT-09 | Phase 8 | Complete |
| TAROT-10 | Phase 8 | Complete |
| TAROT-11 | Phase 4 | Pending |
| NATAL-01 | Phase 8 | Complete |
| NATAL-02 | Phase 8 | Complete |
| NATAL-03 | Phase 8 | Complete |
| NATAL-04 | Phase 8 | Complete |
| NATAL-05 | Phase 8 | Complete |
| NATAL-06 | Phase 8 | Complete |
| AI-01 | Phase 5 | Pending |
| AI-02 | Phase 5 | Pending |
| AI-03 | Phase 5 | Pending |
| AI-04 | Phase 5 | Pending |
| AI-05 | Phase 5 | Pending |
| AI-06 | Phase 5 | Pending |
| AI-07 | Phase 5 | Pending |
| PAY-01 | Phase 6 | Complete |
| PAY-02 | Phase 6 | Complete |
| PAY-03 | Phase 6 | Complete |
| PAY-04 | Phase 6 | Complete |
| PAY-05 | Phase 6 | Complete |
| PAY-06 | Phase 6 | Complete |
| PAY-07 | Phase 6 | Complete |
| PAY-08 | Phase 6 | Complete |
| PAY-09 | Phase 6 | Complete |
| PAY-10 | Phase 6 | Complete |
| BOT-01 | Phase 2 | Complete |
| BOT-02 | Phase 2 | Complete |
| BOT-03 | Phase 2 | Complete |
| BOT-04 | Phase 2 | Complete |
| BOT-05 | Phase 6 | Complete |
| BOT-06 | Phase 2 | Complete |
| BOT-07 | Phase 2 | Complete |
| ADMIN-01 | Phase 9 | Pending |
| ADMIN-02 | Phase 9 | Pending |
| ADMIN-03 | Phase 9 | Pending |
| ADMIN-04 | Phase 9 | Pending |
| ADMIN-05 | Phase 9 | Pending |
| ADMIN-06 | Phase 9 | Pending |
| ADMIN-07 | Phase 9 | Pending |
| ADMIN-08 | Phase 9 | Pending |
| ADMIN-09 | Phase 9 | Pending |
| ADMIN-10 | Phase 9 | Pending |
| ADMIN-11 | Phase 9 | Pending |
| ADMIN-12 | Phase 9 | Pending |
| ADMIN-13 | Phase 9 | Pending |
| INFRA-01 | Phase 1 | Complete |
| INFRA-02 | Phase 1 | Complete |
| INFRA-03 | Phase 2 | Complete |
| INFRA-04 | Phase 1 | Complete |
| INFRA-05 | Phase 1 | Complete |
| INFRA-06 | Phase 1 | Complete |
| INFRA-07 | Phase 1 | Complete |
| INFRA-08 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 74 total
- Mapped to phases: 74
- Unmapped: 0

---
*Requirements defined: 2026-01-22*
*Last updated: 2026-01-22 after roadmap creation*
