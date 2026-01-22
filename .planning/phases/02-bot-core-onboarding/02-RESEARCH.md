# Phase 2: Bot Core + Onboarding - Research

**Researched:** 2026-01-22
**Domain:** Telegram Bot (aiogram 3.x) + FastAPI webhook + FSM onboarding
**Confidence:** HIGH

## Summary

Исследование покрывает интеграцию aiogram 3.24.0 с FastAPI для webhook-based Telegram бота, FSM для onboarding flow, парсинг дат на русском языке, и определение знака зодиака.

**Ключевые находки:**
1. aiogram 3.x НЕ имеет встроенной FastAPI интеграции — нужна ручная реализация через `Dispatcher.feed_update()`
2. FSM в aiogram 3.x использует `StatesGroup`, `State`, `FSMContext` — MemoryStorage для MVP достаточно
3. `dateparser` библиотека отлично парсит русские даты ("15 марта 1990") из коробки
4. Знак зодиака проще вычислить самостоятельно (20 строк кода) чем тянуть библиотеку

**Primary recommendation:** Использовать aiogram 3.24.0 + FastAPI lifespan для webhook, MemoryStorage для FSM (достаточно для onboarding), dateparser для парсинга дат.

## Standard Stack

Установленные библиотеки для этой фазы:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| aiogram | 3.24.0 | Telegram Bot framework | De-facto стандарт для async Python ботов, Bot API 9.3 |
| dateparser | 1.2.2 | Парсинг дат на русском | 200+ локалей, отличная поддержка русского |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| redis (optional) | latest | FSM storage для production | Когда нужна персистентность state между рестартами |

### Уже установлено (из Phase 1)

| Library | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.128.0 | Web framework для webhook |
| SQLAlchemy | 2.0.46+ | Async ORM |
| asyncpg | 0.31.0 | PostgreSQL driver |
| pydantic-settings | 2.7.1 | Configuration |
| structlog | 25.5.0 | Logging |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| MemoryStorage | RedisStorage | Redis требует доп. сервис; для onboarding (1-2 шага) MemoryStorage достаточно |
| dateparser | datetime.strptime | strptime не парсит "15 марта 1990", нужен manual mapping месяцев |
| custom zodiac | kerykeion | kerykeion слишком тяжёлый для простого определения знака |

**Installation:**
```bash
poetry add aiogram dateparser
```

## Architecture Patterns

### Recommended Project Structure

```
src/
├── bot/                    # Telegram bot module
│   ├── __init__.py
│   ├── bot.py              # Bot and Dispatcher instances
│   ├── handlers/           # Route handlers
│   │   ├── __init__.py
│   │   ├── start.py        # /start command, onboarding
│   │   ├── menu.py         # Menu button handlers
│   │   └── common.py       # Common handlers (errors, unknown)
│   ├── states/             # FSM states
│   │   ├── __init__.py
│   │   └── onboarding.py   # Onboarding states
│   ├── keyboards/          # Keyboard builders
│   │   ├── __init__.py
│   │   └── main_menu.py    # Reply keyboard
│   ├── middlewares/        # Middleware
│   │   ├── __init__.py
│   │   └── db.py           # Database session injection
│   └── utils/              # Utilities
│       ├── __init__.py
│       ├── zodiac.py       # Zodiac calculation
│       └── date_parser.py  # Date parsing wrapper
├── main.py                 # FastAPI app + webhook route
└── config.py               # Add TELEGRAM_BOT_TOKEN, WEBHOOK_URL
```

### Pattern 1: FastAPI + aiogram Webhook Integration

**What:** Интеграция aiogram с FastAPI через lifespan events и webhook endpoint

**When to use:** Всегда для production Telegram ботов на Railway/Render/etc

**Example:**
```python
# Source: https://docs.aiogram.dev/en/latest/dispatcher/webhook.html
# + https://fastapi.tiangolo.com/advanced/events/
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from aiogram import Bot, Dispatcher
from aiogram.types import Update

bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: set webhook
    webhook_url = f"{settings.webhook_base_url}/webhook"
    await bot.set_webhook(
        url=webhook_url,
        secret_token=settings.webhook_secret,
        drop_pending_updates=True,
    )
    yield
    # Shutdown: delete webhook, close bot session
    await bot.delete_webhook()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def webhook(request: Request) -> Response:
    # Validate secret token
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != settings.webhook_secret:
        return Response(status_code=401)

    # Process update
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return Response(status_code=200)
```

### Pattern 2: FSM Onboarding Flow

**What:** Finite State Machine для сбора данных при регистрации

**When to use:** Для multi-step диалогов (сбор даты рождения)

**Example:**
```python
# Source: https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/index.html
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class OnboardingStates(StatesGroup):
    waiting_birthdate = State()

# Handler: start onboarding
@router.callback_query(F.data == "get_first_forecast")
async def start_onboarding(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введи дату рождения:")
    await state.set_state(OnboardingStates.waiting_birthdate)

# Handler: receive birthdate
@router.message(OnboardingStates.waiting_birthdate)
async def process_birthdate(message: Message, state: FSMContext, session: AsyncSession):
    parsed_date = parse_russian_date(message.text)
    if not parsed_date:
        await message.answer("Неверный формат. Попробуй ещё раз")
        return

    zodiac = get_zodiac_sign(parsed_date)
    # Save to DB, clear state, show result
    await state.clear()
    await message.answer(f"Твой знак: {zodiac.emoji} {zodiac.name}")
```

### Pattern 3: Router Organization

**What:** Модульная организация handlers через роутеры

**When to use:** Всегда для maintainable кода

**Example:**
```python
# Source: https://docs.aiogram.dev/en/latest/dispatcher/router.html
from aiogram import Router, Dispatcher

# handlers/start.py
start_router = Router(name="start")

@start_router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession):
    ...

# bot.py - connecting routers
dp = Dispatcher()
dp.include_routers(start_router, menu_router, common_router)
```

### Pattern 4: Database Session Middleware

**What:** Инъекция AsyncSession в handlers через middleware

**When to use:** Для доступа к БД в handlers

**Example:**
```python
# Source: https://github.com/MasterGroosha/aiogram-and-sqlalchemy-demo
from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker

class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool

    async def __call__(self, handler, event, data: dict):
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)

# Registration
dp.update.middleware(DbSessionMiddleware(session_pool=AsyncSessionLocal))
```

### Pattern 5: Reply Keyboard 2x2

**What:** Главное меню с 4 кнопками в сетке 2x2

**When to use:** Для постоянного меню внизу экрана

**Example:**
```python
# Source: https://docs.aiogram.dev/en/latest/utils/keyboard.html
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Гороскоп")
    builder.button(text="Таро")
    builder.button(text="Подписка")
    builder.button(text="Профиль")
    builder.adjust(2)  # 2 buttons per row = 2x2 grid
    return builder.as_markup(resize_keyboard=True)
```

### Anti-Patterns to Avoid

- **Polling вместо Webhook:** Polling не работает на serverless/Railway — только webhook
- **Глобальный Bot instance без cleanup:** Всегда закрывать `bot.session.close()` при shutdown
- **Handlers без state validation:** Проверять state перед обработкой, graceful handling если state потерян
- **Синхронные операции в handlers:** Все handlers должны быть async

## Don't Hand-Roll

Проблемы, которые выглядят просто, но имеют готовые решения:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Парсинг дат на русском | Manual regex + month mapping | `dateparser.parse()` | 200+ локалей, edge cases, "вчера", "через неделю" |
| Keyboard builders | Manual dict construction | `ReplyKeyboardBuilder`, `InlineKeyboardBuilder` | Type-safe, fluent API, adjust() |
| FSM state management | Custom state dict | aiogram FSM (StatesGroup, FSMContext) | Integrated with handlers, storage backends |
| Webhook validation | Manual header parsing | `X-Telegram-Bot-Api-Secret-Token` header | Telegram's official mechanism |

**Key insight:** aiogram 3.x имеет мощные built-in абстракции — используй их вместо изобретения велосипеда.

## Common Pitfalls

### Pitfall 1: Webhook не получает updates

**What goes wrong:** Бот deployed, но не реагирует на сообщения
**Why it happens:**
- Webhook URL неправильный (http вместо https)
- Secret token не совпадает
- Не вызван `set_webhook()` при startup
**How to avoid:**
- Использовать HTTPS URL
- Проверять secret token в каждом request
- Логировать webhook registration при startup
**Warning signs:** `getWebhookInfo` показывает `pending_update_count > 0`

### Pitfall 2: FSM state потерян после restart

**What goes wrong:** Пользователь в середине onboarding, бот рестартнулся, state потерян
**Why it happens:** MemoryStorage не персистентный
**How to avoid:**
- Для MVP: accept this limitation — onboarding короткий (1 шаг)
- Для production: использовать RedisStorage
- Всегда handle "unknown state" gracefully
**Warning signs:** Пользователи жалуются что "бот забыл" их

### Pitfall 3: Неправильный парсинг даты

**What goes wrong:** "1990" парсится как "1990-01-01", а не ошибка
**Why it happens:** dateparser слишком умный, пытается парсить всё
**How to avoid:**
```python
from dateparser import parse

def parse_russian_date(text: str):
    result = parse(text, languages=['ru'], settings={
        'STRICT_PARSING': True,
        'REQUIRE_PARTS': ['day', 'month', 'year'],
    })
    # Additional validation: year in reasonable range
    if result and 1900 <= result.year <= 2020:
        return result
    return None
```
**Warning signs:** Тесты проходят, но реальные пользователи вводят странные даты

### Pitfall 4: Bot session не закрыт

**What goes wrong:** Memory leaks, unclosed connections при shutdown
**Why it happens:** Забыли вызвать `bot.session.close()`
**How to avoid:** Всегда закрывать в lifespan shutdown:
```python
yield  # after yield = shutdown
await bot.delete_webhook()
await bot.session.close()
```
**Warning signs:** ResourceWarning в логах

### Pitfall 5: Handlers registered after startup

**What goes wrong:** Некоторые handlers не работают
**Why it happens:** Роутеры включены после `dp.start_polling()` или webhook start
**How to avoid:** Все роутеры должны быть included ДО startup
**Warning signs:** Handler работает в tests но не в production

## Code Examples

### Zodiac Calculation (custom, no library needed)

```python
# Source: Standard Western astrology dates
from datetime import date
from dataclasses import dataclass

@dataclass
class ZodiacSign:
    name: str
    emoji: str
    name_ru: str

ZODIAC_SIGNS = [
    ZodiacSign("Capricorn", "Козерог"),
    ZodiacSign("Aquarius", "Водолей"),
    ZodiacSign("Pisces", "Рыбы"),
    ZodiacSign("Aries", "Овен"),
    ZodiacSign("Taurus", "Телец"),
    ZodiacSign("Gemini", "Близнецы"),
    ZodiacSign("Cancer", "Рак"),
    ZodiacSign("Leo", "Лев"),
    ZodiacSign("Virgo", "Дева"),
    ZodiacSign("Libra", "Весы"),
    ZodiacSign("Scorpio", "Скорпион"),
    ZodiacSign("Sagittarius", "Стрелец"),
]

# Day of year boundaries for each sign (approximate)
ZODIAC_DATES = [
    (1, 20), (2, 19), (3, 21), (4, 20), (5, 21), (6, 21),
    (7, 23), (8, 23), (9, 23), (10, 23), (11, 22), (12, 22),
]

def get_zodiac_sign(birth_date: date) -> ZodiacSign:
    month, day = birth_date.month, birth_date.day
    # Find zodiac index based on date
    for i, (m, d) in enumerate(ZODIAC_DATES):
        if (month == m and day < d) or (month == m - 1 and day >= ZODIAC_DATES[i-1][1]):
            return ZODIAC_SIGNS[(i - 1) % 12]
    return ZODIAC_SIGNS[11]  # Sagittarius as fallback
```

**Note:** Вычисление знака зодиака тривиальное — 20 строк кода. Не нужна библиотека.

### Date Parsing with Validation

```python
# Source: https://dateparser.readthedocs.io/en/latest/
import dateparser
from datetime import date

def parse_russian_date(text: str) -> date | None:
    """
    Parse Russian date string to date object.
    Accepts: "15.03.1990", "15/03/1990", "15 марта 1990", "1990-03-15"
    Returns None if parsing fails or date is invalid.
    """
    result = dateparser.parse(
        text,
        languages=['ru'],
        settings={
            'DATE_ORDER': 'DMY',
            'PREFER_DAY_OF_MONTH': 'first',
        }
    )

    if result is None:
        return None

    # Validate year range (reasonable birth years)
    if not (1900 <= result.year <= date.today().year - 10):
        return None

    return result.date()
```

### Complete Onboarding Handler

```python
# handlers/start.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.bot.states.onboarding import OnboardingStates
from src.bot.keyboards.main_menu import get_main_menu_keyboard, get_start_keyboard
from src.bot.utils.date_parser import parse_russian_date
from src.bot.utils.zodiac import get_zodiac_sign
from src.db.models import User

router = Router(name="start")

@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession):
    """Handle /start command."""
    # Check if user exists
    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user and user.birth_date:
        # Returning user - show menu directly
        await message.answer(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # New user - show welcome + onboarding button
        welcome_text = (
            "Привет! Я астробот.\n\n"
            "Составляю персональные гороскопы и расклады таро "
            "с AI-интерпретацией.\n\n"
            "Базовые функции бесплатны. "
            "Премиум даёт доступ к расширенным прогнозам."
        )
        await message.answer(
            welcome_text,
            reply_markup=get_start_keyboard()
        )

@router.callback_query(F.data == "get_first_forecast")
async def start_onboarding(callback: CallbackQuery, state: FSMContext):
    """Start birthdate collection."""
    await callback.message.answer("Введи дату рождения:")
    await state.set_state(OnboardingStates.waiting_birthdate)
    await callback.answer()

@router.message(OnboardingStates.waiting_birthdate)
async def process_birthdate(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Process birthdate input."""
    parsed_date = parse_russian_date(message.text)

    if not parsed_date:
        await message.answer("Неверный формат. Попробуй ещё раз")
        return

    zodiac = get_zodiac_sign(parsed_date)

    # Update or create user
    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        session.add(user)

    user.birth_date = parsed_date
    user.zodiac_sign = zodiac.name
    await session.commit()

    # Clear FSM state
    await state.clear()

    # Show zodiac + immediate value
    await message.answer(f"Твой знак: {zodiac.emoji} {zodiac.name_ru}")

    # Show horoscope (mock for Phase 2)
    horoscope_text = get_mock_horoscope(zodiac.name)
    await message.answer(horoscope_text)

    # Teaser + main menu
    await message.answer(
        "Хочешь карту дня? Нажми 'Таро'",
        reply_markup=get_main_menu_keyboard()
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| aiogram 2.x polling | aiogram 3.x webhook | 2023 | Полностью другой API, asyncio native |
| @dp.message_handler | @router.message() | aiogram 3.0 | Роутеры вместо глобального dispatcher |
| storage=MemoryStorage() в Dispatcher | Dispatcher(storage=storage) | aiogram 3.0 | Отдельный параметр |
| on_startup, on_shutdown | FastAPI lifespan | FastAPI 0.95+ | Cleaner async context |

**Deprecated/outdated:**
- aiogram 2.x API: Полностью несовместим с 3.x
- `@dp.message_handler()`: Заменён на `@router.message()`
- `Dispatcher(bot, storage=...)`: В 3.x bot передаётся в `dp.feed_update(bot, update)`

## Open Questions

1. **Источник гороскопа для immediate value**
   - What we know: Нужен гороскоп сразу после регистрации
   - What's unclear: Mock, external API, или AI-generated?
   - Recommendation: Для Phase 2 использовать hardcoded/mock тексты (12 текстов на каждый знак). AI integration в Phase 3.

2. **Поведение кнопок "Гороскоп" и "Таро" в Phase 2**
   - What we know: Меню должно быть
   - What's unclear: Показывать функционал или teaser?
   - Recommendation: "Гороскоп" — показать mock/hardcoded гороскоп. "Таро" — teaser "Скоро будет доступно".

3. **RedisStorage vs MemoryStorage**
   - What we know: MemoryStorage теряет state при restart
   - What's unclear: Критично ли для onboarding?
   - Recommendation: MemoryStorage для MVP. Onboarding = 1 шаг, если restart — пользователь просто введёт дату заново.

## Sources

### Primary (HIGH confidence)
- [aiogram 3.24.0 PyPI](https://pypi.org/project/aiogram/) - Version, dependencies
- [aiogram Webhook Documentation](https://docs.aiogram.dev/en/latest/dispatcher/webhook.html) - FastAPI integration pattern
- [aiogram FSM Documentation](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/index.html) - StatesGroup, FSMContext
- [aiogram Router Documentation](https://docs.aiogram.dev/en/latest/dispatcher/router.html) - Handler organization
- [aiogram Errors Documentation](https://docs.aiogram.dev/en/latest/dispatcher/errors.html) - Error handling
- [aiogram Storages Documentation](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/storages.html) - MemoryStorage, RedisStorage
- [dateparser 1.2.2 Documentation](https://dateparser.readthedocs.io/en/latest/) - Russian date parsing
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/) - Startup/shutdown pattern

### Secondary (MEDIUM confidence)
- [aiogram-webhook-template GitHub](https://github.com/QuvonchbekBobojonov/aiogram-webhook-template) - FastAPI+aiogram structure
- [MasterGroosha aiogram-and-sqlalchemy-demo](https://github.com/MasterGroosha/aiogram-and-sqlalchemy-demo) - DB middleware pattern
- [Telegram Bot API - setWebhook](https://core.telegram.org/bots/api#setwebhook) - Secret token validation

### Tertiary (LOW confidence)
- WebSearch results about best practices (need validation with actual implementation)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official documentation verified
- Architecture: HIGH - Multiple authoritative sources agree
- Pitfalls: MEDIUM - Based on documentation + community patterns
- Code examples: HIGH - Adapted from official docs

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (aiogram updates frequently, check for new major versions)

---

## DB Schema Updates Needed

User model нужно расширить для хранения даты рождения и знака:

```python
# src/db/models/user.py - additions
from sqlalchemy import Date, String

class User(Base):
    # ... existing fields ...
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    zodiac_sign: Mapped[str | None] = mapped_column(String(20), nullable=True)
```

Migration needed после изменения модели.

## Config Updates Needed

```python
# src/config.py - additions
class Settings(BaseSettings):
    # ... existing ...

    # Telegram Bot
    telegram_bot_token: str = Field(validation_alias="TELEGRAM_BOT_TOKEN")
    webhook_base_url: str = Field(validation_alias="WEBHOOK_BASE_URL")  # e.g. https://adtrobot-production.up.railway.app
    webhook_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
```

Environment variables на Railway:
- `TELEGRAM_BOT_TOKEN` — от @BotFather
- `WEBHOOK_BASE_URL` — Railway public URL
