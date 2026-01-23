# Phase 10: Улучшить натальную карту - Research

**Researched:** 2026-01-23
**Domain:** SVG визуализация натальной карты + AI интерпретации + монетизация
**Confidence:** MEDIUM

## Summary

Исследование охватывает три области: (1) визуальное улучшение натальной карты с использованием svgwrite, (2) создание "прорывной" AI интерпретации 3000-5000 слов, (3) монетизация детального разбора через YooKassa.

**Визуал:** svgwrite полностью поддерживает градиенты (LinearGradient, RadialGradient), что позволяет создать профессиональный вид с градиентным фоном, свечениями вокруг планет, и плавными переходами цветов. Unicode символы (U+2648-U+2653 для зодиака, U+2609/U+263D-U+2647 для планет) обеспечат аутентичный астрологический вид вместо текстовых аббревиатур.

**AI интерпретация:** Для генерации 3000-5000 слов нужна секционная стратегия - разбить на 6-8 секций по 400-600 слов каждая, генерировать последовательно или использовать один большой промпт с max_tokens=8000. GPT-4o-mini имеет выходной лимит 16K токенов, достаточный для 5000 слов на русском.

**Монетизация:** YooKassa уже интегрирована для подписок. Для разовых покупок используется тот же API с `capture: True`. Цена 199 рублей следует "charm pricing" психологии (окончание на 9), но для premium продукта может быть эффективнее 249 или 299 рублей.

**Primary recommendation:** Улучшить SVG градиентами и Unicode глифами; создать секционный промпт для длинной интерпретации; добавить PaymentPlan.DETAILED_NATAL для разового платежа 199-249 рублей.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| svgwrite | 1.4.3 | SVG генерация с градиентами | Уже используется, поддерживает LinearGradient/RadialGradient |
| cairosvg | current | SVG -> PNG конвертация | Уже интегрирован |
| yookassa | 3.x | Платежи YooKassa | Уже интегрирован для подписок |
| openai (AsyncOpenAI) | current | OpenRouter API для AI | Уже используется через OpenRouter |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| telegraph | current | Публикация длинных статей | Для интерпретаций >4096 символов |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Unicode глифы | Embedded SVG icons | Unicode проще, но требует поддержку шрифта; SVG иконки гарантированно рендерятся |
| Один большой промпт | Секционная генерация | Один промпт проще, но может обрезаться; секции надежнее |

**Installation:**
```bash
# Ничего нового устанавливать не нужно - все библиотеки уже есть
pip install svgwrite cairosvg yookassa
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── services/astrology/
│   ├── natal_svg.py         # Улучшить: градиенты, глифы, профессиональный дизайн
│   └── natal_chart.py       # Без изменений
├── services/ai/
│   ├── prompts.py           # Добавить: DetailedNatalPrompt (3000-5000 слов)
│   ├── client.py            # Добавить: generate_detailed_natal_interpretation()
│   └── cache.py             # Добавить: кэш для detailed natal (7 дней)
├── services/payment/
│   ├── schemas.py           # Добавить: PaymentPlan.DETAILED_NATAL
│   └── service.py           # Расширить: обработка разовых покупок
├── bot/handlers/
│   └── natal.py             # Добавить: обработчик клика по карте, покупка детального разбора
└── db/models/
    └── user.py              # Добавить: purchased_detailed_natal (bool/datetime)
```

### Pattern 1: SVG Gradients для профессионального вида
**What:** Использование RadialGradient для фона и свечений вокруг планет
**When to use:** Всегда для natальной карты
**Example:**
```python
# Source: https://svgwrite.readthedocs.io/en/latest/classes/gradients.html
def _generate_svg(chart_data: FullNatalChartResult, size: int = 600) -> str:
    dwg = svgwrite.Drawing(size=(size, size))

    # Background radial gradient (dark center, lighter edges)
    bg_gradient = dwg.radialGradient(center=("50%", "50%"), r="70%", id="bg_grad")
    bg_gradient.add_stop_color(0, "#0d0d1a")      # Deep space center
    bg_gradient.add_stop_color(0.7, "#1a1a2e")    # Current dark color
    bg_gradient.add_stop_color(1, "#2d2d44")      # Lighter edge
    dwg.defs.add(bg_gradient)

    # Apply to background
    dwg.add(dwg.rect((0, 0), (size, size),
        fill=bg_gradient.get_paint_server()))

    # Planet glow gradient
    planet_glow = dwg.radialGradient(id="planet_glow")
    planet_glow.add_stop_color(0, "rgba(255,215,0,0.8)")  # Bright center
    planet_glow.add_stop_color(1, "rgba(255,215,0,0)")    # Transparent edge
    dwg.defs.add(planet_glow)
```

### Pattern 2: Unicode астрологические символы
**What:** Замена текстовых аббревиатур (Su, Mo) на Unicode глифы
**When to use:** Для планет и знаков зодиака
**Example:**
```python
# Source: https://www.alt-codes.net/planet-symbols.php
PLANET_GLYPHS = {
    "sun": "\u2609",       # Sun symbol
    "moon": "\u263D",      # First quarter moon (or \u263E for last quarter)
    "mercury": "\u263F",   # Mercury
    "venus": "\u2640",     # Venus
    "mars": "\u2642",      # Mars
    "jupiter": "\u2643",   # Jupiter
    "saturn": "\u2644",    # Saturn
    "uranus": "\u2645",    # Uranus
    "neptune": "\u2646",   # Neptune
    "pluto": "\u2647",     # Pluto
    "north_node": "\u260A", # Ascending Node
}

# Source: https://www.symbolspy.com/zodiac-symbols-text.html
ZODIAC_GLYPHS = {
    0: "\u2648",   # Aries
    1: "\u2649",   # Taurus
    2: "\u264A",   # Gemini
    3: "\u264B",   # Cancer
    4: "\u264C",   # Leo
    5: "\u264D",   # Virgo
    6: "\u264E",   # Libra
    7: "\u264F",   # Scorpio
    8: "\u2650",   # Sagittarius
    9: "\u2651",   # Capricorn
    10: "\u2652",  # Aquarius
    11: "\u2653",  # Pisces
}
```

### Pattern 3: Секционная генерация длинного контента
**What:** Разбиение 3000-5000 слов на секции для надежной генерации
**When to use:** Для детальной интерпретации натальной карты
**Example:**
```python
# Source: https://learnprompting.org/docs/intermediate/long_form_content
DETAILED_NATAL_SECTIONS = [
    {
        "name": "personality_core",
        "title": "ЯДРО ЛИЧНОСТИ: Солнце, Луна, Асцендент",
        "prompt": "Детально разбери Большую Тройку...",
        "max_tokens": 1200,  # ~500-600 слов
    },
    {
        "name": "mind_communication",
        "title": "МЫШЛЕНИЕ И КОММУНИКАЦИЯ: Меркурий",
        "prompt": "Разбери позицию Меркурия...",
        "max_tokens": 800,
    },
    # ... 6-8 секций всего
]

async def generate_detailed_natal(natal_data: dict) -> str:
    sections = []
    for section in DETAILED_NATAL_SECTIONS:
        text = await self._generate(
            system_prompt=DetailedNatalPrompt.SYSTEM,
            user_prompt=DetailedNatalPrompt.section(section, natal_data),
            max_tokens=section["max_tokens"],
        )
        sections.append(f"## {section['title']}\n\n{text}")
    return "\n\n".join(sections)
```

### Pattern 4: Разовый платеж через YooKassa
**What:** Одноразовая покупка детального разбора
**When to use:** Когда пользователь кликает на натальную карту
**Example:**
```python
# Уже реализовано в src/services/payment/client.py
# Нужно только добавить новый PaymentPlan

class PaymentPlan(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    DETAILED_NATAL = "detailed_natal"  # Новый

PLAN_PRICES = {
    PaymentPlan.MONTHLY: 29900,        # 299.00 RUB
    PaymentPlan.YEARLY: 249900,        # 2499.00 RUB
    PaymentPlan.DETAILED_NATAL: 19900, # 199.00 RUB
}

# В metadata платежа:
metadata = {
    "user_id": str(user_id),
    "plan_type": "detailed_natal",  # Для webhook processing
    "type": "one_time",             # Не recurring
}
```

### Anti-Patterns to Avoid
- **Хардкод цен в handlers:** Использовать PLAN_PRICES из schemas.py
- **Один огромный промпт без структуры:** Разбить на секции с заголовками
- **Игнорирование Unicode font fallback:** Использовать web-safe font с астрологическими глифами (DejaVu Sans имеет хорошую поддержку)
- **Кэширование детальной интерпретации на 24 часа:** Использовать 7 дней (карта не меняется, а генерация дорогая)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SVG градиенты | Ручной XML | svgwrite.linearGradient/radialGradient | API обрабатывает все edge cases |
| Платежи | Собственный API wrapper | yookassa SDK + существующий client.py | Уже интегрирован, включая webhooks |
| Длинный текст в Telegram | Множественные сообщения | Telegraph | Лимит 4096 символов, Telegraph безлимитный |
| Астро-символы | SVG paths | Unicode U+2648-U+2653 | Стандарт, поддерживается везде |

**Key insight:** Все базовые компоненты уже в проекте. Фаза 10 - это улучшение существующего, не создание нового.

## Common Pitfalls

### Pitfall 1: Unicode глифы не рендерятся в SVG
**What goes wrong:** CairoSVG не может найти шрифт с астрологическими символами
**Why it happens:** Системные шрифты могут не содержать Unicode U+2648-U+2653
**How to avoid:**
1. Указать font-family с fallback: `font-family="DejaVu Sans, Symbola, sans-serif"`
2. Альтернатива: использовать SVG paths для глифов (гарантированный рендеринг)
**Warning signs:** Пустые квадраты вместо символов в PNG

### Pitfall 2: AI обрезает длинный вывод
**What goes wrong:** GPT возвращает 1500 слов вместо запрошенных 3000-5000
**Why it happens:** Модель сама решает когда остановиться, даже если max_tokens позволяет больше
**How to avoid:**
1. Секционная генерация (6-8 секций по 400-600 слов)
2. Явные инструкции: "Напиши МИНИМУМ 500 слов для этой секции"
3. Проверка длины + retry если слишком коротко
**Warning signs:** `chars < 10000` для полной интерпретации (5000 слов ~ 25000 символов)

### Pitfall 3: Клик по фото не работает в Telegram
**What goes wrong:** Telegram не поддерживает callback на клик по фотографии
**Why it happens:** Telegram API ограничение - фото не интерактивны
**How to avoid:**
1. Добавить inline_keyboard под фото с кнопкой "Детальный разбор личности - 199 руб."
2. Использовать caption с инструкцией
**Warning signs:** Требование "при клике на карту" в ТЗ

### Pitfall 4: Двойная покупка одного продукта
**What goes wrong:** Пользователь платит дважды за один детальный разбор
**Why it happens:** Нет проверки purchased_detailed_natal перед созданием платежа
**How to avoid:**
1. Добавить поле `detailed_natal_purchased_at` в User модель
2. Проверять перед показом кнопки покупки
3. При повторном запросе отдавать из кэша
**Warning signs:** Жалобы пользователей на повторные списания

### Pitfall 5: Потеря платежа без доставки контента
**What goes wrong:** Платеж прошел, но интерпретация не сгенерирована
**Why it happens:** AI сервис недоступен после успешного webhook
**How to avoid:**
1. В webhook сохранять флаг "payment_succeeded" без мгновенной генерации
2. Отдельный background task для генерации
3. Retry механизм если генерация failed
**Warning signs:** `payment.status == succeeded` но `user.detailed_natal_interpretation is None`

## Code Examples

### Улучшенный SVG с градиентами
```python
# Source: https://svgwrite.readthedocs.io/en/latest/classes/gradients.html
def _generate_svg_professional(chart_data: FullNatalChartResult, size: int = 800) -> str:
    """Generate professional natal chart SVG with gradients."""
    dwg = svgwrite.Drawing(size=(size, size))
    center = size / 2

    # === DEFS: Gradients ===
    # Background: cosmic radial gradient
    bg_grad = dwg.radialGradient(center=("50%", "50%"), r="70%", id="bg")
    bg_grad.add_stop_color(0, "#0a0a14")     # Deep space
    bg_grad.add_stop_color(0.5, "#1a1a2e")   # Dark blue
    bg_grad.add_stop_color(1, "#252542")     # Lighter edge
    dwg.defs.add(bg_grad)

    # Zodiac band gradient
    zodiac_grad = dwg.linearGradient(start=("0%", "0%"), end=("100%", "100%"), id="zodiac")
    zodiac_grad.add_stop_color(0, "#3d3d5c")
    zodiac_grad.add_stop_color(1, "#2d2d44")
    dwg.defs.add(zodiac_grad)

    # Planet glow (reusable)
    for color_name, color_value in [("gold", "#FFD700"), ("silver", "#C0C0C0")]:
        glow = dwg.radialGradient(id=f"glow_{color_name}")
        glow.add_stop_color(0, color_value)
        glow.add_stop_color(0.5, f"{color_value}80")  # 50% opacity
        glow.add_stop_color(1, f"{color_value}00")    # transparent
        dwg.defs.add(glow)

    # === Background ===
    dwg.add(dwg.rect((0, 0), (size, size), fill=bg_grad.get_paint_server()))

    # === Zodiac wheel with gradient fill ===
    outer_r = size / 2 - 30
    inner_r = outer_r - 60

    # Draw zodiac band as path with gradient
    # ... (arc paths for each sign)

    # === Planets with Unicode glyphs ===
    PLANET_GLYPHS = {
        "sun": "\u2609", "moon": "\u263D", "mercury": "\u263F",
        "venus": "\u2640", "mars": "\u2642", "jupiter": "\u2643",
        "saturn": "\u2644", "uranus": "\u2645", "neptune": "\u2646",
        "pluto": "\u2647", "north_node": "\u260A",
    }

    for planet_name, planet_data in chart_data["planets"].items():
        glyph = PLANET_GLYPHS.get(planet_name, "?")
        # Draw glow circle first
        dwg.add(dwg.circle(center=(px, py), r=20,
            fill=dwg.defs.elements["glow_gold"].get_paint_server()))
        # Draw glyph
        dwg.add(dwg.text(glyph, insert=(px, py),
            text_anchor="middle", dominant_baseline="middle",
            fill=PLANET_COLORS[planet_name], font_size=16,
            font_family="DejaVu Sans, Symbola, sans-serif"))

    return dwg.tostring()
```

### Детальный промпт для натальной интерпретации
```python
# Source: https://promptadvance.club/blog/chatgpt-prompts-for-astrology
@dataclass
class DetailedNatalPrompt:
    """Prompt for detailed natal chart interpretation (3000-5000 words)."""

    SYSTEM = """Ты - профессиональный астролог с 20-летним опытом.
Пиши детальную интерпретацию натальной карты для клиента.

СТИЛЬ:
- Обращайся на "ты", тепло и профессионально
- Используй астрологические термины, но объясняй их
- Приводи конкретные примеры из жизни ("Это может проявляться как...")
- Каждая секция должна быть МИНИМУМ 400 слов
- Общий объем: 3000-5000 слов

СТРУКТУРА КАЖДОЙ СЕКЦИИ:
1. Описание позиции (знак, дом, градус)
2. Психологическое значение
3. Конкретные проявления в жизни
4. Сильные стороны этой позиции
5. Зоны роста и рекомендации

НЕ упоминай, что ты AI. Пиши как живой астролог."""

    SECTIONS = [
        {
            "id": "core",
            "title": "ЯДРО ЛИЧНОСТИ",
            "focus": "Солнце, Луна, Асцендент - кто ты в глубине души",
            "min_words": 600,
        },
        {
            "id": "mind",
            "title": "МЫШЛЕНИЕ И КОММУНИКАЦИЯ",
            "focus": "Меркурий - как ты думаешь, учишься, общаешься",
            "min_words": 400,
        },
        {
            "id": "love",
            "title": "ЛЮБОВЬ И ОТНОШЕНИЯ",
            "focus": "Венера, 7-й дом - как ты любишь и чего ищешь в партнере",
            "min_words": 500,
        },
        {
            "id": "drive",
            "title": "ЭНЕРГИЯ И АМБИЦИИ",
            "focus": "Марс - как ты действуешь, добиваешься целей, проявляешь агрессию",
            "min_words": 400,
        },
        {
            "id": "career",
            "title": "КАРЬЕРА И ПРИЗВАНИЕ",
            "focus": "MC, 10-й дом, Сатурн - твое предназначение в обществе",
            "min_words": 500,
        },
        {
            "id": "growth",
            "title": "ДУХОВНЫЙ РОСТ И ТРАНСФОРМАЦИЯ",
            "focus": "Юпитер, Сатурн, внешние планеты - уроки и возможности",
            "min_words": 400,
        },
        {
            "id": "talents",
            "title": "СКРЫТЫЕ ТАЛАНТЫ И РЕСУРСЫ",
            "focus": "8-й и 12-й дома, Плутон, Нептун - глубинный потенциал",
            "min_words": 400,
        },
        {
            "id": "summary",
            "title": "ИТОГИ И РЕКОМЕНДАЦИИ",
            "focus": "Синтез карты, главные жизненные темы, практические советы",
            "min_words": 400,
        },
    ]

    @staticmethod
    def section(section: dict, natal_data: dict) -> str:
        """Generate prompt for a specific section."""
        return f"""Напиши секцию "{section['title']}" для натальной карты.

Фокус: {section['focus']}

МИНИМУМ {section['min_words']} СЛОВ.

Натальные данные:
{format_natal_for_prompt(natal_data)}

Пиши детально, с примерами из жизни. Не сокращай!"""
```

### Обработка покупки детального разбора
```python
# В handlers/natal.py
@router.callback_query(NatalCallback.filter(F.action == NatalAction.BUY_DETAILED))
async def buy_detailed_natal(callback: CallbackQuery, session: AsyncSession):
    """Handle buy detailed natal interpretation button."""
    user = await get_user(session, callback.from_user.id)

    # Check if already purchased
    if user.detailed_natal_purchased_at:
        # Already purchased - show cached or regenerate
        interpretation = await get_or_generate_detailed_natal(user)
        telegraph_url = await publish_to_telegraph(interpretation)
        await callback.message.answer(
            "Ты уже приобрел детальный разбор!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Открыть разбор", url=telegraph_url)]
            ])
        )
        return

    # Create payment
    from src.services.payment.client import create_payment
    from src.services.payment.schemas import PLAN_PRICES_STR, PaymentPlan

    payment = await create_payment(
        user_id=user.telegram_id,
        amount=PLAN_PRICES_STR[PaymentPlan.DETAILED_NATAL],
        description="Детальный разбор натальной карты",
        save_payment_method=False,  # One-time purchase
        metadata={"plan_type": "detailed_natal", "type": "one_time"},
    )

    await callback.message.answer(
        "Детальный разбор личности (3000-5000 слов):\n\n"
        "- Ядро личности: Солнце, Луна, Асцендент\n"
        "- Мышление и коммуникация\n"
        "- Любовь и отношения\n"
        "- Карьера и призвание\n"
        "- Таланты и скрытый потенциал\n"
        "- Персональные рекомендации\n\n"
        f"Цена: {PLAN_PRICES_STR[PaymentPlan.DETAILED_NATAL]} руб.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить", url=payment.confirmation.confirmation_url)]
        ])
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Текстовые аббревиатуры (Su, Mo) | Unicode глифы (star, moon) | Всегда было в профессиональных картах | Аутентичный астрологический вид |
| Плоские цвета | Градиенты + свечения | CSS/SVG тренд 2020+ | Премиальный вид |
| Короткие AI тексты | Секционная генерация | GPT-4 2023+ | Возможность 5000+ слов |
| Только подписки | Подписки + разовые покупки | Микротранзакции 2024+ | Снижение барьера входа |

**Deprecated/outdated:**
- Kerykeion для SVG (AGPL лицензия - не подходит для коммерческого использования)
- Единый промпт для длинного контента (ненадежно)

## Open Questions

1. **Шрифт для Unicode глифов в Cairo**
   - What we know: DejaVu Sans и Symbola содержат астро-символы
   - What's unclear: Какой шрифт установлен на Railway сервере
   - Recommendation: Добавить fallback на SVG paths если глифы не рендерятся

2. **Оптимальная цена: 199 vs 249 vs 299 руб.**
   - What we know: "Charm pricing" (.99) работает для mass market, округленные цены - для premium
   - What's unclear: Какая конверсия будет у целевой аудитории
   - Recommendation: Начать с 199 руб., A/B тестировать 249 через месяц

3. **Клик по карте -> переход к гороскопу**
   - What we know: Telegram не поддерживает клик по фото
   - What's unclear: Пользователь хочет именно клик или достаточно кнопки под фото
   - Recommendation: Уточнить требование; использовать inline keyboard под фото

## Sources

### Primary (HIGH confidence)
- svgwrite ReadTheDocs (градиенты): https://svgwrite.readthedocs.io/en/latest/classes/gradients.html
- svgwrite GitHub examples: https://github.com/mozman/svgwrite/blob/master/examples/linearGradient.py
- Текущий код проекта: natal_svg.py, payment/client.py, ai/client.py

### Secondary (MEDIUM confidence)
- Unicode символы планет: https://www.alt-codes.net/planet-symbols.php
- Unicode символы зодиака: https://www.symbolspy.com/zodiac-symbols-text.html
- Charm pricing psychology: https://www.shopify.com/blog/psychological-pricing
- Long-form AI content: https://learnprompting.org/docs/intermediate/long_form_content

### Tertiary (LOW confidence)
- AI astrology prompts (WebSearch): https://promptadvance.club/blog/chatgpt-prompts-for-astrology
- Digital goods pricing Russia (не найдено специфичных данных)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - все библиотеки уже в проекте и задокументированы
- Architecture: MEDIUM - секционная генерация AI не протестирована
- Pitfalls: MEDIUM - основаны на общем опыте, не специфичном для проекта
- Pricing: LOW - нет данных по конверсии для этого продукта

**Research date:** 2026-01-23
**Valid until:** 30 дней (стабильный стек, но AI практики быстро меняются)
