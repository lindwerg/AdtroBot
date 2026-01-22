# Roadmap: AdtroBot

## Overview

Telegram бот для гороскопов и таро с freemium моделью. Путь от инфраструктуры через бесплатный функционал (гороскопы, таро) к AI интерпретациям, затем платежи и premium функции. Админка в конце — когда есть что администрировать. Каждая фаза доставляет работающую ценность: пользователь может использовать бот после каждой фазы начиная с Phase 2.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Infrastructure** - PostgreSQL, SQLAlchemy async, Railway deployment foundation
- [ ] **Phase 2: Bot Core + Onboarding** - Telegram webhook, /start, регистрация, дата рождения
- [ ] **Phase 3: Free Horoscopes** - Ежедневный гороскоп для всех знаков, уведомления
- [ ] **Phase 4: Free Tarot** - Карта дня, расклад 3 карты, колода Райдер-Уэйт
- [ ] **Phase 5: AI Integration** - OpenRouter, Claude 3.5 Sonnet, AI интерпретации
- [ ] **Phase 6: Payments** - ЮКасса интеграция, подписки, webhook обработка
- [ ] **Phase 7: Premium Horoscopes** - Детальные гороскопы по сферам, персональный прогноз
- [ ] **Phase 8: Premium Tarot + Natal** - Кельтский крест, натальная карта, история раскладов
- [ ] **Phase 9: Admin Panel** - Статистика, управление подписками, аналитика

## Phase Details

### Phase 1: Infrastructure
**Goal**: Фундамент готов — БД работает, миграции настроены, деплой на Railway автоматизирован
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-04, INFRA-05, INFRA-06, INFRA-07, INFRA-08
**Success Criteria** (what must be TRUE):
  1. PostgreSQL база данных доступна и принимает подключения на Railway
  2. Alembic миграции применяются автоматически при деплое
  3. GitHub push в main автоматически деплоит на Railway
  4. Логи доступны в Railway dashboard для мониторинга
  5. Environment variables (токены, API ключи) настроены безопасно
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Database setup + models (Poetry, SQLAlchemy async, Alembic, User model)
- [x] 01-02-PLAN.md — CI/CD + Railway deployment (GitHub Actions, Procfile, Railway config)

### Phase 2: Bot Core + Onboarding
**Goal**: Пользователь может запустить бота, зарегистрироваться и получить immediate value
**Depends on**: Phase 1
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-05, AUTH-06, BOT-01, BOT-02, BOT-03, BOT-04, BOT-06, BOT-07, INFRA-03
**Success Criteria** (what must be TRUE):
  1. Пользователь нажимает /start и видит приветствие с меню
  2. Бот запрашивает дату рождения и определяет знак зодиака
  3. Пользователь получает первый прогноз сразу после регистрации
  4. Данные пользователя сохраняются в БД (telegram_id, знак, дата рождения)
  5. Бот корректно обрабатывает ошибки и показывает понятные сообщения
**Plans**: TBD

Plans:
- [ ] 02-01: Telegram webhook + FastAPI
- [ ] 02-02: Onboarding flow + FSM

### Phase 3: Free Horoscopes
**Goal**: Пользователь получает ежедневный гороскоп для своего знака зодиака
**Depends on**: Phase 2
**Requirements**: HORO-01, HORO-02, HORO-03, HORO-06
**Success Criteria** (what must be TRUE):
  1. Пользователь нажимает кнопку "Гороскоп" и видит прогноз для своего знака
  2. Гороскоп красиво отформатирован с emoji и разметкой
  3. Пользователь может посмотреть гороскоп для любого из 12 знаков
  4. Пользователь получает push-уведомление о новом ежедневном гороскопе
**Plans**: TBD

Plans:
- [ ] 03-01: Horoscope service + handlers

### Phase 4: Free Tarot
**Goal**: Пользователь может вытянуть карту дня и сделать расклад на 3 карты
**Depends on**: Phase 2
**Requirements**: TAROT-01, TAROT-02, TAROT-03, TAROT-04, TAROT-05, TAROT-06, TAROT-11
**Success Criteria** (what must be TRUE):
  1. Пользователь получает карту дня с предсказанием (1 раз в день)
  2. Пользователь задаёт вопрос и получает расклад на 3 карты
  3. Бот показывает изображения карт (прямые и перевёрнутые)
  4. Бесплатный пользователь ограничен 1 раскладом в день
  5. Пользователь видит сколько раскладов осталось на сегодня
**Plans**: TBD

Plans:
- [ ] 04-01: Tarot deck + card logic
- [ ] 04-02: Tarot handlers + limits

### Phase 5: AI Integration
**Goal**: AI генерирует качественные персонализированные интерпретации
**Depends on**: Phase 3, Phase 4
**Requirements**: AI-01, AI-02, AI-03, AI-04, AI-05, AI-06, AI-07, TAROT-07
**Success Criteria** (what must be TRUE):
  1. Гороскопы генерируются AI и не выглядят как generic копипаста
  2. Расклады таро интерпретируются AI на основе вопроса и выбранных карт
  3. AI персонализирует ответы (упоминает знак зодиака, конкретные карты)
  4. При timeout AI система использует fallback (cached ответ или альтернативная модель)
  5. Output от AI валидируется перед отправкой пользователю
**Plans**: TBD

Plans:
- [ ] 05-01: OpenRouter integration + prompts
- [ ] 05-02: AI service + fallbacks

### Phase 6: Payments
**Goal**: Пользователь может оформить и управлять платной подпиской
**Depends on**: Phase 5
**Requirements**: PAY-01, PAY-02, PAY-03, PAY-04, PAY-05, PAY-06, PAY-07, PAY-08, PAY-09, PAY-10, BOT-05
**Success Criteria** (what must be TRUE):
  1. Пользователь нажимает "Подписаться" и переходит к оплате через ЮКасса
  2. После успешной оплаты подписка активируется автоматически
  3. Подписка автоматически продлевается каждый месяц
  4. Пользователь может отменить подписку через бота
  5. Пользователь получает уведомление об истечении подписки
**Plans**: TBD

Plans:
- [ ] 06-01: YooKassa SDK integration
- [ ] 06-02: Subscription handlers + webhook

### Phase 7: Premium Horoscopes
**Goal**: Платный пользователь получает детальные гороскопы по сферам жизни
**Depends on**: Phase 6
**Requirements**: HORO-04, HORO-05, AUTH-04
**Success Criteria** (what must be TRUE):
  1. Платный пользователь видит гороскоп разбитый по сферам (любовь, карьера, здоровье, финансы)
  2. Платный пользователь может ввести время и место рождения для персонализации
  3. Платный пользователь получает персональный прогноз на основе своих данных
  4. Бесплатный пользователь видит teaser premium контента
**Plans**: TBD

Plans:
- [ ] 07-01: Premium horoscope features

### Phase 8: Premium Tarot + Natal
**Goal**: Платный пользователь получает расширенные расклады таро и натальную карту
**Depends on**: Phase 6
**Requirements**: TAROT-08, TAROT-09, TAROT-10, NATAL-01, NATAL-02, NATAL-03, NATAL-04, NATAL-05, NATAL-06
**Success Criteria** (what must be TRUE):
  1. Платный пользователь может делать 20 раскладов в день
  2. Платный пользователь может выбрать Кельтский крест (10 карт)
  3. Платный пользователь видит историю своих раскладов
  4. Платный пользователь может запросить натальную карту
  5. Натальная карта включает позиции планет, дома, аспекты с AI интерпретацией
**Plans**: TBD

Plans:
- [ ] 08-01: Celtic cross + reading history
- [ ] 08-02: Natal chart calculation + interpretation

### Phase 9: Admin Panel
**Goal**: Админ может управлять ботом и видеть аналитику
**Depends on**: Phase 6
**Requirements**: ADMIN-01, ADMIN-02, ADMIN-03, ADMIN-04, ADMIN-05, ADMIN-06, ADMIN-07, ADMIN-08, ADMIN-09, ADMIN-10, ADMIN-11, ADMIN-12, ADMIN-13
**Success Criteria** (what must be TRUE):
  1. Админ заходит в веб-интерфейс и видит dashboard со статистикой
  2. Админ видит воронку продаж и конверсию free-to-paid
  3. Админ может найти пользователя и изменить его подписку
  4. Админ может отправить сообщение конкретному пользователю
  5. Админ может экспортировать данные для анализа
**Plans**: TBD

Plans:
- [ ] 09-01: Admin dashboard + user management
- [ ] 09-02: Analytics + messaging

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Infrastructure | 1/2 | In progress | - |
| 2. Bot Core + Onboarding | 0/2 | Not started | - |
| 3. Free Horoscopes | 0/1 | Not started | - |
| 4. Free Tarot | 0/2 | Not started | - |
| 5. AI Integration | 0/2 | Not started | - |
| 6. Payments | 0/2 | Not started | - |
| 7. Premium Horoscopes | 0/1 | Not started | - |
| 8. Premium Tarot + Natal | 0/2 | Not started | - |
| 9. Admin Panel | 0/2 | Not started | - |

---
*Roadmap created: 2026-01-22*
*Total v1 requirements: 74*
*All requirements mapped: YES*
