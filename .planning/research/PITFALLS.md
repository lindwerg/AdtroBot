# Pitfalls Research

**Domain:** Telegram астро-бот с freemium подписками, AI интерпретациями, ЮКасса платежами
**Researched:** 2026-01-22
**Confidence:** HIGH (основано на официальной документации и опыте сообщества)

## Critical Pitfalls

### Pitfall 1: Webhook ЮКасса не подтверждён вовремя — потеря платежей

**What goes wrong:**
ЮКасса отправляет webhook о успешном платеже, но сервер не отвечает HTTP 200 за 10 секунд. ЮКасса повторяет запрос, возникает дублирование обработки или пропуск платежа.

**Why it happens:**
- Синхронная обработка webhook внутри HTTP handler
- База данных медленная или недоступна
- AI запрос блокирует поток обработки

**How to avoid:**
1. **Немедленный ответ 200** — сразу отвечать, обрабатывать в фоне
2. **Идемпотентность** — сохранять `payment_id` и проверять дубликаты
3. **Очередь задач** — webhook кладёт в очередь, воркер обрабатывает
4. **Логирование** — записывать все входящие webhooks с timestamp

```python
# Правильный паттерн
async def webhook_handler(request):
    data = await request.json()
    await queue.enqueue(data)  # В очередь
    return web.Response(status=200)  # Мгновенный ответ
```

**Warning signs:**
- Пользователи жалуются "оплатил, но подписка не активирована"
- В логах ЮКасса повторные попытки доставки webhook
- Несоответствие количества платежей в ЮКасса и в БД

**Phase to address:**
Phase 1 (платежи) — архитектура webhook обработки с первого дня

---

### Pitfall 2: Race conditions в системе лимитов — бесплатный доступ к платному

**What goes wrong:**
Пользователь быстро нажимает кнопку несколько раз, система проверяет лимит (лимит=0), но до декремента успевает выполнить действие. Результат: бесплатные пользователи получают больше раскладов, чем положено.

**Why it happens:**
- Check-then-act без атомарности: `if limits > 0: do_action(); limits -= 1`
- Concurrent requests от одного user_id
- Aiogram handlers выполняются параллельно

**How to avoid:**
1. **Атомарные операции в БД:**
```sql
UPDATE user_limits
SET tarot_today = tarot_today - 1
WHERE user_id = $1 AND tarot_today > 0
RETURNING tarot_today;
```
2. **Redis с DECR** — если > 0, разрешить действие
3. **Mutex per user_id** — блокировка на уровне пользователя
4. **Rate limiting на входе** — aiogram ratelimiter плагин

**Warning signs:**
- Пользователи с нулевыми лимитами имеют расклады за сегодня
- Метрики показывают > 1 расклад/день у free users
- Жалобы "почему мне дало 3 расклада, а теперь ни одного?"

**Phase to address:**
Phase 1 — система лимитов должна быть атомарной с первой версии

---

### Pitfall 3: AI генерирует бред или неточности — потеря доверия

**What goes wrong:**
OpenRouter возвращает generic текст ("звёзды говорят о хороших переменах") или фактические ошибки (неправильные позиции планет, перепутанные карты таро). Пользователи понимают, что бот "туповат" и уходят.

**Why it happens:**
- Плохой промпт без структуры и контекста
- Нет валидации выходных данных AI
- Модель не знает конкретную колоду таро или астрологическую систему
- Слишком низкая температура = generic, слишком высокая = бред

**How to avoid:**
1. **Структурированные промпты** с JSON schema для ответа
2. **Few-shot примеры** качественных интерпретаций
3. **Валидация** — проверять упоминания конкретных карт/планет
4. **Human review** первых 100 генераций перед запуском
5. **A/B тестирование** разных моделей и промптов
6. **Fallback** — если AI не сработал, cached generic + retry

```python
# Структурированный промпт
prompt = f"""
Интерпретируй расклад таро:
- Позиция "Прошлое": {card1.name} {'перевёрнутая' if card1.reversed else ''}
- Позиция "Настоящее": {card2.name}
- Позиция "Будущее": {card3.name}

Вопрос пользователя: {user_question}

ОБЯЗАТЕЛЬНО упомяни каждую карту по имени.
ОБЯЗАТЕЛЬНО свяжи карты между собой.
НЕ используй общие фразы типа "всё будет хорошо".
"""
```

**Warning signs:**
- Ответы AI не упоминают конкретные карты из расклада
- Пользователи пишут "это не про мой вопрос"
- Retention падает после первого использования AI

**Phase to address:**
Phase 2 (AI core) — quality gate перед production

---

### Pitfall 4: Подписка истекла, но доступ остался — потеря дохода

**What goes wrong:**
Webhook об отмене/истечении подписки не обработан или обработан с ошибкой. Пользователь продолжает пользоваться premium функциями бесплатно.

**Why it happens:**
- Webhook пришёл, но сервер был недоступен
- Статус подписки проверяется по кэшу, а не по БД
- Нет проверки `subscription_end_date` при каждом запросе
- Отменённая подписка в ЮКасса не синхронизирована с ботом

**How to avoid:**
1. **Проверка на каждый запрос** — не кэшировать статус подписки надолго
2. **Polling fallback** — раз в час проверять статус подписок в ЮКасса API
3. **subscription_end_date** — хранить и проверять `now() < end_date`
4. **Webhook retry queue** — если обработка failed, повторить

```python
async def check_premium(user_id: int) -> bool:
    sub = await db.get_subscription(user_id)
    if not sub:
        return False
    if sub.status != 'active':
        return False
    if sub.end_date < datetime.now():
        await db.deactivate_subscription(user_id)
        return False
    return True
```

**Warning signs:**
- Количество active subscriptions в БД > чем в ЮКасса
- Пользователи с `status=cancelled` используют premium
- Revenue не растёт при росте "платных" пользователей

**Phase to address:**
Phase 1 (платежи) — статус подписки = source of truth в ЮКасса

---

### Pitfall 5: Ошибки расчёта натальной карты — репутационный ущерб

**What goes wrong:**
Позиции планет рассчитаны неправильно из-за ошибок с часовыми поясами, отсутствия ephemeris файлов, или неправильной обработки координат. Опытные астрологи сразу видят ошибки и уходят.

**Why it happens:**
- Swiss Ephemeris без data files даёт точность только 0.1" (вместо 0.001")
- Timezone conversion ошибки (UTC vs local, DST)
- Координаты города неточные или отсутствуют
- Тропическая vs сидерическая система не указана

**How to avoid:**
1. **Swiss Ephemeris data files** — обязательно включить в deployment
2. **Timezone database** — pytz/zoneinfo с актуальной базой
3. **Geocoding API** — проверенный источник координат (Google/OpenStreetMap)
4. **Тестирование** — сравнить результаты с astro.com для 10+ дат
5. **Указывать систему** — явно писать "тропическая система"

```python
import swissephemeris as swe

# ОБЯЗАТЕЛЬНО указать путь к ephemeris
swe.set_ephe_path('/app/ephe')

# ОБЯЗАТЕЛЬНО конвертировать в UTC
birth_utc = convert_to_utc(birth_local, timezone)
```

**Warning signs:**
- Позиция Солнца не совпадает со знаком зодиака пользователя
- Опытные пользователи жалуются на неточности
- Сравнение с astro.com показывает расхождения > 1°

**Phase to address:**
Phase 3 (натальная карта) — верификация перед запуском

---

### Pitfall 6: OpenRouter timeout/failure — бот "завис"

**What goes wrong:**
OpenRouter отвечает медленно (10+ секунд) или не отвечает. Пользователь нажал кнопку и ждёт. Telegram показывает "typing..." бесконечно. Пользователь уходит.

**Why it happens:**
- Нет timeout на API запросы
- Нет fallback при ошибке
- Нет индикации прогресса для пользователя
- Выбрана медленная или перегруженная модель

**How to avoid:**
1. **Timeout 30 секунд** — максимум для AI запроса
2. **Fallback модель** — если GPT-4 недоступен, использовать Claude
3. **Индикация** — "Анализирую ваш расклад... (обычно 10-15 секунд)"
4. **Cached responses** — для повторяющихся запросов
5. **Retry с exponential backoff** — 1s, 2s, 4s

```python
async def generate_interpretation(prompt: str) -> str:
    try:
        async with asyncio.timeout(30):
            return await openrouter.generate(prompt, model="gpt-4o")
    except asyncio.TimeoutError:
        # Fallback
        return await openrouter.generate(prompt, model="claude-3-haiku")
    except Exception:
        return get_cached_generic_response()
```

**Warning signs:**
- Время ответа бота > 15 секунд
- Пользователи повторно нажимают кнопки
- Много незавершённых сессий в аналитике

**Phase to address:**
Phase 2 (AI) — resilience с первой интеграции

---

### Pitfall 7: Пользователь не понимает ценность — низкая конверсия

**What goes wrong:**
Бесплатные пользователи не понимают, зачем платить. Paywall слишком агрессивный ("купи чтобы увидеть") или слишком мягкий (всё и так доступно). Конверсия free→paid < 1%.

**Why it happens:**
- Ценность premium не очевидна из free опыта
- Нет "taste" premium функций
- Paywall появляется слишком рано (до value delivery)
- Или слишком поздно (пользователь уже получил всё бесплатно)

**How to avoid:**
1. **Value first** — дать качественный бесплатный опыт, потом предлагать платный
2. **Teaser** — показать часть premium (первый абзац натальной карты)
3. **Timing** — paywall после 3-5 успешных бесплатных использований
4. **Чёткое сравнение** — таблица Free vs Premium
5. **Urgency без pressure** — "осталось 2 расклада сегодня"

**Warning signs:**
- Конверсия < 2%
- Пользователи отваливаются сразу после первого paywall
- Feedback "непонятно за что платить"

**Phase to address:**
Phase 4 (monetization) — A/B тестирование paywall

---

### Pitfall 8: Railway deployment issues — бот периодически падает

**What goes wrong:**
Бот работает локально, но на Railway падает: connection pool exhausted, memory leaks, shared memory errors с Postgres, sealed variables не работают в dev.

**Why it happens:**
- Не настроен connection pooling для Postgres
- Memory leaks в long-running process
- Shared memory для Postgres не увеличен
- Environment variables разные в dev/prod
- Railway free tier limitations

**How to avoid:**
1. **Connection pooling** — asyncpg с pool_size=10-20
2. **Health checks** — endpoint /health для Railway
3. **Memory monitoring** — отслеживать утечки
4. **SHM для Postgres:** `RAILWAY_SHM_SIZE_BYTES=524288000` (500MB)
5. **Sealed variables** — использовать только для prod secrets

```python
# Правильный connection pool
pool = await asyncpg.create_pool(
    DATABASE_URL,
    min_size=5,
    max_size=20,
    command_timeout=60
)
```

**Warning signs:**
- "Connection pool is full" в логах
- Бот перезапускается каждые N часов
- Memory usage растёт линейно со временем

**Phase to address:**
Phase 1 — infrastructure setup с правильными defaults

---

### Pitfall 9: Пользователь ушёл после первого сообщения — нет retention

**What goes wrong:**
Пользователь запустил бота, получил generic приветствие, не понял что делать, ушёл. DAU/MAU < 5%.

**Why it happens:**
- Onboarding не ведёт к первому "wow moment"
- Слишком много текста, мало действий
- Нет clear next step (кнопки, не команды)
- Первый опыт занимает слишком долго

**How to avoid:**
1. **Immediate value** — карта дня сразу после /start
2. **Buttons, not commands** — визуальные действия
3. **Progressive disclosure** — сначала простое, потом сложное
4. **Daily hook** — напоминание о новой карте дня
5. **Персонализация** — спросить знак зодиака, сразу использовать

```
/start flow:
1. "Привет! Давай узнаем твою карту дня?" [Да!]
2. *Показать карту дня с интерпретацией*
3. "Понравилось? Теперь выбери:" [Гороскоп] [Таро расклад]
```

**Warning signs:**
- > 50% пользователей не делают ни одного действия после /start
- Retention Day 1 < 20%
- Среднее количество сообщений на пользователя < 3

**Phase to address:**
Phase 2 — UX flow с первой версии бота

---

### Pitfall 10: Abuse через multiple accounts — drain лимитов

**What goes wrong:**
Один человек создаёт много Telegram аккаунтов и получает бесплатные расклады каждый день с каждого. AI costs растут, платных пользователей нет.

**Why it happens:**
- Нет device fingerprinting
- Telegram позволяет легко создавать аккаунты
- Виртуальные номера дешёвые
- IP-based rate limiting не работает (VPN, mobile)

**How to avoid:**
1. **Мониторинг аномалий** — много аккаунтов с похожим поведением
2. **Phone number age** — Telegram Premium API показывает возраст аккаунта
3. **Usage patterns** — подозрительно одинаковые вопросы/время
4. **Device ID** — если возможно через web app
5. **Принять как cost of business** — заложить в unit economics

**Warning signs:**
- Много новых аккаунтов в один день
- Одинаковые вопросы от разных user_id
- AI costs растут быстрее чем user base

**Phase to address:**
Phase 4 — мониторинг и anti-fraud после запуска

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Хранить session в памяти | Быстрая разработка | Потеря данных при restart | Никогда для платежей |
| Hardcoded prompts | Быстрый запуск | Невозможно тестировать/менять | MVP, рефакторить в Phase 2 |
| Синхронные DB запросы | Проще код | Блокировка при нагрузке | Никогда |
| Без connection pooling | Работает локально | Падает под нагрузкой | Никогда для production |
| Один monolith handler | Быстрее написать | Сложно тестировать | MVP, рефакторить до платежей |
| Без retry logic для AI | Меньше кода | Частые failures | Никогда |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| ЮКасса webhook | Синхронная обработка в handler | Async queue + немедленный 200 OK |
| ЮКасса recurring | Не сохранять payment_method_id | Сохранять для auto-renewal |
| OpenRouter | Один model без fallback | Primary + fallback model |
| Swiss Ephemeris | Не включать ephemeris files | Включить в Docker image |
| Telegram Bot API | Не обрабатывать 429 Too Many Requests | Exponential backoff + queue |
| Railway Postgres | Использовать default SHM | Увеличить RAILWAY_SHM_SIZE_BYTES |
| Geocoding API | Доверять первому результату | Уточнять город + timezone |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| AI на каждый запрос | Медленные ответы, высокие costs | Кэшировать гороскопы, batch генерация | > 100 users/day |
| Нет индекса на user_id | Медленные запросы лимитов | Index на все lookup поля | > 1000 users |
| N+1 queries | Долгая загрузка истории | JOINs или batch loading | > 100 раскладов на user |
| Нет pagination | Timeout при большой истории | LIMIT + offset | > 50 items |
| Синхронная генерация изображений | Блокировка других users | Background task + notify | > 10 concurrent |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Webhook без верификации подписи | Fake payments, fraud | Проверять IP или signature ЮКасса |
| API keys в коде | Утечка credentials | Environment variables only |
| Нет rate limit на входе | DDoS, resource drain | aiogram ratelimiter plugin |
| User input в SQL | SQL injection | Parameterized queries always |
| User input в prompt | Prompt injection | Sanitize + structured prompts |
| Логирование payment data | PCI compliance issues | Маскировать sensitive data |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Длинные текстовые меню | Confusion, drop-off | Inline buttons с иконками |
| Paywall без preview | "За что платить?" | Показать teaser контента |
| Нет confirmation на оплату | Случайные покупки, refunds | "Подтвердите оплату 299р" |
| Одинаковые daily гороскопы | "Это копипаста" | Генерировать уникальные |
| Нет прогресс-индикатора | "Бот завис?" | "Анализирую... 10 сек" |
| Error messages на английском | Alienation | Русские user-friendly сообщения |

## "Looks Done But Isn't" Checklist

- [ ] **Платежи:** Обработка отмен подписки — verify webhook `payment.canceled` handling
- [ ] **Платежи:** Истечение подписки — verify cron job / scheduled check
- [ ] **AI:** Fallback при timeout — verify backup model или cached response
- [ ] **AI:** Валидация output — verify карты/планеты упоминаются в ответе
- [ ] **Лимиты:** Атомарность — verify concurrent requests не bypass лимит
- [ ] **Натальная карта:** Ephemeris files — verify deployment includes data files
- [ ] **Натальная карта:** Timezone handling — verify birth time converted to UTC
- [ ] **Onboarding:** First message UX — verify user can act without reading instructions
- [ ] **Retention:** Daily notifications — verify scheduled messages work
- [ ] **Admin:** Revenue metrics — verify данные совпадают с ЮКасса dashboard

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Пропущенные webhooks | MEDIUM | Polling ЮКасса API, reconciliation script |
| Race conditions в лимитах | LOW | Database migration + code fix, данные не потеряны |
| Плохое AI качество | MEDIUM | Итерация промптов, A/B тест, 1-2 недели |
| Неточные натальные карты | HIGH | Полный rewrite расчётов, потеря доверия |
| Memory leaks | LOW | Restart + fix, мониторинг |
| Низкая конверсия | MEDIUM | UX iteration, paywall A/B тесты |
| Fraud/abuse | LOW-MEDIUM | Rate limiting, блокировка, принять как cost |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Webhook не подтверждён | Phase 1 (Payments) | Load test webhook endpoint |
| Race conditions лимитов | Phase 1 (Core) | Concurrent requests test |
| AI quality | Phase 2 (AI) | Human review 100 samples |
| Подписка не деактивирована | Phase 1 (Payments) | Webhook cancellation test |
| Ошибки натальной карты | Phase 3 (Natal) | Compare with astro.com |
| OpenRouter timeout | Phase 2 (AI) | Chaos testing / mock failures |
| Низкая конверсия | Phase 4 (Monetization) | A/B testing framework |
| Railway issues | Phase 1 (Infra) | Staging environment tests |
| Плохой retention | Phase 2 (Bot UX) | Day 1/7/30 cohort analysis |
| Account abuse | Phase 4 (Post-launch) | Anomaly detection monitoring |

## Sources

**Платежи и ЮКасса:**
- [YooKassa Webhooks Documentation](https://yookassa.ru/developers/using-api/webhooks)
- [YooKassa API Reference](https://yookassa.ru/developers/api)
- [Telegram Bot Payments API](https://core.telegram.org/bots/payments)

**Telegram Bot Development:**
- [Telegram Bot API Rate Limits](https://core.telegram.org/bots/faq)
- [python-telegram-bot Avoiding Flood Limits](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Avoiding-flood-limits)
- [grammY Deployment Types](https://grammy.dev/guide/deployment-types.html)
- [aiogram GitHub](https://github.com/aiogram/aiogram)

**AI и OpenRouter:**
- [OpenRouter Error Handling](https://openrouter.ai/docs/api/reference/errors-and-debugging)
- [LLM Router Strategies](https://www.vellum.ai/blog/what-to-do-when-an-llm-request-fails)
- [AI Astrology Accuracy Analysis](https://www.allaboutai.com/resources/ai-astrology-predictions/)

**Астрологические расчёты:**
- [Swiss Ephemeris Documentation](https://www.astro.com/swisseph/swisseph.htm)
- [pyswisseph](https://github.com/astrorigin/pyswisseph)
- [immanuel-python](https://github.com/theriftlab/immanuel-python)

**Retention и конверсия:**
- [SaaS Churn Benchmarks 2025](https://www.venasolutions.com/blog/saas-churn-rate)
- [Freemium Conversion Rate Guide](https://userpilot.com/blog/freemium-conversion-rate/)
- [Consumer Subscription KPI Benchmarks](https://medium.com/parsa-vc/consumer-subscription-kpi-benchmarks-retention-engagement-and-conversion-rates-9ac13b57c3d3)

**Railway Deployment:**
- [Railway Variables Documentation](https://docs.railway.com/guides/variables)
- [Railway PostgreSQL Guide](https://docs.railway.com/guides/postgresql)

---
*Pitfalls research for: Telegram астро-бот с freemium моделью*
*Researched: 2026-01-22*
