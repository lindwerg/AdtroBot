# Feature Research: v2.0 Visual & Performance Enhancements

**Domain:** Telegram astrology/tarot bot with freemium model
**Researched:** 2026-01-23
**Confidence:** MEDIUM (WebSearch + official Telegram docs + existing codebase analysis)

## Context: v2.0 Goals

v1.0 уже shipped с полным функционалом. v2.0 фокусируется на:
1. **Performance** — быстрые ответы, фоновая генерация, кеширование
2. **Visual enhancement** — изображения для key moments
3. **UX fixes** — исправление pain points из v1.0
4. **Monitoring** — tracking usage и costs

**User pain points из v1.0:**
- Долгие ответы при нажатии кнопок (AI generation блокирует)
- Непонятно за что платят (общий vs личный гороскоп выглядят одинаково)
- Нет понятного пути free -> premium
- Markdown разметка видна пользователям

---

## Feature Landscape for v2.0

### Table Stakes (Users Expect These)

Features users assume exist in professional Telegram bots. Missing these = product feels incomplete/amateur.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Typing indicator во время AI generation** | Telegram native UX pattern. Без него кажется что бот завис. | LOW | `bot.send_chat_action(action=ChatActions.TYPING)` каждые 5 сек во время AI запроса. Уже есть `asyncio.sleep` — заменить на typing loop. |
| **Быстрый ответ на /start (<1 сек)** | Первое впечатление. Медленный старт = отток. | MEDIUM | Сейчас есть DB query. Нужен кеш существующих пользователей или отложенная загрузка. |
| **Кеширование общих гороскопов** | 12 знаков x AI call = дорого и медленно. Контент одинаков для всех. | MEDIUM | Уже есть `_horoscope_cache` в `cache.py`. Нужна фоновая генерация через APScheduler каждые 12ч. |
| **Markdown/HTML корректное форматирование** | Видимая разметка (*текст*) выглядит непрофессионально. | LOW | Использовать `parse_mode=HTML` или entity-based formatting. Уже есть `Text(), Bold()` — проверить все handlers. |
| **Изображение welcome screen** | Визуальный хук. Чистый текст скучен. | LOW | Одно изображение. `send_photo()` + caption. file_id кешируется автоматически Telegram. |
| **BotFather description и about** | Поиск в Telegram использует description. Без него бот не найдут. | LOW | Команды `/setdescription`, `/setabouttext` в BotFather. Копирайтинг. |

### Differentiators (Competitive Advantage)

Features that set AdtroBot apart в астро/таро нише. Не ожидаются, но добавляют ценность.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **AI-generated изображения знаков зодиака** | Уникальный визуал вместо stock photos. Единый стиль = узнаваемость бренда. | HIGH | 12 изображений в едином стиле. TarotAI/CGDream для consistency. Генерация один раз, хранение file_id. |
| **Визуальное разделение free vs premium** | Решает pain point "непонятно за что платят". | MEDIUM | Разные заголовки, emoji, структура текста. Premium = детальные сферы жизни с разделителями. |
| **Soft paywall после value delivery** | Конверсия после демонстрации ценности, не до. | MEDIUM | Показать гороскоп -> потом teaser premium. Уже есть `PREMIUM_TEASER`. Усилить визуально. |
| **Onboarding с интерактивными slides** | Engagement на старте, объяснение ценности. | HIGH | telegram-onboarding-kit или свой flow. Mini App для rich UI. |
| **Персонализированные изображения таро** | AI генерация уникальных карт под вопрос. | VERY HIGH | MyShell/TarotAI patterns. Долгая генерация, высокая стоимость. Future consideration. |
| **Progress bar при длинных операциях** | UX сигнал что бот работает. Снижает anxiety. | LOW | Редактирование сообщения: "Читаю карты... [====    ]" |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems in Telegram bot context.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Real-time AI streaming в сообщения** | "Как ChatGPT". Видно как печатается. | Telegram rate limits (30 msg/sec). Каждый edit = API call. Быстро упрешься в лимит. | Typing indicator + финальное сообщение. Для длинных текстов — Telegraph link. |
| **Изображение для каждой карты таро (78 шт custom)** | "Полная колода с уникальным AI артом". | 78 генераций x стоимость. Долгая начальная генерация. Большой размер assets. | Текущие изображения достаточны. Фокус на интерпретации, не визуале карт. |
| **Ежедневные push-уведомления с изображением** | "Красивые утренние сообщения". | Каждое изображение = bandwidth cost. 1000 юзеров x 30 дней = 30K images/month. | Текстовые уведомления + изображение только при открытии бота. |
| **Mini App для всего функционала** | "Современный UI как приложение". | Разработка и поддержка двух интерфейсов. Mini App для простых ботов overkill. | Mini App только для onboarding/paywall если нужен rich UI. Основной функционал через бот. |
| **Сложная gamification (достижения, уровни)** | "Увеличит retention". | Отвлекает от core value (астрология). Усложняет бота. | Простой retention: карта дня + streak counter (опционально в v3+). |
| **Детальная натальная карта в сообщении** | "Всё в одном месте". | Telegram 4096 char limit. SVG не рендерится inline. | Telegraph для текста + SVG как документ. Уже реализовано в v1.0. |

---

## Feature Dependencies

```
[Фоновая генерация гороскопов]
    |--requires--> [APScheduler настроен] (уже есть в v1.0)
                       |--enhances--> [Быстрые ответы на zodiac buttons]

[Изображения знаков зодиака]
    |--requires--> [AI image generator выбран]
                       |--requires--> [file_id storage schema]

[Welcome изображение]
    |--independent--> (можно делать первым)

[Soft paywall enhancement]
    |--requires--> [Визуальное разделение free/premium]
                       |--enhances--> [Conversion funnel clarity]

[Typing indicator]
    |--requires--> [Refactor AI call handlers]
                       |--enhances--> [User perceived performance]

[Monitoring metrics]
    |--requires--> [Database tables for tracking]
                       |--enhances--> [Admin panel dashboards]
```

### Dependency Notes

- **Фоновая генерация requires APScheduler:** Уже есть в v1.0 для notifications. Добавить job для horoscope pre-generation.
- **Изображения requires file_id storage:** Telegram кеширует file_id после первой отправки. Нужна таблица для хранения или config.
- **Monitoring requires DB tables:** `horoscopes_today` metric нужна отдельная таблица tracking.
- **Typing indicator requires handler refactor:** Текущие handlers делают AI call синхронно. Нужен background task + typing loop.

---

## v2.0 Phase Definition

### Phase 1: Performance & UX Quick Wins

Критические исправления без новых зависимостей. Максимальный impact на user experience.

- [ ] **Typing indicator** — LOW complexity, HIGH impact на perceived speed
- [ ] **Markdown/HTML fix** — LOW complexity, профессиональный вид
- [ ] **BotFather description** — LOW complexity, SEO в Telegram
- [ ] **Progress messages** — LOW complexity, UX при AI generation

### Phase 2: Caching & Background Jobs

Performance foundation. Снижение latency и AI costs.

- [ ] **Фоновая генерация 12 гороскопов** — MEDIUM complexity, daily job в APScheduler
- [ ] **Warm cache on startup** — MEDIUM complexity, pre-load при запуске бота
- [ ] **file_id caching для изображений** — LOW complexity, DB column или config

### Phase 3: Visual Enhancement

Изображения и визуальное улучшение.

- [ ] **Welcome screen image** — LOW complexity, один asset
- [ ] **Zodiac sign images (12 шт)** — HIGH complexity, AI generation + consistency
- [ ] **Premium vs free visual distinction** — MEDIUM complexity, formatting + emoji
- [ ] **Paywall image** — LOW complexity, один asset

### Phase 4: Onboarding & Conversion

Conversion funnel optimization.

- [ ] **Enhanced welcome text** — LOW complexity, copywriting
- [ ] **Soft paywall flow** — MEDIUM complexity, message ordering
- [ ] **Clear premium value proposition** — MEDIUM complexity, content structure

### Phase 5: Monitoring

Observability и metrics.

- [ ] **horoscopes_today tracking table** — MEDIUM complexity, DB migration
- [ ] **Bot health metrics endpoint** — MEDIUM complexity, FastAPI route
- [ ] **API costs tracking** — MEDIUM complexity, middleware для OpenRouter calls

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Typing indicator | HIGH | LOW | **P1** |
| Markdown fix | HIGH | LOW | **P1** |
| BotFather description | MEDIUM | LOW | **P1** |
| Фоновая генерация гороскопов | HIGH | MEDIUM | **P1** |
| Welcome image | MEDIUM | LOW | **P1** |
| Zodiac images (12) | MEDIUM | HIGH | **P2** |
| Premium visual distinction | HIGH | MEDIUM | **P1** |
| Soft paywall enhancement | HIGH | MEDIUM | **P2** |
| Monitoring metrics | MEDIUM | MEDIUM | **P2** |
| Onboarding Mini App | LOW | HIGH | **P3** (defer) |
| Персонализированные таро images | LOW | VERY HIGH | **P3** (defer) |

**Priority key:**
- **P1:** Must have for v2.0 — критично для UX и performance
- **P2:** Should have — добавляет value, делать после P1
- **P3:** Nice to have — future consideration, defer to v3+

---

## Implementation Recommendations

### Typing Indicator: Паттерн

```python
import asyncio
from aiogram.enums import ChatAction

async def with_typing(bot, chat_id: int, coro):
    """Wrapper для показа typing во время async операции."""
    async def typing_loop():
        while True:
            await bot.send_chat_action(chat_id, ChatAction.TYPING)
            await asyncio.sleep(4)  # Typing длится 5 сек, refresh каждые 4

    task = asyncio.create_task(typing_loop())
    try:
        return await coro
    finally:
        task.cancel()

# Использование:
interpretation = await with_typing(bot, chat_id, ai.generate_interpretation(...))
```

### Изображения: Подход

**Рекомендация:** Использовать CGDream или FLUX.2 через getimg.ai для 12 zodiac images + 2 статичных (welcome, paywall).

**Почему:**
1. CGDream — 100 бесплатных credits/день, достаточно для генерации
2. Transfer Style feature для consistency
3. Один раз сгенерировать, сохранить file_id после первой отправки

**Альтернатива:** Midjourney/DALL-E для высшего качества, но платно.

**file_id caching pattern:**
```python
# После первой отправки сохраняем file_id
msg = await bot.send_photo(chat_id, photo=InputFile("welcome.jpg"))
file_id = msg.photo[-1].file_id  # Highest resolution
# Сохранить в config/DB

# Последующие отправки — мгновенно через file_id
await bot.send_photo(chat_id, photo=stored_file_id)
```

### Кеширование: Архитектура

**Текущее состояние:** In-memory `_horoscope_cache` в `cache.py`. Очищается при рестарте.

**Рекомендация для v2.0:**
1. Сохранить in-memory для MVP (Railway рестарты редки)
2. Добавить APScheduler job: генерация 12 гороскопов каждые 12ч
3. Warm cache при старте бота если сегодня нет кеша

**Фоновая генерация job:**
```python
from apscheduler.triggers.interval import IntervalTrigger

async def generate_all_horoscopes():
    """Pre-generate all 12 zodiac horoscopes."""
    for sign in ZODIAC_SIGNS:
        text = await ai.generate_horoscope(sign)
        await set_cached_horoscope(sign, text)

scheduler.add_job(
    generate_all_horoscopes,
    IntervalTrigger(hours=12),
    id="horoscope_generation",
    replace_existing=True
)
```

**Future (если нужна персистентность):** Redis через Railway addon.

### Visual Distinction: Шаблоны

**Free гороскоп:**
```
Овен на 23.01.2026

[Общий текст без деталей по сферам]

--------------------
Хочешь детальный прогноз по любви,
карьере и здоровью? Подписка 299р/мес
```

**Premium гороскоп:**
```
Персональный гороскоп для Овен
на 23.01.2026

ЛЮБОВЬ
[Детальный текст]

КАРЬЕРА
[Детальный текст]

ЗДОРОВЬЕ
[Детальный текст]

ФИНАНСЫ
[Детальный текст]
```

### Soft Paywall Flow

Рекомендуемая последовательность на основе telegram-onboarding-kit patterns:

1. **Value first:** Показать бесплатный контент (гороскоп/карту дня)
2. **Natural break:** После контента, не прерывая
3. **Clear CTA:** Конкретное предложение с ценой
4. **One-click:** Inline button прямо к оплате

```
[Гороскоп текст]

--------------------
Это общий прогноз.

С подпиской ты получишь:
- Детальный гороскоп по 4 сферам жизни
- Персональный прогноз по натальной карте
- 20 раскладов таро в день

[Подписка 299р/мес] [Подробнее]
```

---

## Competitor Feature Analysis for v2.0

| Feature | @HoroscopeBot | @Stellium | AdtroBot v2.0 Approach |
|---------|---------------|-----------|------------------------|
| Zodiac images | Stock photos | AI-generated | AI-generated в едином стиле |
| Onboarding | Простой /start | Elaborate flow | Enhanced welcome + soft paywall |
| Tarot visuals | Статичная колода | N/A | Текущая колода + AI интерпретации |
| Premium distinction | Нет | Нет явной | Визуальное разделение headers + structure |
| Response time | Быстро (кеш) | Медленно (AI) | Кеш для общих + typing для персональных |
| Natal chart | Нет | Есть | Есть (v1.0) + SVG visualization |

---

## Integration with Existing v1.0 Codebase

### Files to Modify

| File | Changes |
|------|---------|
| `src/bot/handlers/horoscope.py` | Add typing indicator wrapper, visual distinction templates |
| `src/bot/handlers/tarot.py` | Add typing indicator, progress messages |
| `src/bot/handlers/start.py` | Add welcome image, enhanced text |
| `src/services/ai/cache.py` | Add background generation trigger |
| `src/services/scheduler.py` | Add horoscope generation job |
| `src/bot/utils/formatting.py` | Fix markdown issues, add premium templates |

### New Files Needed

| File | Purpose |
|------|---------|
| `src/bot/utils/typing.py` | Typing indicator wrapper utility |
| `src/config/images.py` | file_id storage for images |
| `src/db/models/metrics.py` | Monitoring tables |
| `src/admin/services/health.py` | Health metrics endpoint |

---

## Sources

### Официальные источники (HIGH confidence)
- [Telegram Bot API - sendChatAction](https://core.telegram.org/bots/api#sendchataction)
- [Telegram Bot API - Sending files](https://core.telegram.org/bots/api#sending-files) — file_id caching
- [aiogram 3 documentation](https://docs.aiogram.dev/en/dev-3.x/)

### Паттерны и best practices (MEDIUM confidence)
- [Telegram Onboarding Kit](https://github.com/Easterok/telegram-onboarding-kit) — onboarding/paywall patterns
- [Optimising Telegram Bot Response Times](https://dev.to/imthedeveloper/optimising-telegram-bot-response-times-1a64)
- [Building Telegram Bots That Scale](https://medium.com/@strongnationdev/the-secrets-behind-building-telegram-bots-that-scale-to-thousands-of-users-737236156377)
- [Telegram Bot Analytics Metrics](https://bazucompany.com/blog/telegram-bot-analytics-metrics-you-must-track/)

### AI Image Generation (MEDIUM confidence)
- [CGDream Tarot Generator](https://cgdream.ai/features/ai-tarot-card-generator) — free credits, style transfer
- [Vheer Zodiac Card Generator](https://vheer.com/ai-zodiac-card-generator) — zodiac-specific
- [getimg.ai FLUX.2](https://getimg.ai/use-cases/ai-tarot-card-generator)

### Существующий код (HIGH confidence)
- `/Users/kirill/Desktop/AdtroBot/src/services/ai/cache.py` — текущая архитектура кеширования
- `/Users/kirill/Desktop/AdtroBot/src/bot/handlers/start.py` — текущий onboarding flow
- `/Users/kirill/Desktop/AdtroBot/src/bot/handlers/horoscope.py` — premium teaser pattern

---
*Feature research for: AdtroBot v2.0 Visual & Performance Enhancements*
*Researched: 2026-01-23*
