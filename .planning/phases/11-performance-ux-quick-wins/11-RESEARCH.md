# Phase 11: Performance & UX Quick Wins - Research

**Researched:** 2026-01-23
**Domain:** aiogram UX patterns (typing indicators, message formatting, feedback loops)
**Confidence:** HIGH

## Summary

Phase 11 фокусируется на UX улучшениях без новых зависимостей: typing indicators во время AI генерации, правильное Markdown форматирование, и понятное разделение общего/персонального гороскопа.

**Ключевые находки:**
- aiogram 3.20+ имеет встроенный `ChatActionSender` для автоматического typing indicator
- Entity-based formatting (Text, Bold, etc.) уже используется в проекте - это правильный подход
- Промежуточные сообщения удаляются через `message.delete()` после получения результата
- BotFather description настраивается через `/setdescription` (512 символов) и `/setabouttext` (120 символов)

**Primary recommendation:** Использовать `ChatActionSender.typing()` как async context manager вокруг AI генерации, сохранить entity-based formatting, добавить промежуточные сообщения с эмодзи.

## Standard Stack

### Core (уже в проекте)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| aiogram | 3.20+ | Telegram Bot API | Async, ChatActionSender, entity-based formatting |

### Supporting (встроено в aiogram)
| Component | Module | Purpose | When to Use |
|-----------|--------|---------|-------------|
| ChatActionSender | aiogram.utils.chat_action | Auto-repeat typing | Долгие операции (AI) |
| Text, Bold, Italic | aiogram.utils.formatting | Entity-based formatting | Все сообщения |
| Message.delete() | aiogram.types | Удаление сообщений | Промежуточные сообщения |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ChatActionSender | Manual asyncio loop | Больше кода, возможны баги |
| Entity formatting | parse_mode=MarkdownV2 | Нужно экранировать спецсимволы |
| Entity formatting | parse_mode=HTML | Нужно экранировать < > & |

**Note:** Entity-based formatting уже используется в проекте (`src/bot/utils/formatting.py`, `src/bot/utils/tarot_formatting.py`). Не менять подход.

## Architecture Patterns

### Pattern 1: Typing Indicator для AI генерации
**What:** Async context manager показывает "typing..." пока AI генерирует ответ
**When to use:** Гороскоп (AI), Таро расклад (AI), Натальная карта (AI)

```python
# Source: https://docs.aiogram.dev/en/latest/utils/chat_action.html
from aiogram.utils.chat_action import ChatActionSender

async def generate_with_typing(message: Message, ai_operation: Coroutine) -> str:
    """Run AI operation with typing indicator."""
    async with ChatActionSender.typing(
        bot=message.bot,
        chat_id=message.chat.id,
        interval=4.0,  # Telegram typing lasts ~5 sec, refresh every 4
    ):
        return await ai_operation
```

### Pattern 2: Промежуточное сообщение + удаление
**What:** Показать сообщение "Генерирую...", удалить после получения результата
**When to use:** Вместе с typing indicator для явного feedback

```python
async def show_with_progress(message: Message, ai_coro: Coroutine, progress_text: str) -> str:
    """Show progress message during AI generation, delete after."""
    progress_msg = await message.answer(progress_text)

    async with ChatActionSender.typing(bot=message.bot, chat_id=message.chat.id):
        result = await ai_coro

    # Delete progress message (clean chat history)
    await progress_msg.delete()
    return result
```

### Pattern 3: Entity-based Formatting (уже в проекте)
**What:** Форматирование через Python объекты, не raw Markdown
**When to use:** Все сообщения с форматированием

```python
# Source: https://docs.aiogram.dev/en/latest/utils/formatting.html
from aiogram.utils.formatting import Text, Bold, BlockQuote

content = Text(
    Bold("Персональный гороскоп для Овна"),
    "\n",
    "на 23.01.2026",
    "\n\n",
    Bold("Общий прогноз"),
    "\n",
    horoscope_text,
)
await message.answer(**content.as_kwargs())
```

### Anti-Patterns to Avoid
- **Raw Markdown в тексте:** Markdown символы (*_`[]) в AI-ответах ломают parse_mode. Entity-based formatting решает эту проблему автоматически.
- **Typing без промежуточного сообщения:** Пользователь видит только "typing...", не понимает что происходит.
- **Множественные typing loops:** Не запускать несколько typing loops для одного чата.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Continuous typing | asyncio loop с send_chat_action | ChatActionSender | Встроенный interval, auto-stop |
| Markdown escaping | regex/manual escape | Entity formatting | Автоматическое экранирование |
| Progress messages | Отдельная логика в каждом handler | Helper function | DRY, единообразие |

**Key insight:** aiogram уже имеет все нужные утилиты. Задача - правильно их применить.

## Common Pitfalls

### Pitfall 1: Typing indicator не обновляется
**What goes wrong:** Typing исчезает через 5 секунд если не обновлять
**Why it happens:** Telegram API requirement
**How to avoid:** ChatActionSender с interval=4.0 (меньше 5 секунд)
**Warning signs:** Пользователь видит прерывистый typing

### Pitfall 2: Markdown разметка видна в сообщениях
**What goes wrong:** Пользователь видит *bold* вместо **bold**
**Why it happens:** parse_mode не установлен или AI вернул raw markdown
**How to avoid:** Entity-based formatting через Text/Bold/etc
**Warning signs:** Asterisks, underscores, backticks в тексте

### Pitfall 3: Сообщение не удаляется (старше 48 часов)
**What goes wrong:** delete_message fails для старых сообщений
**Why it happens:** Telegram API limitation
**How to avoid:** Удалять сразу после получения результата
**Warning signs:** Исключение при delete, мусорные сообщения в чате

### Pitfall 4: Дублирующие запросы от нетерпеливых пользователей
**What goes wrong:** Пользователь жмет кнопку несколько раз
**Why it happens:** Нет feedback о начале операции
**How to avoid:** Промежуточное сообщение + debounce через _generating set (уже есть в natal.py)
**Warning signs:** Множественные AI запросы от одного пользователя

## Code Examples

### Typing + Progress Message для гороскопа
```python
# Source: verified from aiogram docs + existing project patterns
from aiogram.utils.chat_action import ChatActionSender

PROGRESS_MESSAGES = {
    "horoscope": "Генерирую гороскоп...",
    "tarot": "Создаю расклад таро...",
    "natal": "Анализирую натальную карту...",
}

async def generate_with_feedback(
    message: Message,
    operation_type: str,
    ai_coro: Coroutine,
) -> str:
    """AI generation with typing indicator and progress message."""
    progress_text = PROGRESS_MESSAGES.get(operation_type, "Обработка...")
    progress_msg = await message.answer(progress_text)

    try:
        async with ChatActionSender.typing(
            bot=message.bot,
            chat_id=message.chat.id,
            interval=4.0,
        ):
            result = await ai_coro
    finally:
        # Always delete progress message
        try:
            await progress_msg.delete()
        except Exception:
            pass  # Message already deleted or too old

    return result
```

### Различие общий vs персональный гороскоп
```python
from aiogram.utils.formatting import Text, Bold

def format_horoscope_header(
    zodiac_emoji: str,
    zodiac_name_ru: str,
    date_str: str,
    is_personal: bool,
) -> Text:
    """Format horoscope header with type distinction."""
    if is_personal:
        title = f"{zodiac_emoji} Персональный гороскоп"
    else:
        title = f"{zodiac_emoji} Общий гороскоп для {zodiac_name_ru}"

    return Text(
        Bold(title),
        "\n",
        f"на {date_str}",
    )
```

### Клавиатура с различием типов гороскопа
```python
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_horoscope_type_keyboard() -> InlineKeyboardMarkup:
    """Keyboard with general vs personal horoscope options."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Общий гороскоп",
                callback_data="horoscope:general",
            ),
            InlineKeyboardButton(
                text="Персональный гороскоп",
                callback_data="horoscope:personal",
            ),
        ],
    ])
```

### BotFather Description (512 chars max)
```
Астрологический бот - ежедневные гороскопы с AI, расклады таро, натальные карты.

Бесплатно:
- Гороскоп на день
- Карта таро дня
- 1 расклад таро/день

Premium (299 р/мес):
- Персональный гороскоп по натальной карте
- 20 раскладов таро/день
- Кельтский крест (10 карт)
- Полная натальная карта
```

### BotFather About (120 chars max)
```
Гороскопы, таро, натальные карты с AI-интерпретацией. Персональная астрология.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual send_chat_action loop | ChatActionSender context manager | aiogram 3.0 | Чище код, нет race conditions |
| parse_mode=Markdown | Entity-based formatting | aiogram 3.0 | Нет проблем с экранированием |
| Статичные horoscopes | AI-генерация | Phase 5 | Требует typing indicator |

**Deprecated/outdated:**
- `parse_mode="Markdown"` (legacy, заменен на MarkdownV2)
- Manual typing loops в каждом handler

## Open Questions

1. **Первое объяснение разницы гороскопов**
   - What we know: Показать при первом запросе
   - What's unclear: Как трекать "первый раз"? User field? FSM state?
   - Recommendation: Добавить поле `horoscope_explained: bool` в User model или проверять via FSM

2. **FAQ команда**
   - What we know: WEL-04 требует About/FAQ команду
   - What's unclear: Формат (inline keyboard с категориями vs простой текст)
   - Recommendation: Простой текст с разделами, inline keyboard для навигации

## Sources

### Primary (HIGH confidence)
- [aiogram Chat Action docs](https://docs.aiogram.dev/en/latest/utils/chat_action.html) - ChatActionSender API
- [aiogram Formatting docs](https://docs.aiogram.dev/en/latest/utils/formatting.html) - Entity-based formatting
- [aiogram delete_message](https://docs.aiogram.dev/en/latest/api/methods/delete_message.html) - Message deletion

### Secondary (MEDIUM confidence)
- [Telegram BotFather tutorial](https://core.telegram.org/bots/tutorial) - setDescription, setAboutText

### Tertiary (LOW confidence)
- Community patterns for continuous typing loops (verified with official docs)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - aiogram docs verified
- Architecture patterns: HIGH - Based on existing project code + official docs
- Pitfalls: HIGH - Known Telegram API limitations + project experience (natal.py)
- Code examples: HIGH - Verified against aiogram 3.20+ docs

**Research date:** 2026-01-23
**Valid until:** 60 days (aiogram API stable)
