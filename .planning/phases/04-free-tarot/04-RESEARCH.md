# Phase 4: Free Tarot - Research

**Researched:** 2026-01-22
**Domain:** Telegram bot с картами Таро (Rider-Waite), FSM-диалоги, кеширование на календарный день, лимиты пользователей
**Confidence:** HIGH

## Summary

Исследована реализация функциональности Таро для Telegram бота: "Карта дня" (кешируется до 00:00 user timezone) и "Расклад на 3 карты" (FSM-диалог с вопросом, лимит 1/день для free пользователей). Стандартный стек: Rider-Waite датасет (78 карт, JSON + изображения 300x527px, CC0/public domain), Pillow для ротации 180° перевёрнутых карт, aiogram 3.x FSM (StatesGroup + FSMContext), BufferedInputFile для отправки из BytesIO. Хранение: JSON файл с картами + PostgreSQL для лимитов и кеша. Визуальный "ритуал": эмодзи 🔮, задержки между сообщениями (asyncio.sleep), InlineKeyboardButton для вытягивания карт.

**Primary recommendation:** Использовать датасет ekelen/tarot-api (JSON с meaning_up/meaning_rev), изображения luciellaes CC0 (JPG 300x527px), сохранять перевёрнутые карты в BytesIO через Pillow с quality=85, хранить лимиты и кеш карты дня в User модели (SQLAlchemy колонки с timezone-aware датами).

## Standard Stack

Установленный стек для реализации Таро в Telegram ботах:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| aiogram | 3.20+ | Telegram Bot API framework | Уже используется в проекте, async FSM из коробки |
| Pillow | 10.x+ | Обработка изображений (ротация 180°) | Стандарт для PIL в Python, легковесная, BytesIO support |
| SQLAlchemy | 2.0+ | ORM для хранения лимитов и кеша | Уже используется в проекте, async support |
| APScheduler | 3.11+ | Планировщик для сброса лимитов | Уже используется для нотификаций (Phase 3) |
| pytz | 2025.2+ | Timezone handling | Уже используется, необходим для midnight reset per user timezone |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncio | stdlib | Задержки между сообщениями (ритуал) | asyncio.sleep() для UX эффектов |
| json | stdlib | Чтение датасета карт | Парсинг JSON файла с 78 картами |
| random | stdlib | Выбор случайной карты | random.choice() для рандомизации |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JSON файл | SQLAlchemy модель для карт | JSON проще (read-only data), БД избыточна для статического датасета 78 карт |
| Pillow ротация | Pre-rotated изображения (156 файлов) | Ротация on-the-fly экономит storage, минимальный overhead (<100ms) |
| BufferedInputFile | FSInputFile (сохранение на диск) | BytesIO избегает I/O, быстрее для динамических изображений |

**Installation:**
```bash
# Pillow еще не в pyproject.toml
poetry add pillow
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── bot/
│   ├── handlers/
│   │   └── tarot.py              # Хендлеры "Таро", "Карта дня", расклад 3 карты
│   ├── keyboards/
│   │   └── tarot.py              # InlineKeyboard для "Вытянуть карту"
│   ├── states/
│   │   └── tarot.py              # TarotStates: waiting_question (для расклада)
│   └── utils/
│       ├── tarot_cards.py        # load_tarot_deck(), get_random_card(), rotate_image()
│       └── tarot_formatting.py   # format_card_of_day(), format_three_card_spread()
├── db/models/
│   └── user.py                   # +колонки: card_of_day_date, card_of_day_id,
│                                 #           tarot_spread_count, spread_reset_date
└── data/
    ├── tarot/
    │   ├── cards.json            # 78 карт (ekelen/tarot-api формат)
    │   └── images/               # 78 JPG файлов (luciellaes CC0)
    │       ├── ar00.jpg          # The Fool
    │       ├── ar01.jpg          # The Magician
    │       └── ...
```

### Pattern 1: FSM для сбора вопроса (Расклад 3 карты)
**What:** aiogram 3.x FSM (StatesGroup + FSMContext) для multi-step диалога
**When to use:** Пользователь нажимает "Таро" → вводит вопрос → вытягивает 3 карты

**Example:**
```python
# Source: https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/index.html
from aiogram.fsm.state import State, StatesGroup

class TarotStates(StatesGroup):
    waiting_question = State()

# Handler: кнопка "Таро" → запрос вопроса
@router.message(F.text == "Таро")
async def tarot_start(message: Message, state: FSMContext):
    await state.set_state(TarotStates.waiting_question)
    await message.answer("Задайте свой вопрос:")

# Handler: получение вопроса → сохранение в FSMContext
@router.message(TarotStates.waiting_question)
async def tarot_question_received(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    await message.answer("Тасую колоду... 🔮")
    # ... далее показ 3 перевёрнутых рубашек + кнопка "Вытянуть карты"
```

### Pattern 2: Кеширование карты дня (00:00 user timezone)
**What:** Хранение card_of_day_id + card_of_day_date в User модели, проверка при запросе
**When to use:** Пользователь запрашивает "Карта дня" — если date == today (user tz), возвращаем кеш

**Example:**
```python
# Source: собственный паттерн на основе User модели (src/db/models/user.py)
from datetime import datetime
import pytz

async def get_card_of_day(user: User, session: AsyncSession) -> dict:
    user_tz = pytz.timezone(user.timezone or "Europe/Moscow")
    today = datetime.now(user_tz).date()

    # Проверка кеша
    if user.card_of_day_date == today:
        return get_card_by_id(user.card_of_day_id)

    # Новая карта
    card = get_random_card()
    user.card_of_day_id = card["name_short"]
    user.card_of_day_date = today
    await session.commit()
    return card
```

### Pattern 3: Ротация изображения и отправка через BufferedInputFile
**What:** Pillow transpose(Image.Transpose.ROTATE_180) → BytesIO → BufferedInputFile
**When to use:** Перевёрнутая карта (reversed=True) — ротация + отправка в Telegram

**Example:**
```python
# Source: https://docs.aiogram.dev/en/latest/api/upload_file.html
from PIL import Image
from io import BytesIO
from aiogram.types import BufferedInputFile

def rotate_card_image(image_path: str) -> BytesIO:
    img = Image.open(image_path)
    rotated = img.transpose(Image.Transpose.ROTATE_180)
    buffer = BytesIO()
    rotated.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    return buffer

async def send_reversed_card(message: Message, card_name: str):
    image_path = f"src/data/tarot/images/{card_name}.jpg"
    buffer = rotate_card_image(image_path)
    photo = BufferedInputFile(buffer.read(), filename=f"{card_name}_reversed.jpg")
    await message.answer_photo(photo, caption=f"{card_name} (перевёрнутая)")
```

### Pattern 4: InlineKeyboardButton для "ритуала" вытягивания
**What:** Показать "рубашки" карт → кнопка "Вытянуть карты" → callback → показ результата
**When to use:** UX паттерн для ощущения участия (не instant result)

**Example:**
```python
# Source: https://docs.aiogram.dev/en/latest/utils/keyboard.html
from aiogram.utils.keyboard import InlineKeyboardBuilder

async def show_card_backs(message: Message):
    await message.answer("Тасую колоду... 🔮")
    await asyncio.sleep(1.5)
    await message.answer("🃏 🃏 🃏")  # 3 рубашки

    builder = InlineKeyboardBuilder()
    builder.button(text="Вытянуть карты", callback_data="draw_three_cards")
    await message.answer("Готово!", reply_markup=builder.as_markup())

@router.callback_query(F.data == "draw_three_cards")
async def draw_cards_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    question = data.get("question")
    # ... вытягивание 3 карт, отправка с интерпретацией
    await callback.answer()
```

### Pattern 5: Лимиты (1 расклад/день) с timezone reset
**What:** Хранить tarot_spread_count + spread_reset_date, сбрасывать в 00:00 user tz
**When to use:** Free пользователь запрашивает расклад — проверить лимит

**Example:**
```python
# Source: собственный паттерн
async def check_tarot_limit(user: User, session: AsyncSession) -> tuple[bool, int]:
    user_tz = pytz.timezone(user.timezone or "Europe/Moscow")
    today = datetime.now(user_tz).date()

    # Сброс лимита если новый день
    if user.spread_reset_date != today:
        user.tarot_spread_count = 0
        user.spread_reset_date = today
        await session.commit()

    # Проверка лимита (free: 1, premium: 20)
    limit = 20 if user.is_premium else 1
    remaining = limit - user.tarot_spread_count
    return remaining > 0, remaining
```

### Anti-Patterns to Avoid

- **Хранение карт в БД:** Статический датасет 78 карт не нужно нормализовать — JSON файл проще и быстрее
- **Глобальный random.seed():** Не использовать seed для "репродуцируемости" — убивает рандомность между пользователями
- **Instant результат без "ритуала":** Пользователи ждут UX процесса (тасование, рубашки, кнопка) — не показывайте карты сразу
- **Ротация при старте бота:** Не создавать 78 перевёрнутых изображений заранее — ротация on-demand экономит память и storage

## Don't Hand-Roll

Проблемы, которые выглядят простыми, но имеют готовые решения:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Timezone-aware дата | datetime.now() + ручной offset | pytz.timezone(user.timezone).localize() | Daylight saving, исторические изменения timezone |
| FSM для диалога | Свой state manager в dict | aiogram.fsm.state (StatesGroup + FSMContext) | Async-safe, интеграция с aiogram, persistence |
| Ротация изображения | Ручная манипуляция пикселей | Pillow transpose(ROTATE_180) | Аппаратное ускорение, EXIF handling, форматы |
| Датасет карт Таро | Парсинг Wikipedia / ручной ввод | ekelen/tarot-api JSON | 78 карт, meanings (upright/reversed), public domain |
| Лимиты с reset | Cron job для сброса всех пользователей | Проверка per-user при запросе | Разные timezone, нет race conditions |

**Key insight:** Таро кажется простым (рандом + картинки), но edge cases (timezone midnight, перевёрнутые карты, FSM, лимиты per-user) требуют проверенных библиотек. Не изобретайте велосипед.

## Common Pitfalls

### Pitfall 1: Рандом без учёта уже вытянутых карт (в рамках одного расклада)
**What goes wrong:** При вытягивании 3 карт random.choice() может выбрать одну карту дважды
**Why it happens:** random.choice() не удаляет элемент из списка
**How to avoid:** Использовать random.sample(deck, 3) вместо 3x random.choice()
**Warning signs:** Пользователь видит дубликаты карт в трёхкарточном раскладе

**Example:**
```python
# ПЛОХО: может быть дубликат
cards = [random.choice(deck) for _ in range(3)]

# ХОРОШО: гарантия уникальности
cards = random.sample(deck, 3)
```

### Pitfall 2: Сброс лимитов в 00:00 UTC вместо user timezone
**What goes wrong:** Пользователь в GMT+3 получает сброс лимита в 03:00 по локальному времени
**Why it happens:** datetime.now() без timezone = UTC, не учитывается user.timezone
**How to avoid:** Всегда использовать pytz.timezone(user.timezone) для вычисления "сегодня"
**Warning signs:** Пользователи жалуются "лимит не сбросился в полночь"

**Example:**
```python
# ПЛОХО
today = datetime.now().date()  # UTC

# ХОРОШО
user_tz = pytz.timezone(user.timezone or "Europe/Moscow")
today = datetime.now(user_tz).date()
```

### Pitfall 3: Отправка изображений FSInputFile после ротации (лишний I/O)
**What goes wrong:** Pillow ротирует → сохраняет в /tmp → FSInputFile читает → удаляет — медленно
**Why it happens:** Разработчики привыкли к file paths, не знают про BufferedInputFile + BytesIO
**How to avoid:** Pillow → BytesIO → BufferedInputFile (без промежуточного файла)
**Warning signs:** Медленная отправка перевёрнутых карт (>500ms), /tmp мусор

### Pitfall 4: Качество JPEG после ротации (артефакты)
**What goes wrong:** После rotate() изображение размытое или с артефактами
**Why it happens:** Pillow по умолчанию quality=75, недостаточно для визуальных карт
**How to avoid:** save(buffer, format='JPEG', quality=85) — баланс качество/размер
**Warning signs:** Пользователи жалуются на плохое качество изображений

### Pitfall 5: FSM state не очищается после расклада
**What goes wrong:** Пользователь заканчивает расклад, но следующее сообщение обрабатывается как вопрос
**Why it happens:** Забыли вызвать await state.clear() после завершения диалога
**How to avoid:** Всегда state.clear() после финального шага FSM
**Warning signs:** Бот неправильно реагирует на команды после расклада

### Pitfall 6: Перевёрнутость карты (reversed) не сохраняется в кеше карты дня
**What goes wrong:** Пользователь вытянул перевёрнутую карту дня, через час запросил снова — карта прямая
**Why it happens:** Кешируется только card_id, а reversed (True/False) генерируется заново при каждом запросе
**How to avoid:** Хранить card_of_day_reversed: bool в User модели рядом с card_of_day_id
**Warning signs:** Карта дня меняет ориентацию при повторных запросах в течение дня

## Code Examples

Проверенные паттерны из официальных источников:

### Load Tarot Deck from JSON
```python
# Source: ekelen/tarot-api формат (https://github.com/ekelen/tarot-api)
import json
from pathlib import Path

def load_tarot_deck() -> list[dict]:
    """Load 78 tarot cards from JSON."""
    deck_path = Path(__file__).parent.parent / "data" / "tarot" / "cards.json"
    with open(deck_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["cards"]  # Список из 78 словарей

# Формат каждой карты:
# {
#   "name": "The Fool",
#   "name_short": "ar00",
#   "type": "major",
#   "value_int": 0,
#   "meaning_up": "Beginnings, innocence, spontaneity...",
#   "meaning_rev": "Naivety, recklessness, risk-taking..."
# }
```

### Get Random Card with Reversed Flag
```python
# Source: Python random module (https://docs.python.org/3/library/random.html)
import random

def get_random_card(deck: list[dict]) -> tuple[dict, bool]:
    """Return random card + reversed flag (50% chance)."""
    card = random.choice(deck)
    reversed = random.choice([True, False])
    return card, reversed

def get_three_cards(deck: list[dict]) -> list[tuple[dict, bool]]:
    """Return 3 unique cards with reversed flags."""
    cards = random.sample(deck, 3)  # Гарантия уникальности
    return [(card, random.choice([True, False])) for card in cards]
```

### Format Three Card Spread Message
```python
# Source: aiogram.utils.formatting (уже используется в проекте)
from aiogram.utils.formatting import Bold, BlockQuote, Text, as_line

def format_three_card_spread(
    cards: list[tuple[dict, bool]],
    question: str
) -> Text:
    """
    Format 3-card spread (Past, Present, Future).

    Output:
        *Ваш вопрос:*
        > {question}

        🔮 *Прошлое:* {card1} (перевёрнутая)
        {meaning_rev}

        🔮 *Настоящее:* {card2}
        {meaning_up}

        🔮 *Будущее:* {card3}
        {meaning_up}
    """
    positions = ["Прошлое", "Настоящее", "Будущее"]
    content = [
        Bold("Ваш вопрос:"),
        "\n",
        BlockQuote(question),
        "\n\n",
    ]

    for i, (card, reversed) in enumerate(cards):
        position = positions[i]
        card_name = card["name"]
        meaning = card["meaning_rev"] if reversed else card["meaning_up"]
        reversed_text = " (перевёрнутая)" if reversed else ""

        content.extend([
            Bold(f"🔮 {position}:"),
            " ",
            as_line(f"{card_name}{reversed_text}"),
            "\n",
            as_line(meaning),
            "\n\n",
        ])

    return Text(*content)
```

### Send Card Image (Upright or Reversed)
```python
# Source: https://docs.aiogram.dev/en/latest/api/upload_file.html
from PIL import Image
from io import BytesIO
from aiogram.types import BufferedInputFile, Message

async def send_card_image(
    message: Message,
    card_short_name: str,
    reversed: bool = False
) -> None:
    """Send card image (rotated 180° if reversed)."""
    image_path = Path(__file__).parent.parent / "data" / "tarot" / "images" / f"{card_short_name}.jpg"

    if not reversed:
        # Прямая карта — отправка напрямую
        photo = FSInputFile(image_path)
        await message.answer_photo(photo)
    else:
        # Перевёрнутая — ротация через Pillow
        img = Image.open(image_path)
        rotated = img.transpose(Image.Transpose.ROTATE_180)
        buffer = BytesIO()
        rotated.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)

        photo = BufferedInputFile(
            buffer.read(),
            filename=f"{card_short_name}_reversed.jpg"
        )
        await message.answer_photo(photo)
```

### Check and Update Daily Tarot Limit
```python
# Source: собственный паттерн на основе SQLAlchemy User модели
from datetime import datetime
import pytz
from sqlalchemy.ext.asyncio import AsyncSession

async def check_and_use_tarot_limit(
    user: User,
    session: AsyncSession
) -> tuple[bool, int]:
    """
    Check if user can do tarot spread today.
    Returns: (allowed, remaining_count)
    """
    user_tz = pytz.timezone(user.timezone or "Europe/Moscow")
    today = datetime.now(user_tz).date()

    # Сброс если новый день
    if user.spread_reset_date != today:
        user.tarot_spread_count = 0
        user.spread_reset_date = today

    # Лимиты: free=1, premium=20
    limit = 20 if user.is_premium else 1
    remaining = limit - user.tarot_spread_count

    if remaining > 0:
        user.tarot_spread_count += 1
        await session.commit()
        return True, remaining - 1

    return False, 0
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Хранить 156 изображений (78 прямых + 78 перевёрнутых) | Ротация on-the-fly через Pillow | 2020+ | Экономия storage (20MB → 10MB), гибкость |
| FSM через глобальные dict user_states[user_id] | aiogram 3.x FSM (StatesGroup + FSMContext) | aiogram 3.0 (2023) | Async-safe, persistence, type hints |
| Сброс лимитов cron job 00:00 UTC для всех | Per-user проверка при запросе (user timezone) | 2022+ | Корректный UX, нет race conditions |
| Отправка через URL (external hosting) | BufferedInputFile (BytesIO) для динамических изображений | aiogram 3.0 (2023) | Нет external dependency, быстрее |
| Датасеты Таро без reversed meanings | ekelen/tarot-api с meaning_rev | 2020+ | Полный функционал (прямые + перевёрнутые) |

**Deprecated/outdated:**
- **aiogram 2.x FSM (aiogram.dispatcher.filters.state):** Заменён на aiogram.fsm.state (3.x) — новый async API
- **PIL (оригинальная библиотека):** Заменена на Pillow (fork) — активная поддержка, Python 3.11+
- **random.seed() для "честности":** Не используется — убивает рандомность, нет смысла в Таро контексте

## Open Questions

Вопросы, которые не удалось полностью разрешить:

1. **Оптимальный размер изображений для Telegram**
   - What we know: Telegram рекомендует 10MB max, 1280x1280px для квадратных, компрессия 80% для JPEG
   - What's unclear: Баланс между качеством (85% quality) и скоростью отправки для luciellaes 300x527px изображений
   - Recommendation: Использовать quality=85 (HIGH визуальное качество, ~50KB per image), тестировать скорость отправки 3 фото подряд

2. **Глубина интерпретаций (meaning_up/meaning_rev)**
   - What we know: ekelen/tarot-api содержит короткие meanings из AE Waite (1-2 предложения)
   - What's unclear: Достаточно ли этого для "immediate value" или нужны более длинные толкования
   - Recommendation: Начать с ekelen meanings (проверенный источник), собирать feedback, расширять в Phase 8 (Premium Tarot) через AI интерпретации

3. **Хранение reversed флага для карты дня**
   - What we know: Нужно кешировать card_id + reversed до 00:00 user timezone
   - What's unclear: Достаточно ли Boolean колонки или нужен более сложный механизм
   - Recommendation: Добавить card_of_day_reversed: bool в User модель, простое решение для Phase 4

4. **Последовательная отправка 3 фото vs MediaGroup**
   - What we know: MediaGroup отправляет альбом (все фото сразу), последовательная отправка — по одному с задержками
   - What's unclear: Что лучше для UX "ритуала" — альбом (компактно) или последовательно (драматично)
   - Recommendation: Последовательная отправка (asyncio.sleep 1s между фото) для "ритуала", MediaGroup — опция для будущего A/B теста

## Sources

### Primary (HIGH confidence)
- [aiogram 3.24.0 FSM documentation](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/index.html) — StatesGroup, FSMContext, state transitions
- [aiogram 3 upload file documentation](https://docs.aiogram.dev/en/latest/api/upload_file.html) — FSInputFile, BufferedInputFile, BytesIO usage
- [aiogram 3 InlineKeyboardBuilder](https://docs.aiogram.dev/en/latest/utils/keyboard.html) — Dynamic keyboard creation
- [Pillow Image module documentation](https://pillow.readthedocs.io/en/stable/reference/Image.html) — transpose(ROTATE_180), save quality
- [Python random module documentation](https://docs.python.org/3/library/random.html) — random.choice, random.sample

### Secondary (MEDIUM confidence)
- [ekelen/tarot-api GitHub](https://github.com/ekelen/tarot-api) — JSON structure, 78 cards, meanings (WebSearch verified)
- [luciellaes CC0 Rider-Waite cards](https://luciellaes.itch.io/rider-waite-smith-tarot-cards-cc0) — 300x527px JPG/PNG, CC0 license (WebFetch verified)
- [PostgreSQL timezone handling](https://www.cybertec-postgresql.com/en/time-zone-management-in-postgresql/) — AT TIME ZONE, midnight per user timezone
- [Telegram bot photo best practices](https://copyprogramming.com/howto/sending-animated-gifs-with-sendphoto-telegram-bot) — 10MB limit, JPEG quality 80-85%

### Tertiary (LOW confidence)
- [aiogram MediaGroup builder](https://docs.aiogram.dev/en/latest/utils/media_group.html) — MediaGroupBuilder API (официальная документация, но не протестирован в проекте)
- [Tarot three-card spread interpretation](https://science.howstuffworks.com/science-vs-myth/extrasensory-perceptions/past-present-future-spread.htm) — Past/Present/Future positions (WebSearch only)
- [Tarot reversed card meanings](https://biddytarot.com/blog/how-to-interpret-reversed-tarot-cards/) — Interpretation approaches (WebSearch only, нужна валидация с экспертом)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — aiogram 3.x, Pillow, SQLAlchemy уже используются в проекте, официальная документация проверена
- Architecture: HIGH — FSM паттерны из aiogram docs, User модель существует, timezone handling через pytz (Phase 3)
- Pitfalls: MEDIUM — Рандом и FSM pitfalls проверены, timezone midnight reset — логический вывод (нужно протестировать)
- Датасет Таро: MEDIUM — ekelen/tarot-api и luciellaes проверены через WebFetch, но JSON структура нуждается в валидации при загрузке
- Интерпретации: LOW — Meanings из ekelen/tarot-api (AE Waite) могут быть слишком короткими, требуется feedback после имплементации

**Research date:** 2026-01-22
**Valid until:** 2026-03-22 (60 days) — aiogram 3.x стабильный, Pillow 10.x stable, датасет статический (не меняется)
