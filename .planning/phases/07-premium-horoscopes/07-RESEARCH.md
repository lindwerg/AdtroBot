# Phase 7: Premium Horoscopes - Research

**Researched:** 2026-01-23
**Domain:** Premium astrology features, natal chart calculation, birth data input, personalized AI horoscopes
**Confidence:** HIGH

## Summary

Phase 7 реализует премиум-гороскопы с детализацией по сферам жизни и персонализацию на основе натальной карты. Основные задачи:
1. Расширить существующий HoroscopePrompt для детального формата по сферам
2. Добавить поля birth_time и birth_place в User модель для натальной карты
3. Создать UI для ввода времени и места рождения
4. Интегрировать астрологические данные в AI-промпт для персонализации
5. Показывать teaser для бесплатных пользователей

Текущая архитектура (AIService, HoroscopePrompt, validators) позволяет расширение без рефакторинга. Натальная карта требует библиотеку для вычисления позиций планет и домов.

**Primary recommendation:** Использовать flatlib (MIT лицензия) для расчета натальной карты, GeoNames API для геокодинга города. Для MVP достаточно передавать астрологические данные в prompt GPT-4o-mini без сложных астрологических интерпретаций.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| flatlib | 0.2.3 | Расчет натальной карты | MIT лицензия, работает с pyswisseph, проверенная библиотека |
| pyswisseph | 2.10.3.2 | Swiss Ephemeris для астровычислений | Стандарт индустрии (NASA JPL DE431), высокая точность |
| geopy | 2.4.1 | Геокодинг через GeoNames | Простой Python API, поддержка timezone |
| aiogram-calendar | 0.9.3+ | Inline календарь для даты рождения | Интеграция с aiogram 3.x |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| aiogram-timepicker | 0.0.1 | Inline выбор времени | Для birth_time (опционально, можно текстовый ввод) |
| timezonefinder | 6.5.0+ | Определение timezone по координатам | Если нужна автоопределение timezone |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| flatlib | kerykeion 5.6.3 | Активнее разрабатывается, больше фич, SVG-чарты, НО AGPL лицензия требует open-source всего проекта |
| flatlib | immanuel 1.5.3 | Современнее, JSON-сериализация, НО тоже AGPL |
| flatlib | astrology-api.io | Hosted API, нет лицензионных проблем, НО зависимость от внешнего сервиса |
| geopy + GeoNames | Google Places API | Лучший autocomplete, НО платный для production |
| Inline keyboard time | Text input "HH:MM" | Проще реализация, меньше зависимостей |

**Installation:**
```bash
poetry add flatlib pyswisseph geopy aiogram-calendar
```

**Note:** flatlib не обновлялся с 2021, но стабилен и работает. Если возникнут проблемы совместимости с Python 3.12+, рассмотреть API-сервис.

## Architecture Patterns

### Recommended Project Structure
```
src/
├── services/
│   ├── ai/
│   │   ├── prompts.py           # Добавить PremiumHoroscopePrompt
│   │   └── client.py            # Добавить generate_premium_horoscope()
│   └── astrology/
│       ├── __init__.py
│       ├── natal_chart.py       # Расчет натальной карты через flatlib
│       └── geocoding.py         # GeoNames интеграция для города
├── bot/
│   ├── handlers/
│   │   └── horoscope.py         # Расширить для premium/free логики
│   ├── states/
│   │   └── birth_data.py        # FSM для ввода time/place
│   ├── callbacks/
│   │   └── horoscope.py         # Добавить premium callbacks
│   └── keyboards/
│       └── birth_data.py        # Клавиатуры для ввода birth data
└── db/
    └── models/
        └── user.py              # Добавить birth_time, birth_city, birth_lat, birth_lon
```

### Pattern 1: Premium Feature Gating

**What:** Проверка is_premium перед показом детального контента
**When to use:** Любой premium-only endpoint
**Example:**
```python
# Source: Existing pattern from tarot.py limit checks
async def show_horoscope(callback: CallbackQuery, session: AsyncSession):
    user = await get_user(session, callback.from_user.id)

    if user.is_premium:
        text = await get_premium_horoscope(user)
    else:
        # Teaser: показать общий гороскоп + призыв к подписке
        basic_text = await get_basic_horoscope(user.zodiac_sign)
        text = f"{basic_text}\n\n{'*' * 20}\nПремиум включает персональный прогноз по сферам жизни!"

    await callback.message.edit_text(text, reply_markup=...)
```

### Pattern 2: Two-Stage Prompt (Astro Data + AI Generation)

**What:** Сначала рассчитать астрологические данные, затем передать в AI prompt
**When to use:** Персонализированные гороскопы с натальной картой
**Example:**
```python
# Stage 1: Calculate natal chart data
natal_data = calculate_natal_chart(
    birth_date=user.birth_date,
    birth_time=user.birth_time,  # Optional, use noon if None
    latitude=user.birth_lat,
    longitude=user.birth_lon
)
# natal_data = {
#     "sun_sign": "Aries", "sun_house": 10,
#     "moon_sign": "Cancer", "moon_house": 1,
#     "ascendant": "Leo",
#     "planets": {...},
#     "aspects": [...]
# }

# Stage 2: Generate personalized horoscope
prompt = PremiumHoroscopePrompt.user(
    zodiac_sign_ru="Овен",
    date_str="23.01.2026",
    natal_data=natal_data  # Добавляем астрологический контекст
)
horoscope = await ai_service.generate_premium_horoscope(prompt)
```

### Pattern 3: Progressive Birth Data Collection

**What:** FSM для пошагового сбора birth_date -> birth_time -> birth_place
**When to use:** Premium onboarding, profile settings
**Example:**
```python
class BirthDataStates(StatesGroup):
    waiting_birth_time = State()      # "Введи время рождения (HH:MM)"
    waiting_birth_city = State()      # "Введи город рождения"
    confirming_city = State()         # Показать найденные варианты

# Handler flow:
# 1. User clicks "Настроить натальную карту"
# 2. Bot asks for birth_time (text input "HH:MM" или "не знаю")
# 3. If "не знаю" -> use noon (12:00)
# 4. Bot asks for birth_city (text input)
# 5. Geocode city -> show inline buttons with matches
# 6. User selects city -> save coordinates + timezone
# 7. Calculate natal chart -> show summary
```

### Anti-Patterns to Avoid

- **Синхронные вычисления натальной карты в handler:** flatlib быстрый, но геокодинг требует HTTP-вызова. Всегда используй async/await с aiohttp.
- **Хранение raw natal chart в БД:** Слишком много данных. Храни только birth_time, birth_lat, birth_lon. Вычисляй натальную карту при генерации гороскопа.
- **Показ полного premium контента без подписки:** Всегда проверяй is_premium. Teaser должен быть коротким и интригующим.
- **Жесткая привязка к конкретному geocoding провайдеру:** Используй абстракцию, позволяющую сменить GeoNames на OpenCage если лимиты превышены.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Расчет позиций планет | Формулы астрономии | flatlib + pyswisseph | Сложная математика, нужна точность Swiss Ephemeris |
| Геокодинг города | HTTP-запросы к API | geopy.geocoders.GeoNames | Обработка ошибок, rate limiting, caching |
| Определение timezone | Lookup таблицы | geopy/timezonefinder | База данных меняется, есть DST |
| Парсинг времени "12:30" | regex | datetime.strptime | Edge cases: 24:00, пробелы |
| Inline календарь | InlineKeyboardBuilder | aiogram-calendar | Pagination, навигация по месяцам |

**Key insight:** Астрологические вычисления требуют специализированных эфемерид (Swiss Ephemeris). Попытка реализовать самому приведет к неточностям, которые астрологически подкованные пользователи заметят.

## Common Pitfalls

### Pitfall 1: Время рождения "не знаю"

**What goes wrong:** Пользователь не знает точное время рождения, но хочет натальную карту
**Why it happens:** ~50% пользователей не знают время рождения
**How to avoid:**
- Сделать birth_time опциональным
- Использовать noon chart (12:00) если время неизвестно
- Предупреждать, что Ascendant и дома могут быть неточными
- В prompt указывать "время приблизительное"
**Warning signs:** Пользователь отказывается от premium из-за обязательного поля

### Pitfall 2: Геокодинг неоднозначных названий

**What goes wrong:** "Москва" -> какой регион? "Paris" -> France или Texas?
**Why it happens:** Одинаковые названия городов в разных странах/регионах
**How to avoid:**
- Возвращать несколько результатов (max 5)
- Показывать страну/регион в результатах: "Москва, Россия" vs "Москва, Московская область, Россия"
- Inline buttons для выбора конкретного варианта
- Приоритизировать результаты (countryBias для России/СНГ)
**Warning signs:** Пользователь выбирает неправильный город, получает странный timezone

### Pitfall 3: GeoNames Rate Limiting

**What goes wrong:** API возвращает 503 при превышении лимитов
**Why it happens:** 10,000 credits/day, 1,000/hour бесплатно
**How to avoid:**
- Кэшировать результаты геокодинга в БД (город + координаты)
- Использовать собственный GeoNames username (не demo)
- Fallback на альтернативный провайдер (OpenCage: 2,500/day free)
**Warning signs:** Спайки ошибок геокодинга в логах

### Pitfall 4: Лицензия AGPL

**What goes wrong:** Использование kerykeion/immanuel требует open-source всего проекта
**Why it happens:** AGPL "copyleft" распространяется на network use
**How to avoid:**
- Использовать flatlib (MIT) вместо kerykeion/immanuel (AGPL)
- Или использовать astrology-api.io (hosted service, нет лицензионных требований)
- Если нужен kerykeion - купить коммерческую лицензию или сделать проект open-source
**Warning signs:** Юридические риски при коммерческом использовании

### Pitfall 5: Prompt длина с natal data

**What goes wrong:** Слишком много астрологических данных в prompt -> токены/стоимость
**Why it happens:** Полная натальная карта = ~50 полей
**How to avoid:**
- Включать только ключевые данные: Sun, Moon, Ascendant, ключевые аспекты
- Не включать все планеты и все аспекты
- Формат: краткий JSON, не verbose описания
**Warning signs:** Резкий рост стоимости AI-генерации

## Code Examples

### Natal Chart Calculation with flatlib

```python
# Source: flatlib README + pyswisseph docs
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

def calculate_natal_chart(
    birth_date: date,
    birth_time: time | None,
    latitude: float,
    longitude: float
) -> dict:
    """Calculate natal chart positions.

    Args:
        birth_date: Date of birth
        birth_time: Time of birth (use 12:00 if None)
        latitude: Birth place latitude
        longitude: Birth place longitude

    Returns:
        Dict with sun_sign, moon_sign, ascendant, planets, houses
    """
    # Use noon if time unknown
    hour = birth_time.hour if birth_time else 12
    minute = birth_time.minute if birth_time else 0

    # Create flatlib datetime (format: 'YYYY/MM/DD', 'HH:MM', timezone)
    dt = Datetime(
        f"{birth_date.year}/{birth_date.month:02d}/{birth_date.day:02d}",
        f"{hour:02d}:{minute:02d}",
        "+00:00"  # UTC, adjust for user timezone if needed
    )

    # Create position (format: 'DDnMM' for lat, 'DDDwMM' for lon)
    lat_dir = 'n' if latitude >= 0 else 's'
    lon_dir = 'e' if longitude >= 0 else 'w'
    pos = GeoPos(
        f"{abs(int(latitude))}{lat_dir}{int((abs(latitude) % 1) * 60):02d}",
        f"{abs(int(longitude))}{lon_dir}{int((abs(longitude) % 1) * 60):02d}"
    )

    chart = Chart(dt, pos)

    # Extract key positions
    sun = chart.get(const.SUN)
    moon = chart.get(const.MOON)
    asc = chart.get(const.ASC)

    return {
        "sun_sign": sun.sign,
        "sun_degree": round(sun.lon % 30, 1),
        "moon_sign": moon.sign,
        "moon_degree": round(moon.lon % 30, 1),
        "ascendant": asc.sign,
        "ascendant_degree": round(asc.lon % 30, 1),
        "time_known": birth_time is not None,
    }
```

### Premium Horoscope Prompt

```python
# Source: Extension of existing HoroscopePrompt in prompts.py
@dataclass
class PremiumHoroscopePrompt:
    """Prompt for premium personalized horoscope."""

    SYSTEM = """Ты - опытный астролог, создающий персонализированные гороскопы.
Твоя задача - написать детальный гороскоп на сегодня с учетом натальной карты пользователя.

ФОРМАТ ОТВЕТА (500-700 слов):

[ОБЩИЙ ПРОГНОЗ]
2-3 предложения о энергии дня для этого знака.

[ЛЮБОВЬ И ОТНОШЕНИЯ]
4-5 предложений. Учитывай позицию Луны и Венеры в натальной карте.
Конкретные советы для одиноких и пар.

[КАРЬЕРА И ФИНАНСЫ]
4-5 предложений. Учитывай Солнце и Сатурн.
Практические рекомендации по работе и деньгам.

[ЗДОРОВЬЕ И ЭНЕРГИЯ]
3-4 предложения. Учитывай Марс.
Советы по самочувствию, физической активности.

[ЛИЧНОСТНЫЙ РОСТ]
3-4 предложения. Учитывай Асцендент.
Что можно сделать сегодня для развития.

[СОВЕТ ДНЯ]
1-2 конкретных совета, персонализированных под натальную карту.

СТИЛЬ:
- Обращайся на "ты", дружелюбно и тепло
- Упоминай влияние планет из натальной карты
- Пиши конкретно, используй детали из астроданных
- НЕ упоминай, что ты AI
- НЕ используй фразы "как AI", "я не могу"
- НЕ извиняйся и не отказывайся"""

    @staticmethod
    def user(
        zodiac_sign_ru: str,
        date_str: str,
        natal_data: dict,
        zodiac_sign_en: str = ""
    ) -> str:
        """Generate user prompt with natal chart data."""
        greeting = get_zodiac_greeting(zodiac_sign_en, zodiac_sign_ru)

        natal_context = f"""
Натальная карта:
- Солнце: {natal_data['sun_sign']} {natal_data['sun_degree']}°
- Луна: {natal_data['moon_sign']} {natal_data['moon_degree']}°
- Асцендент: {natal_data['ascendant']} {natal_data['ascendant_degree']}°
- Время рождения: {"известно" if natal_data['time_known'] else "неизвестно (используется полдень)"}
"""
        return f"""Создай персональный гороскоп на {date_str} для:
Знак: {zodiac_sign_ru}
{natal_context}
Начни с обращения: "{greeting}"
"""
```

### GeoNames City Search

```python
# Source: geopy docs + GeoNames API docs
from geopy.geocoders import GeoNames
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import asyncio

class GeocodingService:
    """Service for geocoding birth cities."""

    def __init__(self, username: str = "your_geonames_username"):
        self.geolocator = GeoNames(username=username)

    async def search_city(
        self,
        query: str,
        max_results: int = 5,
        country_bias: str = "RU"
    ) -> list[dict]:
        """Search for cities matching query.

        Returns list of {name, country, lat, lon, timezone}
        """
        try:
            # geopy is sync, run in executor
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.geolocator.geocode(
                    query,
                    exactly_one=False,
                    timeout=10
                )
            )

            if not results:
                return []

            cities = []
            for loc in results[:max_results]:
                cities.append({
                    "name": loc.address,
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                    "timezone": loc.raw.get("timezone", {}).get("timezoneId", "UTC"),
                })
            return cities

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error("geocoding_failed", error=str(e), query=query)
            return []
```

### Teaser for Free Users

```python
# Source: Pattern from subscription.py premium features
PREMIUM_TEASER = """
{'='*30}
ПРЕМИУМ-ГОРОСКОП

Хочешь узнать:
- Персональный прогноз по любви на основе твоей Луны
- Карьерные возможности с учетом твоего Солнца
- Советы по здоровью по Марсу
- Финансовый прогноз

Подробный гороскоп с натальной картой ждет тебя!
{'='*30}
"""

async def show_horoscope_with_teaser(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession
) -> None:
    """Show horoscope with premium teaser for free users."""
    zodiac = ZODIAC_SIGNS[user.zodiac_sign]

    # Basic horoscope for everyone
    basic_text = await get_horoscope_text(user.zodiac_sign, zodiac.name_ru)

    if user.is_premium:
        # Full premium experience
        if user.birth_lat and user.birth_lon:
            natal_data = calculate_natal_chart(
                user.birth_date, user.birth_time,
                user.birth_lat, user.birth_lon
            )
            premium_text = await generate_premium_horoscope(
                zodiac.name_ru, natal_data
            )
            text = premium_text
        else:
            # Premium but no natal data yet
            text = f"{basic_text}\n\nДля персонального прогноза укажи место рождения в профиле!"
    else:
        # Free user - show teaser
        text = f"{basic_text}\n\n{PREMIUM_TEASER}"

    await callback.message.edit_text(
        text,
        reply_markup=build_horoscope_keyboard(user.is_premium)
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Статические гороскопы из газет | AI-генерация (GPT-4o-mini) | 2023-2024 | Персонализация, вариативность |
| Расчет натальной карты вручную | Swiss Ephemeris (flatlib) | 2010s | Точность до аркминуты |
| Google Maps geocoding | GeoNames/OpenCage | 2020s | Бесплатные тиры, лучше для небольших проектов |

**Deprecated/outdated:**
- **flatlib v0.2.3 (2021):** Работает, но не обновляется. Мониторить совместимость с Python 3.12+
- **kerykeion < 5.0:** Сильно изменился API в v5. Использовать только 5.6.x если переходить

## Open Questions

1. **Нужна ли визуализация натальной карты (SVG)?**
   - What we know: kerykeion умеет SVG, flatlib нет
   - What's unclear: Важно ли это для пользователей Telegram?
   - Recommendation: MVP без визуализации. Добавить в Phase 8+ если будет спрос

2. **Точность noon chart vs unknown time**
   - What we know: Ascendant меняется на 1 знак каждые 2 часа
   - What's unclear: Насколько критично для пользователей?
   - Recommendation: Предупреждать пользователя, что без времени Асцендент приблизительный

3. **Кэширование premium гороскопов**
   - What we know: Basic horoscope кэшируется по знаку, premium персональный
   - What's unclear: Кэшировать ли premium по user_id + date?
   - Recommendation: Да, кэшировать на 1 час. Экономит AI-вызовы при повторных запросах

## Sources

### Primary (HIGH confidence)
- [flatlib GitHub](https://github.com/flatangle/flatlib) - README, examples, MIT license verified
- [pyswisseph PyPI](https://pypi.org/project/pyswisseph/) - Version 2.10.3.2, AGPL-3.0
- [GeoNames Web Services](http://www.geonames.org/export/web-services.html) - API docs, rate limits
- [geopy Documentation](https://geopy.readthedocs.io/) - GeoNames geocoder usage
- [aiogram 3.x Docs](https://docs.aiogram.dev/) - CallbackQuery, FSM, InlineKeyboard

### Secondary (MEDIUM confidence)
- [kerykeion PyPI](https://pypi.org/project/kerykeion/) - v5.6.3 features, AGPL license confirmed
- [immanuel-python GitHub](https://github.com/theriftlab/immanuel-python) - v1.5.3, AGPL license
- [astrology-api.io](https://astrology-api.io/) - Free tier 100 req/mo, pricing tiers

### Tertiary (LOW confidence)
- WebSearch: Premium horoscope features (love, career, health, finance) - common patterns across services
- WebSearch: AGPL commercial use - general guidance, consult lawyer for specifics
- WebSearch: pyswisseph natal chart examples - various tutorials, verify with official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - flatlib/pyswisseph well-documented, MIT license clear
- Architecture: HIGH - patterns match existing codebase, verified implementations
- Pitfalls: MEDIUM - based on general knowledge + WebSearch, some require validation
- GeoNames limits: HIGH - official documentation verified

**Research date:** 2026-01-23
**Valid until:** 2026-02-23 (30 days - stable domain)
