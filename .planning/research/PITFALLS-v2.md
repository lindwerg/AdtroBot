# Pitfalls Research: v2.0 Enhancements

**Domain:** Добавление визуалов, кэширования, background jobs, мониторинга в существующий Telegram бот
**Researched:** 2026-01-23
**Confidence:** HIGH (основано на официальной документации aiogram, APScheduler, Telegram Bot API, опыте сообщества)

---

## Critical Pitfalls

### Pitfall 1: In-Memory Cache Lost on Railway Restart — Гороскопы генерируются заново

**What goes wrong:**
Кэш гороскопов хранится в памяти (`_horoscope_cache` в `src/services/ai/cache.py`). Railway перезапускает сервис при деплое, memory limit, или плановом обслуживании. Все 12 кэшированных гороскопов теряются. Первые 12 пользователей после рестарта получают медленный ответ (AI генерация ~10 сек) + лишние API costs.

**Why it happens:**
- Railway использует ephemeral filesystem — локальные данные не сохраняются
- Текущая архитектура: `dict[str, CacheEntry]` в памяти процесса
- Рестарт происходит внезапно, graceful shutdown не всегда возможен

**How to avoid:**
1. **PostgreSQL-backed cache** — хранить кэш в БД (уже есть):
```python
# Новая таблица horoscope_cache
class HoroscopeCache(Base):
    zodiac_sign: str  # primary key
    content: str
    generated_at: datetime
    expires_at: date
```

2. **Warm-up при старте** — проверять, есть ли в БД сегодняшние гороскопы:
```python
async def warmup_cache():
    """Load today's horoscopes from DB into memory on startup."""
    cached = await db.get_today_horoscopes()
    for h in cached:
        _horoscope_cache[h.zodiac_sign] = CacheEntry(text=h.content, ...)
```

3. **Background pre-generation** — генерировать все 12 в фоне до запросов пользователей

**Warning signs:**
- После деплоя первые запросы гороскопов медленные (>5 сек)
- AI costs спайк после каждого рестарта
- Логи показывают "Cache miss" сразу после старта

**Phase to address:**
Phase 1 (Caching) — переход на persistent cache с первого дня v2.0

---

### Pitfall 2: Telegram sendPhoto File ID Not Cached — Повторная загрузка тех же картинок

**What goes wrong:**
Картинки знаков зодиака загружаются на Telegram при каждом sendPhoto вместо использования file_id. При 100 пользователях/день = 100+ загрузок одной картинки. Медленно, трафик, rate limits.

**Why it happens:**
- Telegram Bot API позволяет повторно использовать file_id уже загруженного файла
- Разработчик не сохраняет file_id после первой отправки
- InputFile создаётся каждый раз из локального файла или bytes

**How to avoid:**
1. **Сохранять file_id после первой отправки:**
```python
# В БД или конфиге
ZODIAC_FILE_IDS: dict[str, str] = {}  # zodiac_sign -> file_id

async def send_zodiac_image(chat_id: int, sign: str) -> Message:
    if sign in ZODIAC_FILE_IDS:
        # Используем кэшированный file_id (мгновенная отправка)
        return await bot.send_photo(chat_id, ZODIAC_FILE_IDS[sign])

    # Первая отправка — загружаем файл
    photo = FSInputFile(f"assets/zodiac/{sign}.png")
    message = await bot.send_photo(chat_id, photo)

    # Кэшируем file_id для будущих отправок
    ZODIAC_FILE_IDS[sign] = message.photo[-1].file_id
    return message
```

2. **Bootstrap file_ids** — при первом деплое отправить все картинки в тестовый чат и сохранить file_id в БД/env

3. **Использовать file_unique_id для дедупликации** — если картинка обновилась

**Warning signs:**
- sendPhoto занимает 1-3 сек вместо мгновенного
- "Uploading photo" статус показывается каждый раз
- Telegram rate limit errors при высокой нагрузке

**Phase to address:**
Phase 1 (Images) — file_id caching с первой интеграции картинок

---

### Pitfall 3: APScheduler Jobs Lost After Railway Redeploy — Pre-generation не работает

**What goes wrong:**
Scheduled job для pre-generation гороскопов (каждые 12 часов) создан с `replace_existing=True`, но после Railway redeploy SQLAlchemyJobStore показывает job в БД, но процесс не подхватил его. Гороскопы не pre-generируются, первые пользователи утром ждут.

**Why it happens:**
- `SQLAlchemyJobStore` хранит jobs в БД, но scheduler instance создаётся заново
- Job с `misfire_grace_time=3600` но прошло больше часа — job считается пропущенным
- Не настроен `coalesce=True` — если 3 execution пропущены, все 3 пытаются запуститься

**How to avoid:**
1. **Увеличить misfire_grace_time или убрать:**
```python
scheduler.add_job(
    pre_generate_horoscopes,
    CronTrigger(hour="0,12", timezone="Europe/Moscow"),
    id="pre_generate_horoscopes",
    replace_existing=True,
    misfire_grace_time=None,  # Всегда выполнять при старте
    coalesce=True,  # Объединить пропущенные в одно выполнение
)
```

2. **Startup check** — при старте проверить, нужно ли выполнить job:
```python
async def on_startup():
    # Если последняя генерация >12 часов назад — запустить сейчас
    if await should_regenerate_horoscopes():
        await pre_generate_horoscopes()
```

3. **Railway native cron** — для критичных задач использовать Railway Cron Jobs вместо APScheduler

**Warning signs:**
- Логи APScheduler: "was missed by 0:XX:XX"
- Утром нет pre-generated гороскопов
- Job в БД (`apscheduler_jobs`) с прошлой датой `next_run_time`

**Phase to address:**
Phase 2 (Background Jobs) — misfire handling с первого дня

---

### Pitfall 4: Cache Race Condition — Два пользователя получают разные "сегодняшние" гороскопы

**What goes wrong:**
Пользователь A запрашивает гороскоп Овна в 23:59:59. Cache miss, начинается AI генерация (10 сек).
Пользователь B запрашивает в 00:00:01 (новый день). Также cache miss (дата изменилась), ещё одна генерация.
Пользователь A получает гороскоп за "вчера", B — за "сегодня". Оба кэшируются, но для разных дат.
Если A запросит снова — получит устаревший.

**Why it happens:**
- Проверка даты кэша: `if date.today() > expires_date` — race condition на границе дня
- Нет lock при генерации — concurrent requests запускают параллельные генерации
- In-memory cache не атомарен

**How to avoid:**
1. **Lock per zodiac sign при генерации:**
```python
_generation_locks: dict[str, asyncio.Lock] = {}

async def get_horoscope(sign: str) -> str:
    if sign not in _generation_locks:
        _generation_locks[sign] = asyncio.Lock()

    async with _generation_locks[sign]:
        # Double-check после получения lock
        cached = await get_cached_horoscope(sign)
        if cached:
            return cached

        # Генерируем и кэшируем
        text = await generate_horoscope(sign)
        await set_cached_horoscope(sign, text)
        return text
```

2. **Pre-generate все 12 атомарно** — не по запросу пользователя

3. **Timezone-aware expiration** — кэш истекает в 00:00 Moscow, не local server time:
```python
def get_cache_expires_date() -> date:
    moscow = datetime.now(ZoneInfo("Europe/Moscow"))
    return moscow.date()
```

**Warning signs:**
- Два пользователя получают разный текст для одного знака в один день
- Дублирующиеся AI запросы в логах для одного знака
- "Стоимость гороскопов" > 12 генераций в день

**Phase to address:**
Phase 1 (Caching) — locking с первого дня

---

### Pitfall 5: sendPhoto без Chat Action — Пользователь думает бот завис

**What goes wrong:**
Генерация картинки занимает 2-5 секунд (загрузка из S3, resize, отправка). Пользователь нажал кнопку и видит ничего. Думает бот завис. Нажимает снова. 3 дублирующихся запроса.

**Why it happens:**
- Telegram показывает "typing..." только если вызван sendChatAction
- При sendPhoto без предварительного action — нет индикации
- Aiogram не добавляет chat action автоматически

**How to avoid:**
1. **ChatActionSender для загрузки картинок:**
```python
from aiogram.utils.chat_action import ChatActionSender

async def send_zodiac_card(message: Message, sign: str):
    async with ChatActionSender.upload_photo(
        chat_id=message.chat.id,
        bot=message.bot
    ):
        # Пока идёт генерация — показывается "uploading photo..."
        image = await generate_zodiac_image(sign)
        await message.answer_photo(image)
```

2. **Middleware с flags для автоматического action:**
```python
@router.callback_query(...)
@flags.chat_action(action="upload_photo")
async def handle_zodiac_image(callback: CallbackQuery):
    ...
```

3. **Debounce повторных нажатий** — игнорировать если уже обрабатывается

**Warning signs:**
- Пользователи жалуются "бот молчит"
- Дублирующиеся callback_query в логах
- Время от нажатия до ответа >2 сек без индикации

**Phase to address:**
Phase 1 (Images) — chat actions с первой картинки

---

### Pitfall 6: Картинки >10MB или неправильный формат — sendPhoto fails

**What goes wrong:**
Красивые PNG картинки для таро-раскладов весят 15MB. sendPhoto возвращает ошибку. Или JPG с прозрачностью — артефакты. Или WebP не отображается в некоторых клиентах.

**Why it happens:**
- Telegram Bot API лимит для sendPhoto: 10MB
- PNG с прозрачностью — большой размер
- Dimension limit: width + height <= 10000px

**How to avoid:**
1. **Оптимизация при сборке:**
```python
from PIL import Image

def optimize_for_telegram(image_path: str) -> bytes:
    img = Image.open(image_path)

    # Resize если слишком большая
    max_dimension = 2000
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension))

    # Конвертируем в JPEG для фото, PNG для графики с прозрачностью
    buffer = BytesIO()
    if img.mode == 'RGBA':
        img.save(buffer, 'PNG', optimize=True)
    else:
        img.save(buffer, 'JPEG', quality=85, optimize=True)

    buffer.seek(0)
    return buffer.getvalue()
```

2. **Pre-check размер перед отправкой:**
```python
MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10MB

if len(image_bytes) > MAX_PHOTO_SIZE:
    # Fallback: отправить как document или сжать сильнее
    await bot.send_document(chat_id, BufferedInputFile(image_bytes, "card.png"))
```

3. **WebP для лучшего сжатия** — но тестировать на старых клиентах

**Warning signs:**
- "Bad Request: photo_invalid_dimensions" в логах
- "Request Entity Too Large" ошибки
- Картинки отображаются с артефактами

**Phase to address:**
Phase 1 (Images) — image pipeline с оптимизацией

---

### Pitfall 7: Monitoring Cardinality Explosion — Prometheus падает

**What goes wrong:**
Метрика `horoscope_requests{user_id="123", zodiac="aries"}` создаёт отдельный time series на каждого пользователя. 10,000 пользователей = 120,000 time series (12 знаков). Prometheus OOM, Grafana тормозит.

**Why it happens:**
- High-cardinality labels: user_id, session_id, request_id
- Разработчик хочет видеть детали — добавляет все labels
- Prometheus держит все active series в памяти

**How to avoid:**
1. **Запрет high-cardinality labels:**
```python
# ПЛОХО
horoscope_counter.labels(
    user_id=user.telegram_id,  # Уникален для каждого пользователя!
    zodiac=sign
).inc()

# ХОРОШО
horoscope_counter.labels(
    zodiac=sign,
    subscription_type="premium"  # Ограниченное количество значений
).inc()
```

2. **Counters вместо per-user metrics:**
```python
# Агрегированные метрики
horoscopes_generated_total = Counter("horoscopes_generated_total", "Total horoscopes", ["zodiac"])
active_users_gauge = Gauge("active_users", "DAU")  # Обновлять раз в час
```

3. **Логи для детализации** — user_id в structured logs, не в metrics

**Warning signs:**
- Prometheus memory usage растёт линейно с users
- Grafana queries timeout
- `prometheus_tsdb_head_series` показывает >100,000

**Phase to address:**
Phase 3 (Monitoring) — metrics design review перед внедрением

---

### Pitfall 8: Визуальные изменения ломают существующий flow — Пользователи путаются

**What goes wrong:**
Добавили картинку перед гороскопом. Теперь сообщение в 2 частях (photo + text). Inline кнопки под текстом, не под картинкой. Пользователи привыкли к старому layout — нажимают не туда, пишут "где кнопки?".

**Why it happens:**
- sendPhoto + sendMessage = 2 сообщения, кнопки только под вторым
- Media + caption имеет лимит 1024 символа для caption
- Inline keyboard можно прикрепить только к одному сообщению

**How to avoid:**
1. **Использовать caption с картинкой:**
```python
# Картинка + текст + кнопки в ОДНОМ сообщении
await bot.send_photo(
    chat_id,
    photo=zodiac_image,
    caption=horoscope_text[:1024],  # Лимит caption!
    reply_markup=inline_keyboard
)
```

2. **Если текст >1024 — Media Group или ссылка на Telegraph:**
```python
if len(text) > 1024:
    # Короткий caption + ссылка "Читать полностью"
    short_text = text[:900] + "...\n\n[Читать полностью](telegraph_url)"
    await bot.send_photo(chat_id, photo, caption=short_text, parse_mode="Markdown")
```

3. **A/B тест нового UI** — 10% пользователей видят новый, собираем feedback

4. **Announce changes** — "Мы обновили дизайн! Теперь с красивыми картинками"

**Warning signs:**
- Резкое падение engagement после визуальных изменений
- Пользователи пишут "раньше было удобнее"
- Клики на кнопки упали

**Phase to address:**
Phase 1 (Images) — UI/UX design с учётом ограничений Telegram

---

### Pitfall 9: Background Job Silently Fails — Гороскопы пустые

**What goes wrong:**
Pre-generation job запустился, но OpenRouter вернул ошибку. Job не retry, не alert. Утром все 12 гороскопов пустые или со старыми данными. Пользователи получают "Гороскоп временно недоступен".

**Why it happens:**
- `try/except` с `pass` или просто логирование без action
- APScheduler не retry failed jobs по умолчанию
- Нет health check для результата job

**How to avoid:**
1. **Explicit error handling с retry:**
```python
async def pre_generate_horoscopes():
    for sign in ZODIAC_SIGNS:
        for attempt in range(3):
            try:
                text = await generate_horoscope(sign)
                await save_to_cache(sign, text)
                break
            except Exception as e:
                logger.error("Generation failed", sign=sign, attempt=attempt, error=str(e))
                if attempt == 2:
                    # Финальная попытка failed — alert
                    await send_admin_alert(f"Horoscope generation failed for {sign}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

2. **Verification job после generation:**
```python
async def verify_horoscopes():
    """Run after pre_generate to verify all 12 exist."""
    missing = []
    for sign in ZODIAC_SIGNS:
        if not await get_cached_horoscope(sign):
            missing.append(sign)

    if missing:
        await send_admin_alert(f"Missing horoscopes: {missing}")
        # Trigger regeneration for missing
        for sign in missing:
            await generate_horoscope_with_retry(sign)
```

3. **Monitoring метрика:**
```python
horoscopes_cached_gauge = Gauge("horoscopes_cached", "Number of cached horoscopes for today")
# В pre_generate_horoscopes:
horoscopes_cached_gauge.set(count_cached_today())
# Alert если < 12 после 00:30
```

**Warning signs:**
- `horoscopes_cached` gauge < 12
- Errors в логах APScheduler без recovery
- Пользователи видят fallback сообщения утром

**Phase to address:**
Phase 2 (Background Jobs) — error handling и verification

---

### Pitfall 10: Timezone Mismatch — Job запускается не вовремя

**What goes wrong:**
Pre-generation настроен на `hour=0, timezone="Europe/Moscow"`. Railway server в UTC. APScheduler использует server local time. Job запускается в 00:00 UTC = 03:00 Moscow. Пользователи в Москве просыпаются в 07:00, а гороскопы сгенерированы для "вчера" по их ощущению.

**Why it happens:**
- Путаница между server timezone, scheduler timezone, user timezone
- `CronTrigger(hour=0)` без явного timezone использует scheduler default
- Текущий код: `CronTrigger(hour=9, minute=0, timezone="Europe/Moscow")` — правильно, но легко забыть

**How to avoid:**
1. **Всегда explicit timezone:**
```python
from pytz import timezone

MOSCOW_TZ = timezone("Europe/Moscow")

scheduler.add_job(
    pre_generate_horoscopes,
    CronTrigger(hour=0, minute=5, timezone=MOSCOW_TZ),  # 00:05 Moscow
    id="pre_generate",
    replace_existing=True,
)
```

2. **Scheduler default timezone = Moscow:**
```python
scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    timezone=MOSCOW_TZ,  # Все jobs по умолчанию в Moscow
)
```

3. **Тестирование timezone:**
```python
def test_job_runs_at_moscow_midnight():
    # Mock datetime to 23:59 Moscow, verify job not triggered
    # Mock datetime to 00:01 Moscow, verify job triggered
```

4. **Логировать timezone при выполнении:**
```python
async def pre_generate_horoscopes():
    moscow_now = datetime.now(MOSCOW_TZ)
    logger.info("Starting pre-generation", moscow_time=moscow_now.isoformat())
```

**Warning signs:**
- Логи показывают job execution в неожиданное время
- Гороскопы "сегодня" отличаются от ожидаемых
- `next_run_time` в БД не совпадает с ожидаемым

**Phase to address:**
Phase 2 (Background Jobs) — timezone handling от начала

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| In-memory cache без persistence | Быстрая разработка | Потеря данных при restart | Никогда для pre-generated content |
| file_id не кэшируется | Проще код | Медленная отправка, rate limits | MVP только |
| Все картинки одного размера | Меньше кода | Плохой UX на разных устройствах | MVP, optimize в Phase 2 |
| Metrics с user_id label | Детальная отладка | Cardinality explosion | Никогда в production |
| Job без retry logic | Меньше кода | Silent failures | Никогда для critical jobs |
| Caption >1024 обрезается | Быстрый fix | Потеря информации | Никогда, использовать Telegraph |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| aiogram sendPhoto | Загружать файл каждый раз | Кэшировать file_id после первой отправки |
| aiogram ChatAction | Не показывать "uploading photo" | ChatActionSender context manager |
| APScheduler CronTrigger | timezone не указан | Всегда explicit timezone="Europe/Moscow" |
| APScheduler JobStore | Не проверять misfired jobs при старте | startup check + misfire_grace_time=None |
| PIL Image | Отправлять PNG >10MB | Optimize + resize перед отправкой |
| Prometheus | Labels с user_id | Только low-cardinality labels |
| Railway | Полагаться на filesystem | Всё в БД или external storage |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Загрузка картинок при каждом запросе | sendPhoto >1 сек | file_id caching | >50 users/day |
| In-memory cache после restart | Spike AI costs после deploy | PostgreSQL-backed cache | При любом deploy |
| 12 последовательных AI calls | Pre-generation >2 мин | Parallel generation | >12 знаков или >1 вариант |
| Metrics для каждого user | Prometheus OOM | Агрегированные counters | >1000 active users |
| Resize картинок on-the-fly | CPU spike при отправке | Pre-processed assets | >10 concurrent sends |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Нет "uploading photo" индикатора | "Бот завис" | ChatActionSender |
| 2 сообщения вместо 1 (photo + text) | Путаница с кнопками | Использовать caption |
| Текст обрезан в caption | Неполная информация | Telegraph ссылка |
| Разный UI для free/premium без объяснения | "Почему у меня нет картинки?" | Явный teaser + CTA |
| Резкое изменение layout | Дезориентация | Gradual rollout + announcement |
| Fallback "гороскоп недоступен" | Разочарование | Cached previous day + "обновится скоро" |

## "Looks Done But Isn't" Checklist

- [ ] **Images:** file_id caching — verify повторная отправка использует cached ID, не upload
- [ ] **Images:** Размер проверен — verify все assets <10MB и dimensions <10000 total
- [ ] **Cache:** Persistent storage — verify гороскопы сохраняются после restart
- [ ] **Cache:** Race condition handling — verify lock при concurrent генерации
- [ ] **Cache:** Timezone-aware expiration — verify кэш истекает в 00:00 Moscow
- [ ] **Jobs:** Misfire handling — verify job выполняется после downtime
- [ ] **Jobs:** Error recovery — verify retry при AI failure
- [ ] **Jobs:** Verification — verify все 12 гороскопов сгенерированы
- [ ] **Monitoring:** Cardinality check — verify нет user_id в metrics labels
- [ ] **Monitoring:** Alerts — verify alert при <12 cached horoscopes
- [ ] **UX:** Chat actions — verify "uploading photo" показывается
- [ ] **UX:** Caption limits — verify длинный текст не обрезается

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Cache lost on restart | LOW | Warm-up из БД, regenerate missing |
| file_id not cached | LOW | Bootstrap: отправить в тестовый чат, сохранить IDs |
| Missed scheduled job | LOW | Manual trigger + fix misfire_grace_time |
| Race condition в cache | MEDIUM | Add locking, clear inconsistent entries |
| Cardinality explosion | MEDIUM | Remove bad labels, restart Prometheus, compact TSDB |
| Image too large | LOW | Optimize assets, re-deploy |
| Timezone bug | LOW | Fix timezone config, verify next_run_time |
| Silent job failure | MEDIUM | Add alerting, backfill missing data |
| UI confusion | LOW-MEDIUM | Rollback or add explanation message |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| In-memory cache loss | Phase 1 (Caching) | Restart service, verify cache warm |
| file_id not cached | Phase 1 (Images) | Check logs for upload vs file_id |
| APScheduler job loss | Phase 2 (Jobs) | Simulate redeploy, verify job runs |
| Cache race condition | Phase 1 (Caching) | Concurrent requests test |
| No chat action | Phase 1 (Images) | UI test with slow network |
| Image size limits | Phase 1 (Images) | Test all assets <10MB |
| Cardinality explosion | Phase 3 (Monitoring) | Check series count after deployment |
| UX confusion | Phase 1 (Images) | A/B test + user feedback |
| Silent job failure | Phase 2 (Jobs) | Simulate AI timeout, verify alert |
| Timezone mismatch | Phase 2 (Jobs) | Check job execution time in logs |

## Sources

**Telegram Bot API:**
- [sendPhoto documentation](https://docs.aiogram.dev/en/dev-3.x/api/methods/send_photo.html)
- [File upload & file_id caching](https://core.telegram.org/bots/api#sending-files)
- [Chat Actions](https://docs.aiogram.dev/en/latest/api/methods/send_chat_action.html)
- [ChatActionSender utility](https://docs.aiogram.dev/en/v3.0.0rc1/utils/chat_action.html)
- [Telegram file size limits](https://limits.tginfo.me/en)

**APScheduler:**
- [User guide — misfire handling](https://apscheduler.readthedocs.io/en/3.x/userguide.html)
- [Job persistence with SQLAlchemyJobStore](https://apscheduler.readthedocs.io/en/3.x/userguide.html#configuring-the-scheduler)
- [FAQ — misfired jobs](https://apscheduler.readthedocs.io/en/3.x/faq.html)
- [misfire_grace_time issues](https://github.com/agronholm/apscheduler/issues/146)

**Caching & Race Conditions:**
- [Redis vs In-Memory Cache](https://blog.nashtechglobal.com/redis-cache-vs-in-memory-cache-when-to-use-what/)
- [Cache race conditions](https://medium.com/pythoneers/avoiding-race-conditions-in-python-in-2025-best-practices-for-async-and-threads-4e006579a622)
- [Cache invalidation patterns](https://gajabagi.medium.com/caching-part-1-a-deep-dive-into-sync-race-conditions-and-the-timeline-fallacy-41cb10bbffe8)

**Monitoring:**
- [Prometheus cardinality management](https://last9.io/blog/how-to-manage-high-cardinality-metrics-in-prometheus/)
- [Prometheus best practices](https://betterstack.com/community/guides/monitoring/prometheus-best-practices/)
- [High cardinality metrics](https://medium.com/@dotdc/prometheus-performance-and-cardinality-in-practice-74d5d9cd6230)

**Railway:**
- [Cron Jobs documentation](https://docs.railway.com/guides/cron-jobs)
- [Ephemeral filesystem behavior](https://docs.railway.com/reference/cron-jobs)

---
*Pitfalls research for: v2.0 enhancements (visuals, caching, background jobs, monitoring)*
*Researched: 2026-01-23*
