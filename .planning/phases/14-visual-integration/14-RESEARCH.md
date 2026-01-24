# Phase 14: Visual Integration - Research

**Researched:** 2026-01-24
**Domain:** Telegram Bot API file_id caching + aiogram 3.x photo handling
**Confidence:** HIGH

## Summary

Фаза 14 интегрирует 43 космических изображения (скачанных в Phase 13) в бота. Ключевая задача — кэширование `file_id` в PostgreSQL для мгновенной отправки без повторной загрузки файлов.

**Ключевые находки:**
- **file_id кэширование** — Telegram рекомендует сохранять file_id после первой загрузки и использовать его для всех последующих отправок. Мгновенная доставка без re-upload.
- **aiogram 3.x FSInputFile** — для первичной загрузки локальных файлов используется `FSInputFile(path)`. После отправки `message.photo[-1].file_id` содержит идентификатор для кэширования.
- **PostgreSQL image_assets таблица** — хранит mapping (asset_key -> file_id). Один раз загрузил — всегда используешь file_id.
- **Рандомная отправка** — 43 космических изображения отправляются случайным выбором при каждом ключевом событии (гороскоп, таро, натальная карта, welcome, paywall).

**Primary recommendation:** Создать ImageAssetService с PostgreSQL persistence. При первом запросе — загружать через FSInputFile и кэшировать file_id. При последующих — отправлять напрямую по file_id.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| aiogram | 3.24.0 | FSInputFile, send_photo, Message.photo | Уже используется в проекте |
| SQLAlchemy | 2.x | ImageAsset model, async session | Уже используется в проекте |
| PostgreSQL | - | file_id persistence | Уже используется для кэша |
| Pillow | 12.1.0 | Проверка валидности изображений (опционально) | Уже установлен |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib | stdlib | Работа с путями к изображениям | Всегда |
| random | stdlib | Выбор случайного изображения | Рандомная отправка |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PostgreSQL file_id cache | Redis | Добавляет зависимость, нет persistence бесплатно |
| FSInputFile | URLInputFile | Требует HTTP сервер для раздачи файлов |
| Random selection | Round-robin | Меньше разнообразия для одного пользователя |

**Installation:**
```bash
# Ничего нового не нужно!
# Все зависимости уже установлены
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── db/models/
│   └── image_asset.py         # ImageAsset model (NEW)
├── services/
│   └── image_asset.py         # ImageAssetService (NEW)
├── bot/handlers/
│   ├── start.py               # MODIFY: добавить welcome image
│   ├── horoscope.py           # MODIFY: добавить cosmic image
│   ├── tarot.py               # MODIFY: добавить cosmic image (для spread)
│   └── natal.py               # (уже отправляет PNG, можно добавить cosmic)
└── bot/utils/
    └── cosmic_images.py       # Helper для получения случайного изображения (NEW)

assets/
└── images/
    └── cosmic/                # 43 космических изображения (готово)
        ├── pexels-*.jpg
        └── ...

migrations/
└── versions/
    └── 2026_01_24_xxx_add_image_assets_table.py  # NEW
```

### Pattern 1: ImageAsset Model
**What:** SQLAlchemy model для хранения file_id
**When to use:** Любое изображение, которое нужно отправлять повторно
**Example:**
```python
# Source: Собственная реализация по паттерну HoroscopeCache

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from src.db.models.base import Base


class ImageAsset(Base):
    """Cached Telegram file_ids for images.

    After first upload, file_id is stored for instant re-sending.
    """

    __tablename__ = "image_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Unique key for the asset (e.g., "cosmic/pexels-abc-123.jpg")
    asset_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # Telegram file_id (returned after first upload)
    file_id: Mapped[str] = mapped_column(String(255))

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
    )
```

### Pattern 2: ImageAssetService (Singleton)
**What:** Сервис для отправки изображений с кэшированием file_id
**When to use:** Любая отправка изображения
**Example:**
```python
# Source: Паттерн из HoroscopeCacheService

import random
from pathlib import Path
from aiogram import Bot
from aiogram.types import FSInputFile, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.image_asset import ImageAsset


COSMIC_IMAGES_DIR = Path("assets/images/cosmic")


class ImageAssetService:
    """Service for sending images with file_id caching."""

    _instance: "ImageAssetService | None" = None
    _cosmic_images: list[str] | None = None

    def __init__(self) -> None:
        """Initialize and load cosmic image paths."""
        self._load_cosmic_images()

    def _load_cosmic_images(self) -> None:
        """Load list of cosmic image filenames."""
        if COSMIC_IMAGES_DIR.exists():
            self._cosmic_images = [
                f.name for f in COSMIC_IMAGES_DIR.glob("*.jpg")
            ]
        else:
            self._cosmic_images = []

    def get_random_cosmic_key(self) -> str | None:
        """Get random cosmic image asset key."""
        if not self._cosmic_images:
            return None
        filename = random.choice(self._cosmic_images)
        return f"cosmic/{filename}"

    async def send_image(
        self,
        bot: Bot,
        chat_id: int,
        asset_key: str,
        session: AsyncSession,
        caption: str | None = None,
        reply_markup=None,
    ) -> Message | None:
        """Send image using cached file_id or upload and cache.

        Args:
            bot: Telegram Bot instance
            chat_id: Target chat ID
            asset_key: Unique key (e.g., "cosmic/pexels-abc.jpg")
            session: Database session
            caption: Optional photo caption
            reply_markup: Optional keyboard

        Returns:
            Sent Message or None on error
        """
        # Check cache
        stmt = select(ImageAsset).where(ImageAsset.asset_key == asset_key)
        result = await session.execute(stmt)
        cached = result.scalar_one_or_none()

        if cached:
            # Cache hit - send by file_id (instant)
            return await bot.send_photo(
                chat_id=chat_id,
                photo=cached.file_id,
                caption=caption,
                reply_markup=reply_markup,
            )

        # Cache miss - upload file and cache file_id
        file_path = Path("assets/images") / asset_key
        if not file_path.exists():
            return None

        message = await bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(file_path),
            caption=caption,
            reply_markup=reply_markup,
        )

        # Extract file_id from response and cache
        if message.photo:
            file_id = message.photo[-1].file_id  # Largest size

            asset = ImageAsset(
                asset_key=asset_key,
                file_id=file_id,
            )
            session.add(asset)
            await session.commit()

        return message

    async def send_random_cosmic(
        self,
        bot: Bot,
        chat_id: int,
        session: AsyncSession,
        caption: str | None = None,
        reply_markup=None,
    ) -> Message | None:
        """Send random cosmic image."""
        asset_key = self.get_random_cosmic_key()
        if not asset_key:
            return None

        return await self.send_image(
            bot=bot,
            chat_id=chat_id,
            asset_key=asset_key,
            session=session,
            caption=caption,
            reply_markup=reply_markup,
        )


# Singleton
_instance: ImageAssetService | None = None


def get_image_asset_service() -> ImageAssetService:
    """Get image asset service singleton."""
    global _instance
    if _instance is None:
        _instance = ImageAssetService()
    return _instance
```

### Pattern 3: Integration in Handler
**What:** Использование ImageAssetService в handler'ах
**When to use:** Любой handler, где нужно отправить изображение
**Example:**
```python
# Source: Паттерн интеграции

from aiogram import Bot, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.image_asset import get_image_asset_service

router = Router(name="start")

@router.message(Command("start"))
async def cmd_start(
    message: Message,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """Handle /start with welcome image."""
    image_service = get_image_asset_service()

    # Send random cosmic image as welcome
    await image_service.send_random_cosmic(
        bot=bot,
        chat_id=message.chat.id,
        session=session,
    )

    # Then send welcome text
    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=get_start_keyboard(),
    )
```

### Anti-Patterns to Avoid
- **Re-uploading every time:** Никогда не загружать файл повторно через FSInputFile если file_id уже есть
- **Global file_id across bots:** file_id уникален для каждого бота, нельзя использовать между разными ботами
- **Storing in memory only:** file_id должен persist в БД, иначе после рестарта всё перезагрузится
- **Ignoring Message.photo order:** Последний элемент `message.photo[-1]` — максимальное разрешение

## Telegram file_id Details

### file_id Characteristics
| Property | Value | Notes |
|----------|-------|-------|
| Уникальность | Per-bot | Нельзя использовать между ботами |
| Время жизни | Бессрочно | Не истекает для фото |
| Формат | String | ~100 символов |
| Размер | - | Telegram хранит несколько размеров, отправляет все |

### Message.photo Structure
```python
# После отправки фото, message.photo содержит список PhotoSize:
[
    PhotoSize(file_id="...", width=90, height=51),    # Thumbnail
    PhotoSize(file_id="...", width=320, height=180),  # Small
    PhotoSize(file_id="...", width=800, height=450),  # Medium
    PhotoSize(file_id="...", width=1280, height=720), # Large (наш target)
]

# Используем последний (самый большой):
file_id = message.photo[-1].file_id
```

### Sending by file_id
```python
# Мгновенная отправка (рекомендуется Telegram):
await bot.send_photo(chat_id=chat_id, photo="AgACAgIAAxk...")

# vs загрузка файла (медленно, трафик):
await bot.send_photo(chat_id=chat_id, photo=FSInputFile("path/to/file.jpg"))
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| file_id storage | In-memory dict | PostgreSQL ImageAsset | Persistence after restart |
| Random image selection | Complex algorithm | `random.choice(list)` | Simple, sufficient |
| Image upload | Manual HTTP | FSInputFile | aiogram handles multipart |
| file_id extraction | Parse response manually | `message.photo[-1].file_id` | Standard pattern |

**Key insight:** Telegram делает всё сложное (хранение, CDN, resize). Нам нужно только сохранить file_id и использовать его.

## Common Pitfalls

### Pitfall 1: Потеря file_id после рестарта
**What goes wrong:** После рестарта бота все изображения загружаются заново
**Why it happens:** file_id хранится только в памяти
**How to avoid:** PostgreSQL persistence через ImageAsset model
**Warning signs:** Медленная отправка фото после каждого деплоя

### Pitfall 2: Использование file_id другого бота
**What goes wrong:** Ошибка "Bad Request: wrong file identifier"
**Why it happens:** file_id уникален для каждого бота
**How to avoid:** Кэшировать file_id только для текущего бота
**Warning signs:** Ошибки 400 при отправке фото

### Pitfall 3: Отправка message.photo[0] вместо [-1]
**What goes wrong:** Получатель видит размытое thumbnail
**Why it happens:** photo[0] — минимальный размер
**How to avoid:** Всегда `message.photo[-1]` для максимального качества
**Warning signs:** Жалобы на качество изображений

### Pitfall 4: Блокирующая загрузка при cache miss
**What goes wrong:** Пользователь долго ждёт первое изображение
**Why it happens:** FSInputFile загрузка занимает 1-3 секунды
**How to avoid:** Предзагрузка: отправить все 43 изображения в тестовый чат при старте
**Warning signs:** Первые пользователи ждут дольше

### Pitfall 5: Отсутствие fallback при ошибке
**What goes wrong:** Handler падает если изображение не найдено
**Why it happens:** Нет проверки существования файла
**How to avoid:** `send_image` возвращает None при ошибке, handler проверяет
**Warning signs:** 500 ошибки при отправке фото

## Onboarding Tutorial Options

### Option A: Простые сообщения с фото (Рекомендуется)
**Плюсы:** Нативно, просто, работает везде
**Минусы:** Нет swipe/carousel
**Implementation:**
```python
# Серия сообщений с изображениями
await image_service.send_image(bot, chat_id, "onboarding/step1.jpg", session)
await message.answer("Шаг 1: Введи дату рождения")
await image_service.send_image(bot, chat_id, "onboarding/step2.jpg", session)
await message.answer("Шаг 2: Получай ежедневный гороскоп")
```

### Option B: Telegram Mini App с carousel
**Плюсы:** Красивый UI, swipe
**Минусы:** Требует отдельный фронтенд (Vue/React), деплой
**Not recommended:** Слишком сложно для MVP

### Рекомендация
Для v2.0 использовать Option A — простые сообщения с космическими изображениями. Onboarding через FSM уже работает в start.py, нужно только добавить изображения.

## Integration Points

### 1. /start (Welcome)
**Текущее состояние:** Текстовое сообщение WELCOME_MESSAGE
**Изменение:** Добавить космическое изображение перед текстом
**Где:** `src/bot/handlers/start.py` -> `cmd_start()`

### 2. Гороскоп
**Текущее состояние:** Только текст
**Изменение:** Добавить космическое изображение перед текстом гороскопа
**Где:** `src/bot/handlers/horoscope.py` -> `show_horoscope_message()`, `show_zodiac_horoscope()`

### 3. Таро (3-card spread)
**Текущее состояние:** Карты отправляются как фото
**Изменение:** Добавить космическое изображение перед раскладом (опционально)
**Где:** `src/bot/handlers/tarot.py` -> `tarot_draw_three_cards()`

### 4. Натальная карта
**Текущее состояние:** PNG натальной карты отправляется как фото
**Изменение:** Можно добавить космическое изображение перед (опционально, не обязательно)
**Где:** `src/bot/handlers/natal.py` -> `show_natal_chart()`

### 5. Paywall
**Текущее состояние:** Текстовый teaser в гороскопе
**Изменение:** Можно добавить изображение при показе premium offer
**Где:** Несколько мест (subscription keyboards)

## Code Examples

### Migration: Add image_assets table
```python
# migrations/versions/2026_01_24_xxx_add_image_assets_table.py

def upgrade() -> None:
    """Create image_assets table."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS image_assets (
            id SERIAL PRIMARY KEY,
            asset_key VARCHAR(255) NOT NULL UNIQUE,
            file_id VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_image_assets_asset_key
        ON image_assets (asset_key)
    """)


def downgrade() -> None:
    """Drop image_assets table."""
    op.execute("DROP TABLE IF EXISTS image_assets CASCADE")
```

### Getting Bot instance in handler
```python
# aiogram 3.x: Bot доступен через контекст или параметр

from aiogram import Bot, Router
from aiogram.types import Message

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, bot: Bot, session: AsyncSession) -> None:
    # bot автоматически inject'ится aiogram'ом
    await bot.send_photo(chat_id=message.chat.id, photo="file_id_here")
```

### Pre-warming cache (опционально)
```python
# При старте бота — отправить все изображения в тестовый чат для кэширования
# Не обязательно для MVP, но ускоряет первых пользователей

async def prewarm_image_cache(bot: Bot, test_chat_id: int, session: AsyncSession):
    """Upload all images to cache file_ids before users arrive."""
    service = get_image_asset_service()

    for filename in service._cosmic_images:
        asset_key = f"cosmic/{filename}"

        # Check if already cached
        stmt = select(ImageAsset).where(ImageAsset.asset_key == asset_key)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            continue

        # Upload and cache
        await service.send_image(
            bot=bot,
            chat_id=test_chat_id,
            asset_key=asset_key,
            session=session,
        )
        await asyncio.sleep(0.5)  # Rate limit safety
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Re-upload every time | Cache file_id | Telegram Bot API 2.0 | Мгновенная отправка |
| Memory cache | PostgreSQL persistence | Best practice | Survive restarts |
| InputFile for all | FSInputFile для локальных | aiogram 3.x | Type safety |

**Deprecated/outdated:**
- `aiogram.types.InputFile`: Заменён на FSInputFile, URLInputFile, BufferedInputFile в aiogram 3.x

## Open Questions

### 1. Предзагрузка кэша
- **What we know:** Первая отправка каждого изображения занимает 1-3 секунды
- **What's unclear:** Нужно ли делать pre-warm при старте?
- **Recommendation:** Для 43 изображений — нет, lazy loading достаточно. Через несколько дней все file_id будут в кэше.

### 2. Изображения в git vs external storage
- **What we know:** 43 файла x ~500KB = ~20MB в репозитории
- **What's unclear:** Не слишком ли много для git?
- **Recommendation:** Для MVP — OK. Если вырастет до 500+ изображений, мигрировать на S3.

### 3. Разные изображения для разных событий
- **What we know:** Сейчас 43 общих космических изображения
- **What's unclear:** Нужны ли отдельные изображения для welcome, paywall?
- **Recommendation:** Для v2.0 — одни и те же космические. Специфические (если нужны) — в v3.0.

## Sources

### Primary (HIGH confidence)
- [Telegram Bot API - Sending Files](https://core.telegram.org/bots/api#sending-files) - file_id behavior, caching recommendations
- [aiogram 3.24.0 - send_photo](https://docs.aiogram.dev/en/dev-3.x/api/methods/send_photo.html) - Method signature
- [aiogram 3.24.0 - Upload File](https://docs.aiogram.dev/en/dev-3.x/api/upload_file.html) - FSInputFile usage

### Secondary (MEDIUM confidence)
- [aiogram GitHub Discussion #1393](https://github.com/aiogram/aiogram/discussions/1393) - file_id reuse patterns
- Phase 12 HoroscopeCacheService - Паттерн PostgreSQL persistence

### Tertiary (LOW confidence)
- [telegram-onboarding-kit](https://github.com/Easterok/telegram-onboarding-kit) - Onboarding UI patterns (Mini App)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Всё уже используется в проекте
- Architecture: HIGH - Паттерн из HoroscopeCacheService
- Pitfalls: HIGH - Официальная документация Telegram
- Onboarding: MEDIUM - Несколько подходов, выбрали простой

**Research date:** 2026-01-24
**Valid until:** 60 дней (Telegram API стабилен, aiogram редко меняется)

---

## Summary Table: What to Build

| Component | Type | Effort | Priority |
|-----------|------|--------|----------|
| `ImageAsset` model | New file | 30 min | P0 |
| Migration | New file | 15 min | P0 |
| `ImageAssetService` | New file | 1 hour | P0 |
| Update `start.py` | Modify | 30 min | P0 |
| Update `horoscope.py` | Modify | 30 min | P1 |
| Update `tarot.py` | Modify | 30 min | P2 |
| Update `models/__init__.py` | Modify | 5 min | P0 |

**Total estimated effort:** 3-4 часа
