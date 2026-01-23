# Phase 8: Premium Tarot + Natal - Research

**Researched:** 2026-01-23
**Domain:** Premium tarot spreads, tarot history storage, natal chart calculation, SVG visualization
**Confidence:** HIGH (verified with official sources)

## Summary

Phase 8 расширяет таро и астрологию для платных пользователей: 20 раскладов в день, Кельтский крест (10 карт), история раскладов, полная натальная карта с SVG визуализацией.

Основные компоненты:
1. **Кельтский крест** — 10-карточный расклад с 2 секциями (крест + посох), AI интерпретация 800-1200 слов
2. **История раскладов** — новая таблица TarotSpread для хранения, пагинация при показе
3. **Натальная карта (полная)** — расширение существующего `natal_chart.py` для всех планет, домов, аспектов через pyswisseph
4. **SVG генерация** — собственная генерация через svgwrite (избегаем AGPL kerykeion)

**Primary recommendation:** Использовать pyswisseph напрямую для расчётов (уже в проекте), svgwrite для SVG генерации (MIT license), избегать kerykeion из-за AGPL.

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pyswisseph | 2.10+ | Астрономические расчёты | Уже используется в `natal_chart.py`, Swiss Ephemeris — золотой стандарт |
| aiogram | 3.x | Telegram Bot API | Уже используется, `MediaGroupBuilder` для альбомов |
| SQLAlchemy | 2.0+ | ORM для истории раскладов | Уже используется в проекте |
| Pillow | 10.x | Ротация изображений карт | Уже используется для reversed карт |

### New for Phase 8
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| svgwrite | 1.4.3+ | SVG генерация | Создание натальной карты (MIT license) |
| cairosvg | 2.8+ | SVG to PNG конвертация | Для отправки в Telegram (принимает только PNG/JPG) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| svgwrite | kerykeion | Kerykeion — AGPL-3.0, требует открытие исходного кода. svgwrite — MIT, полный контроль |
| Custom SVG | kerykeion ChartDrawer | Больше работы, но без лицензионных рисков для коммерческого проекта |
| cairosvg | Pillow SVG | cairosvg качественнее для SVG to PNG |

**Installation:**
```bash
pip install svgwrite cairosvg
```

**AGPL Warning:** Kerykeion (AGPL-3.0) требует открытия исходного кода если бот взаимодействует с пользователями через сеть. Для коммерческого проекта рекомендуется svgwrite (MIT).

## Architecture Patterns

### Recommended Project Structure
```
src/
├── services/
│   └── astrology/
│       ├── natal_chart.py      # Расширить: все планеты, дома, аспекты
│       ├── natal_svg.py        # НОВЫЙ: SVG генерация натальной карты
│       └── geocoding.py        # Уже есть
├── db/
│   └── models/
│       └── tarot_spread.py     # НОВЫЙ: модель истории раскладов
├── bot/
│   ├── handlers/
│   │   ├── tarot.py            # Расширить: Кельтский крест, история
│   │   └── natal.py            # НОВЫЙ: натальная карта handler
│   ├── keyboards/
│   │   ├── tarot.py            # Расширить: кнопки Кельтский крест, История
│   │   └── natal.py            # НОВЫЙ: клавиатура натальной карты
│   └── callbacks/
│       ├── tarot.py            # Расширить: новые actions
│       └── natal.py            # НОВЫЙ: callbacks натальной карты
└── services/
    └── ai/
        └── prompts.py          # Расширить: Кельтский крест, Натальная карта
```

### Pattern 1: Celtic Cross 10-Card Layout
**What:** Структура расклада Кельтский крест — 10 позиций в 2 секциях
**When to use:** При генерации и интерпретации Кельтского креста

**Позиции Кельтского креста:**
```
Секция КРЕСТ (карты 1-6):
1. Настоящее (центр) — текущая ситуация
2. Препятствие (поперёк 1) — вызов, который нужно преодолеть
3. Прошлое (слева) — влияние прошлого
4. Будущее (справа) — ближайшее будущее
5. Сознательное (сверху) — цели и желания
6. Подсознательное (снизу) — скрытые влияния

Секция ПОСОХ (карты 7-10, справа вертикально):
7. Я (внизу) — самовосприятие
8. Окружение (выше) — внешние влияния
9. Надежды и Страхи (выше) — ожидания
10. Исход (вверху) — итог ситуации
```

### Pattern 2: Tarot Spread History Model
**What:** Модель для хранения раскладов пользователя
**When to use:** Сохранение каждого расклада для истории

```python
# Source: SQLAlchemy 2.0 ORM pattern
class TarotSpread(Base):
    __tablename__ = "tarot_spreads"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Spread metadata
    spread_type: Mapped[str] = mapped_column(String(20))  # "three_card" | "celtic_cross"
    question: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Cards (JSON array)
    cards: Mapped[dict] = mapped_column(JSON)  # [{"card_id": "ar01", "reversed": false, "position": 1}, ...]

    # AI interpretation (stored for history view)
    interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
```

### Pattern 3: Full Natal Chart Calculation
**What:** Расширение расчёта натальной карты для всех планет и аспектов
**When to use:** Генерация полной натальной карты

```python
# Source: pyswisseph documentation
import swisseph as swe

# Планеты для расчёта
PLANETS = {
    swe.SUN: "Sun",
    swe.MOON: "Moon",
    swe.MERCURY: "Mercury",
    swe.VENUS: "Venus",
    swe.MARS: "Mars",
    swe.JUPITER: "Jupiter",
    swe.SATURN: "Saturn",
    swe.URANUS: "Uranus",
    swe.NEPTUNE: "Neptune",
    swe.PLUTO: "Pluto",
    swe.TRUE_NODE: "North Node",  # Лунные узлы
}

# Аспекты
ASPECTS = {
    0: ("Conjunction", 8),      # орб 8 градусов
    60: ("Sextile", 6),
    90: ("Square", 8),
    120: ("Trine", 8),
    180: ("Opposition", 8),
}

def calculate_aspects(planets: dict[str, float]) -> list[dict]:
    """Calculate aspects between all planet pairs."""
    aspects = []
    planet_names = list(planets.keys())
    for i, p1 in enumerate(planet_names):
        for p2 in planet_names[i+1:]:
            diff = abs(planets[p1] - planets[p2])
            if diff > 180:
                diff = 360 - diff
            for angle, (name, orb) in ASPECTS.items():
                if abs(diff - angle) <= orb:
                    aspects.append({
                        "planet1": p1,
                        "planet2": p2,
                        "aspect": name,
                        "orb": round(abs(diff - angle), 1)
                    })
    return aspects
```

### Pattern 4: SVG Natal Chart Generation
**What:** Генерация SVG круга натальной карты через svgwrite
**When to use:** Визуализация натальной карты

```python
# Source: svgwrite documentation, custom implementation
import svgwrite
from io import BytesIO
import cairosvg

def generate_natal_svg(chart_data: dict, size: int = 600) -> bytes:
    """Generate natal chart SVG and convert to PNG."""
    dwg = svgwrite.Drawing(size=(size, size))
    center = size / 2
    radius = size / 2 - 20

    # Внешний круг (знаки зодиака)
    dwg.add(dwg.circle(center=(center, center), r=radius,
                       stroke='#333', fill='none', stroke_width=2))

    # Деления знаков (12 секторов по 30 градусов)
    for i in range(12):
        angle = i * 30 - 90  # Aries at top
        # ... добавить линии и символы знаков

    # Планеты (точки на окружности)
    for planet, lon in chart_data['planets'].items():
        # ... расположить планету по долготе

    # Аспекты (линии между планетами)
    for aspect in chart_data['aspects']:
        # ... нарисовать линию соответствующего цвета/стиля

    # Конвертация в PNG для Telegram
    svg_string = dwg.tostring()
    png_bytes = cairosvg.svg2png(bytestring=svg_string.encode())
    return png_bytes
```

### Pattern 5: MediaGroupBuilder for Cards
**What:** Отправка нескольких карт таро одним альбомом
**When to use:** Кельтский крест — 10 карт (но Telegram лимит 10)

```python
# Source: aiogram 3.x documentation
from aiogram.utils.media_group import MediaGroupBuilder

async def send_celtic_cross_cards(message: Message, cards: list[tuple[dict, bool]]):
    """Send 10 cards as album (max 10 items in Telegram)."""
    media_group = MediaGroupBuilder()

    positions = ["Настоящее", "Препятствие", "Прошлое", "Будущее",
                 "Сознательное", "Подсознательное", "Я", "Окружение",
                 "Надежды/Страхи", "Исход"]

    for i, (card, reversed_flag) in enumerate(cards):
        photo = get_card_image(card["name_short"], reversed_flag)
        caption = f"{i+1}. {positions[i]}: {card['name']}"
        if reversed_flag:
            caption += " (перевернутая)"
        media_group.add_photo(media=photo, caption=caption if i == 0 else None)

    await message.answer_media_group(media=media_group.build())
```

### Anti-Patterns to Avoid
- **Хранение изображений карт в БД**: Храни только card_id и reversed flag, изображения генерируй на лету
- **Неограниченная история**: Установи лимит (100-200 раскладов) или retention период (90 дней)
- **Синхронный SVG рендеринг**: Используй `run_in_executor` для cairosvg, это CPU-bound операция
- **Хардкод timezone**: Всегда конвертируй в UTC для хранения, в локальное время для показа

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Астрономические расчёты | Собственные формулы | pyswisseph | NASA JPL DE431 ephemeris, точность до arc-seconds |
| Timezone birth time | Manual offset calculation | pytz + GeoNames timezone | DST изменения, исторические offsets |
| Aspect orbs | Fixed orbs for all | Standard orbs per aspect | Традиционная астрология имеет разные орбы |
| SVG to PNG | Pillow SVG parsing | cairosvg | Полная поддержка SVG 1.1 |

**Key insight:** Астрологические расчёты требуют высокой точности. Swiss Ephemeris — индустриальный стандарт с 1997 года, используется профессиональными астрологами.

## Common Pitfalls

### Pitfall 1: Telegram Media Group Limit
**What goes wrong:** Попытка отправить более 10 элементов в альбоме
**Why it happens:** Кельтский крест = 10 карт, ровно на границе лимита
**How to avoid:** Проверять `len(cards) <= 10`, при необходимости разбивать на 2 сообщения
**Warning signs:** aiogram.exceptions.TelegramBadRequest

### Pitfall 2: UTC vs Local Time for Birth
**What goes wrong:** Неправильный расчёт позиций планет из-за неверного времени
**Why it happens:** Пользователь вводит локальное время, а расчёт требует UTC
**How to avoid:**
1. Получить timezone от GeoNames (уже есть в `geocoding.py`)
2. Конвертировать local time в UTC: `local_tz.localize(dt).astimezone(pytz.UTC)`
3. Использовать UTC для swe.julday()
**Warning signs:** Позиции планет отличаются от других калькуляторов

### Pitfall 3: AGPL License Contamination
**What goes wrong:** Использование kerykeion требует открытия всего исходного кода бота
**Why it happens:** AGPL распространяется на любой код, взаимодействующий с AGPL через сеть
**How to avoid:** Использовать MIT-licensed svgwrite для SVG генерации
**Warning signs:** Использование `from kerykeion import ...`

### Pitfall 4: Large AI Prompts for 10 Cards
**What goes wrong:** Timeout или обрезанный ответ при генерации интерпретации 10 карт
**Why it happens:** GPT-4o-mini имеет ограничения на output tokens
**How to avoid:**
1. Увеличить `max_tokens` до 3000-4000 для Кельтского креста
2. Структурировать промпт по секциям (Крест, Посох)
3. Увеличить timeout до 60 секунд
**Warning signs:** Обрезанные интерпретации, `finish_reason: "length"`

### Pitfall 5: Spread History Pagination
**What goes wrong:** Telegram callback_data превышает 64 байта при передаче spread_id
**Why it happens:** Длинные callback данные с pagination + spread_id
**How to avoid:** Использовать короткие prefixes: `h:5:1` (history, spread_id, page)
**Warning signs:** aiogram.exceptions.TelegramBadRequest: BUTTON_DATA_INVALID

## Code Examples

### Example 1: Extended Natal Chart Calculation
```python
# Source: pyswisseph official documentation + project pattern
from datetime import datetime, time, date
import swisseph as swe
import pytz

PLANETS = [
    (swe.SUN, "sun"), (swe.MOON, "moon"),
    (swe.MERCURY, "mercury"), (swe.VENUS, "venus"),
    (swe.MARS, "mars"), (swe.JUPITER, "jupiter"),
    (swe.SATURN, "saturn"), (swe.URANUS, "uranus"),
    (swe.NEPTUNE, "neptune"), (swe.PLUTO, "pluto"),
    (swe.TRUE_NODE, "north_node"),
]

def calculate_full_natal_chart(
    birth_date: date,
    birth_time: time | None,
    latitude: float,
    longitude: float,
    timezone_str: str,
) -> dict:
    """Calculate complete natal chart with all planets, houses, aspects."""

    # Convert local time to UTC
    local_tz = pytz.timezone(timezone_str)
    if birth_time:
        dt = datetime.combine(birth_date, birth_time)
        dt_local = local_tz.localize(dt)
        dt_utc = dt_local.astimezone(pytz.UTC)
        hour_ut = dt_utc.hour + dt_utc.minute / 60.0
    else:
        hour_ut = 12.0  # Noon if unknown

    # Julian Day in UT
    jd = swe.julday(birth_date.year, birth_date.month, birth_date.day, hour_ut)

    # Calculate all planets
    planets = {}
    for planet_id, name in PLANETS:
        result, _ = swe.calc_ut(jd, planet_id)
        planets[name] = {
            "longitude": result[0],
            "sign": get_sign(result[0]),
            "degree": result[0] % 30,
        }

    # Calculate houses (Placidus)
    cusps, ascmc = swe.houses(jd, latitude, longitude, b"P")
    houses = {i+1: {"cusp": cusps[i], "sign": get_sign(cusps[i])} for i in range(12)}

    # Ascendant, MC
    angles = {
        "ascendant": {"longitude": ascmc[0], "sign": get_sign(ascmc[0])},
        "mc": {"longitude": ascmc[1], "sign": get_sign(ascmc[1])},
    }

    # Calculate aspects
    aspects = calculate_aspects({name: p["longitude"] for name, p in planets.items()})

    return {
        "planets": planets,
        "houses": houses,
        "angles": angles,
        "aspects": aspects,
        "time_known": birth_time is not None,
    }
```

### Example 2: Celtic Cross AI Prompt
```python
# Source: TarotSpreadPrompt pattern from existing prompts.py
@dataclass
class CelticCrossPrompt:
    """Prompt for Celtic Cross 10-card spread interpretation."""

    SYSTEM = """Ты - опытный таролог, интерпретирующий расклады Кельтский крест.
Твоя задача - дать глубокую интерпретацию 10-карточного расклада.

ФОРМАТ ОТВЕТА (800-1200 слов):

[СЕРДЦЕ ВОПРОСА]
Карты 1-2: Настоящее и Препятствие. Суть ситуации и главный вызов.

[ВРЕМЕННАЯ ОСЬ]
Карты 3-4: Прошлое и Ближайшее будущее. Как прошлое влияет и куда движется.

[СОЗНАНИЕ И ПОДСОЗНАНИЕ]
Карты 5-6: Сознательное и Подсознательное. Явные и скрытые мотивы.

[ВНЕШНИЙ МИР]
Карты 7-8: Я и Окружение. Самовосприятие и влияние других.

[ПУТЬ К ИСХОДУ]
Карты 9-10: Надежды/Страхи и Исход. Ожидания и итог.

[ОБЩИЙ ПОСЫЛ]
Синтез всех карт. Практические рекомендации.

СТИЛЬ:
- Обращайся на "ты", глубоко и мудро
- Связывай карты в единое повествование
- Учитывай перевернутые карты
- Давай конкретные рекомендации
- НЕ упоминай, что ты AI"""

    @staticmethod
    def user(question: str, cards: list[tuple[dict, bool]]) -> str:
        positions = [
            "1. Настоящее", "2. Препятствие", "3. Прошлое", "4. Будущее",
            "5. Сознательное", "6. Подсознательное", "7. Я", "8. Окружение",
            "9. Надежды/Страхи", "10. Исход"
        ]
        cards_text = []
        for i, (card, reversed_flag) in enumerate(cards):
            status = " (перевернута)" if reversed_flag else ""
            cards_text.append(f"{positions[i]}: {card['name']}{status}")

        return f"""Вопрос: {question[:500]}

Карты Кельтского креста:
{chr(10).join(cards_text)}"""
```

### Example 3: Natal Chart AI Prompt
```python
# Source: PremiumHoroscopePrompt pattern + natal chart requirements
@dataclass
class NatalChartPrompt:
    """Prompt for full natal chart interpretation."""

    SYSTEM = """Ты - опытный астролог, интерпретирующий натальные карты.
Твоя задача - дать полную интерпретацию карты рождения, понятную новичку.

ФОРМАТ ОТВЕТА (1000-1500 слов):

[СОЛНЦЕ, ЛУНА, АСЦЕНДЕНТ - Большая тройка]
Твоя суть (Солнце), эмоции (Луна), маска для мира (Асцендент).

[ЛИЧНОСТЬ И САМОВЫРАЖЕНИЕ]
Меркурий (мышление), Венера (любовь), Марс (действие).

[СОЦИАЛЬНЫЕ ПЛАНЕТЫ]
Юпитер (удача, рост), Сатурн (ограничения, уроки).

[ВЫСШИЕ ПЛАНЕТЫ]
Уран, Нептун, Плутон - поколенческие влияния.

[ОСНОВНЫЕ АСПЕКТЫ]
Ключевые взаимодействия между планетами.

[СФЕРЫ ЖИЗНИ]
- Личность и внешность (1 дом)
- Отношения (7 дом, Венера)
- Карьера (10 дом, MC)
- Здоровье (6 дом, Марс)

СТИЛЬ:
- Объясняй простым языком без жаргона
- Приводи конкретные примеры проявления
- Будь позитивным даже о сложных аспектах
- НЕ упоминай, что ты AI"""

    @staticmethod
    def user(natal_data: dict) -> str:
        # Format planets
        planets_text = []
        for name, data in natal_data["planets"].items():
            planets_text.append(f"{name}: {data['sign']} {data['degree']:.1f}")

        # Format aspects
        aspects_text = []
        for asp in natal_data["aspects"][:15]:  # Top 15 aspects
            aspects_text.append(f"{asp['planet1']} {asp['aspect']} {asp['planet2']}")

        return f"""Натальная карта:

Планеты:
{chr(10).join(planets_text)}

Асцендент: {natal_data['angles']['ascendant']['sign']}
MC: {natal_data['angles']['mc']['sign']}

Основные аспекты:
{chr(10).join(aspects_text)}

Время рождения: {'известно' if natal_data['time_known'] else 'неизвестно'}"""
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| flatlib для расчётов | pyswisseph напрямую | Phase 7 decision | flatlib устарел, требует pyswisseph 2.08 |
| Внешние API для SVG | Собственная генерация | Phase 8 decision | Полный контроль над дизайном |
| pytz для timezone | zoneinfo (Python 3.9+) | Python 3.9 | Можно использовать оба, pytz уже в проекте |

**Deprecated/outdated:**
- flatlib: Требует устаревшую версию pyswisseph
- kerykeion для коммерческих проектов: AGPL лицензия

## Open Questions

1. **Лимит истории раскладов**
   - What we know: Нужно хранить историю, но бесконечное хранение нецелесообразно
   - What's unclear: Сколько раскладов хранить? По времени (90 дней) или количеству (100)?
   - Recommendation: 100 последних раскладов, с возможностью увеличить позже

2. **SVG стиль натальной карты**
   - What we know: Нужно "красивое идеальное изображение"
   - What's unclear: Конкретная цветовая схема, стиль символов
   - Recommendation: Минималистичный дизайн, тёмная тема (как бот), планеты как цветные точки

3. **Показ 10 карт Кельтского креста**
   - What we know: Можно альбомом (10 фото = лимит Telegram)
   - What's unclear: Альбом vs последовательная отправка с задержкой
   - Recommendation: Альбом — быстрее и компактнее

## Sources

### Primary (HIGH confidence)
- [pyswisseph GitHub](https://github.com/astrorigin/pyswisseph) - API и примеры
- [aiogram MediaGroupBuilder docs](https://docs.aiogram.dev/en/latest/utils/media_group.html) - отправка альбомов
- [Labyrinthos Celtic Cross](https://labyrinthos.co/blogs/learn-tarot-with-labyrinthos-academy/the-celtic-cross-tarot-spread-exploring-the-classic-10-card-tarot-spread) - позиции Кельтского креста

### Secondary (MEDIUM confidence)
- [Kerykeion documentation](https://www.kerykeion.net/content/docs/aspects) - паттерны расчёта аспектов (не используем, но референс)
- [svgwrite PyPI](https://pypi.org/project/svgwrite/) - SVG генерация

### Tertiary (LOW confidence)
- [Code for Fiction - Vedic SVG charts](https://www.codeforafiction.com/2024/03/creating-north-indian-style-vedic.html) - пример svgwrite для астрологии

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - все компоненты уже в проекте или проверены
- Architecture: HIGH - паттерны следуют существующей архитектуре проекта
- Pitfalls: HIGH - верифицировано через документацию Telegram и pyswisseph

**Research date:** 2026-01-23
**Valid until:** 30 дней (стабильные технологии)
