# Phase 13: Image Generation - Research

**Researched:** 2026-01-24
**Domain:** Бесплатные stock изображения (Unsplash/Pexels) + Pillow обработка
**Confidence:** HIGH

## Summary

Исследование нового подхода: вместо AI-генерации использовать готовые бесплатные stock изображения с Unsplash и Pexels, затем обрабатывать их Pillow для единого мистического стиля.

**Ключевые находки:**
- **Pexels** — лучший выбор: 200 req/hour бесплатно, лицензия разрешает коммерческое использование без атрибуции
- **Unsplash** — backup: 50 req/hour (demo), требует approval для production (5000 req/hour)
- **Pillow 12.1.0** — уже установлен в проекте, достаточен для всех операций обработки
- **Лицензии** — обе платформы разрешают коммерческое использование в ботах без атрибуции
- **Единый стиль** — достигается через Pillow: darkening + purple overlay + contrast

**Primary recommendation:** Использовать Pexels API для поиска/скачивания изображений + Pillow для унификации стиля (darkening, purple tint, contrast boost). Создать скрипт `scripts/fetch_and_process_images.py` с двухэтапной обработкой.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pexels-api-py | 0.0.5 | Pexels API wrapper | Простой API, хорошая документация, активно поддерживается |
| Pillow | 12.1.0 | Image processing | УЖЕ УСТАНОВЛЕН в проекте, полный функционал |
| requests | (installed) | HTTP для скачивания | Стандарт Python, уже в проекте |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib | stdlib | Path management | Организация assets/ |
| io | stdlib | BytesIO | Промежуточная обработка |
| python-unsplash | 1.1.0 | Unsplash API (backup) | Если Pexels не найдет подходящие изображения |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pexels | Unsplash | 50 vs 200 req/hour бесплатно, Unsplash требует approval |
| Pexels | Pixabay | Нет официального Python SDK, API менее удобный |
| pexels-api-py | requests напрямую | Больше кода, но без зависимости |

**Installation:**
```bash
pip install pexels-api-py
# Pillow уже установлен в проекте
```

## Лицензирование (КРИТИЧНО)

### Pexels License
| Аспект | Статус | Детали |
|--------|--------|--------|
| Коммерческое использование | ДА | Разрешено в приложениях, ботах, продуктах |
| Атрибуция | НЕ ТРЕБУЕТСЯ | Опционально, но приветствуется |
| Модификация | ДА | Можно обрабатывать, фильтровать, изменять |
| Ограничения | Да | Нельзя создавать конкурирующий stock сервис |

**Источник:** https://help.pexels.com/hc/en-us/articles/360042295174

### Unsplash License
| Аспект | Статус | Детали |
|--------|--------|--------|
| Коммерческое использование | ДА | Irrevocable, worldwide license |
| Атрибуция | НЕ ТРЕБУЕТСЯ | "No permission needed" |
| Модификация | ДА | Полная свобода обработки |
| Ограничения | Да | Нельзя продавать без модификации, нельзя конкурировать |

**Источник:** https://unsplash.com/license

### Вывод по лицензиям
Оба сервиса полностью подходят для коммерческого Telegram бота. Модификация изображений (наша обработка) дополнительно защищает от любых претензий.

## API Rate Limits

### Pexels (РЕКОМЕНДУЕТСЯ)
| Tier | Requests/Hour | Requests/Month | Карта |
|------|---------------|----------------|-------|
| Default | 200 | 20,000 | НЕТ |
| Unlimited | Unlimited | Unlimited | НЕТ (нужна атрибуция) |

**Для 17 изображений:** 17 запросов = 8.5% часового лимита. Более чем достаточно.

### Unsplash
| Tier | Requests/Hour | Approval |
|------|---------------|----------|
| Demo | 50 | Не нужен |
| Production | 5,000 | Нужен (показать использование) |

**Для 17 изображений:** Хватит даже demo tier.

## Architecture Patterns

### Recommended Project Structure
```
assets/
└── images/
    ├── raw/                    # Оригиналы с Pexels (временно)
    │   ├── welcome_raw.jpg
    │   ├── zodiac/
    │   └── tarot/
    └── processed/              # Обработанные (финальные)
        ├── welcome.png
        ├── zodiac/
        │   ├── aries.png
        │   └── ...
        ├── tarot/
        │   ├── three_card.png
        │   └── celtic_cross.png
        ├── natal_chart.png
        └── paywall.png
scripts/
├── fetch_images.py             # Скачивание с Pexels
└── process_images.py           # Обработка Pillow
```

### Pattern 1: Pexels Search and Download
**What:** Поиск изображений по ключевым словам и скачивание
**When to use:** Первый этап — получение raw материала
**Example:**
```python
# Source: Pexels API documentation + pexels-api-py
import os
import requests
from pexelsapi.pexels import Pexels
from pathlib import Path

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
pexel = Pexels(PEXELS_API_KEY)

def search_and_download(query: str, output_path: Path, color: str = "", orientation: str = "square"):
    """Search for image and download best match."""
    results = pexel.search_photos(
        query=query,
        orientation=orientation,  # square, landscape, portrait
        size="large",             # large(24MP), medium(12MP), small(4MP)
        color=color,              # purple, black, blue, etc.
        per_page=5
    )

    if not results or 'photos' not in results or not results['photos']:
        print(f"No results for: {query}")
        return False

    # Берем первое изображение
    photo = results['photos'][0]
    image_url = photo['src']['large']  # или 'original' для максимального качества

    # Скачиваем
    response = requests.get(image_url)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    print(f"Downloaded: {output_path}")
    return True
```

### Pattern 2: Unified Style Processing
**What:** Обработка изображения для единого мистического стиля
**When to use:** Второй этап — унификация всех изображений
**Example:**
```python
# Source: Pillow documentation + ImageEnhance, ImageOps
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from pathlib import Path

def apply_mystical_style(input_path: Path, output_path: Path, size: tuple = (1024, 1024)):
    """Apply unified mystical style to image."""
    # Открываем изображение
    img = Image.open(input_path)

    # 1. Resize to square (crop center if needed)
    img = ImageOps.fit(img, size, method=Image.Resampling.LANCZOS)

    # 2. Convert to RGB (remove alpha if present)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # 3. Darken (reduce brightness to 0.6-0.7)
    brightness = ImageEnhance.Brightness(img)
    img = brightness.enhance(0.65)

    # 4. Increase contrast slightly
    contrast = ImageEnhance.Contrast(img)
    img = contrast.enhance(1.2)

    # 5. Purple tint overlay
    # Создаем фиолетовый слой и blend
    purple = Image.new('RGB', size, (75, 0, 130))  # Indigo purple
    img = Image.blend(img, purple, alpha=0.15)  # 15% tint

    # 6. Optional: slight blur for mystical effect
    # img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

    # 7. Final contrast boost
    contrast = ImageEnhance.Contrast(img)
    img = contrast.enhance(1.1)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"Processed: {output_path}")
```

### Pattern 3: Golden Accent Enhancement
**What:** Усиление золотых/желтых тонов для символов
**When to use:** Для изображений с золотыми элементами (zodiac symbols, paywall lock)
**Example:**
```python
from PIL import Image, ImageEnhance

def enhance_golden_tones(img: Image.Image) -> Image.Image:
    """Boost warm/golden colors in image."""
    # Increase color saturation
    color = ImageEnhance.Color(img)
    img = color.enhance(1.3)  # 30% more saturated

    # Slightly warm the image (shift toward yellow/gold)
    r, g, b = img.split()
    r = r.point(lambda x: min(255, int(x * 1.05)))  # +5% red
    g = g.point(lambda x: min(255, int(x * 1.02)))  # +2% green
    # blue stays same

    return Image.merge('RGB', (r, g, b))
```

### Anti-Patterns to Avoid
- **Скачивание без проверки:** Всегда проверять, что изображение загрузилось успешно
- **Hardcoded paths:** Использовать pathlib и относительные пути от корня проекта
- **Сохранение raw в git:** Добавить `assets/images/raw/` в .gitignore (только processed коммитить)
- **Игнорирование aspect ratio:** Всегда использовать `ImageOps.fit()` для правильного crop

## Поиск изображений — Ключевые слова

### Таблица поиска для 17 изображений

| Категория | Файл | Query (Pexels) | Color filter | Backup query |
|-----------|------|----------------|--------------|--------------|
| Welcome | welcome.png | "zodiac wheel cosmic" | purple | "astrology cosmic stars" |
| Aries | aries.png | "aries zodiac symbol" | - | "ram horns golden" |
| Taurus | taurus.png | "taurus zodiac symbol" | - | "bull symbol zodiac" |
| Gemini | gemini.png | "gemini zodiac symbol" | - | "twins symbol zodiac" |
| Cancer | cancer.png | "cancer zodiac symbol" | - | "crab zodiac" |
| Leo | leo.png | "leo zodiac symbol" | - | "lion zodiac" |
| Virgo | virgo.png | "virgo zodiac symbol" | - | "maiden zodiac" |
| Libra | libra.png | "libra zodiac symbol" | - | "scales zodiac" |
| Scorpio | scorpio.png | "scorpio zodiac symbol" | - | "scorpion zodiac" |
| Sagittarius | sagittarius.png | "sagittarius zodiac" | - | "archer zodiac" |
| Capricorn | capricorn.png | "capricorn zodiac" | - | "goat zodiac" |
| Aquarius | aquarius.png | "aquarius zodiac" | - | "water bearer zodiac" |
| Pisces | pisces.png | "pisces zodiac" | - | "fish zodiac" |
| Tarot 3-card | three_card.png | "tarot cards back" | black | "tarot spread dark" |
| Celtic Cross | celtic_cross.png | "celtic cross tarot" | - | "tarot spread ten cards" |
| Natal Chart | natal_chart.png | "birth chart astrology" | - | "natal chart wheel" |
| Paywall | paywall.png | "golden lock unlock" | gold | "premium lock mystical" |

### Альтернативные источники (если Pexels не найдет)
1. **Unsplash** — те же запросы, другая база
2. **Pixabay** — 10,000+ tarot cards images
3. **Ручной поиск** — Pexels.com web interface с manual download

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Image resize | Manual pixel math | `ImageOps.fit()` | Handles aspect ratio, centering |
| Color overlay | Per-pixel loops | `Image.blend()` | Fast, vectorized |
| Brightness adjust | Manual math | `ImageEnhance.Brightness` | Preserves color balance |
| HTTP downloads | Custom socket code | `requests.get()` | Handles redirects, errors |
| API rate limiting | Manual timers | `time.sleep(2)` | 200 req/hour = safe margin |
| Path handling | String concatenation | `pathlib.Path` | Cross-platform |

**Key insight:** Pillow и requests делают 90% работы. Скрипт будет < 200 строк.

## Common Pitfalls

### Pitfall 1: Неподходящие изображения
**What goes wrong:** Stock фото не соответствует мистическому стилю
**Why it happens:** Общие запросы возвращают любые изображения
**How to avoid:**
- Использовать color filter (`color="purple"` или `color="black"`)
- Просматривать результаты перед batch processing
- Иметь backup queries
**Warning signs:** Яркие, дневные, несерьезные изображения

### Pitfall 2: Разный стиль после обработки
**What goes wrong:** Изображения все равно выглядят разрозненно
**Why it happens:** Исходники слишком разные
**How to avoid:**
- Применять ОДИНАКОВЫЕ настройки ко всем изображениям
- Тестировать на 2-3 изображениях перед full batch
- При необходимости корректировать индивидуально
**Warning signs:** Визуальная несогласованность при preview

### Pitfall 3: Rate Limit Exceeded
**What goes wrong:** API возвращает 429 ошибку
**Why it happens:** Слишком быстрые запросы
**How to avoid:**
- `time.sleep(2)` между запросами (200/hour = 3/minute safe)
- Retry с exponential backoff
**Warning signs:** 429 status code, "Too Many Requests"

### Pitfall 4: API Key в коде
**What goes wrong:** Ключ утекает в git
**Why it happens:** Hardcoded или .env не в .gitignore
**How to avoid:**
- Использовать `os.getenv("PEXELS_API_KEY")`
- Проверить .gitignore
**Warning signs:** Git history содержит ключи

### Pitfall 5: Wrong Image Format
**What goes wrong:** Telegram сжимает или искажает
**Why it happens:** Неоптимальный размер/формат
**How to avoid:**
- 1024x1024 PNG для всех изображений
- Проверить файл < 10MB
**Warning signs:** Telegram долго загружает

## Code Examples

### Complete Fetch Script
```python
#!/usr/bin/env python3
"""Fetch images from Pexels for AdtroBot."""
# Source: Pexels API docs + pexels-api-py

import os
import time
import requests
from pathlib import Path
from pexelsapi.pexels import Pexels

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
RAW_DIR = Path("assets/images/raw")
DELAY = 2  # seconds between requests

# Image search configuration
IMAGES_CONFIG = {
    "welcome": {"query": "zodiac wheel cosmic", "color": "purple"},
    "zodiac/aries": {"query": "aries zodiac symbol golden"},
    "zodiac/taurus": {"query": "taurus zodiac symbol"},
    "zodiac/gemini": {"query": "gemini zodiac twins"},
    "zodiac/cancer": {"query": "cancer zodiac crab"},
    "zodiac/leo": {"query": "leo zodiac lion"},
    "zodiac/virgo": {"query": "virgo zodiac maiden"},
    "zodiac/libra": {"query": "libra zodiac scales"},
    "zodiac/scorpio": {"query": "scorpio zodiac"},
    "zodiac/sagittarius": {"query": "sagittarius zodiac archer"},
    "zodiac/capricorn": {"query": "capricorn zodiac goat"},
    "zodiac/aquarius": {"query": "aquarius zodiac water"},
    "zodiac/pisces": {"query": "pisces zodiac fish"},
    "tarot/three_card": {"query": "tarot cards back dark", "color": "black"},
    "tarot/celtic_cross": {"query": "tarot spread cards"},
    "natal_chart": {"query": "birth chart astrology wheel"},
    "paywall": {"query": "golden lock premium", "color": "gold"},
}


def fetch_image(pexel: Pexels, name: str, config: dict) -> bool:
    """Fetch single image from Pexels."""
    query = config.get("query", name)
    color = config.get("color", "")

    results = pexel.search_photos(
        query=query,
        orientation="square",
        size="large",
        color=color,
        per_page=5
    )

    if not results or 'photos' not in results or not results['photos']:
        print(f"No results for: {name} (query: {query})")
        return False

    photo = results['photos'][0]
    image_url = photo['src']['large']
    photographer = photo.get('photographer', 'Unknown')

    output_path = RAW_DIR / f"{name}_raw.jpg"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(image_url)
    output_path.write_bytes(response.content)

    print(f"Downloaded: {name} (by {photographer})")
    return True


def main():
    if not PEXELS_API_KEY:
        raise ValueError("PEXELS_API_KEY not set")

    pexel = Pexels(PEXELS_API_KEY)

    for name, config in IMAGES_CONFIG.items():
        fetch_image(pexel, name, config)
        time.sleep(DELAY)

    print(f"\nAll images downloaded to: {RAW_DIR.absolute()}")


if __name__ == "__main__":
    main()
```

### Complete Processing Script
```python
#!/usr/bin/env python3
"""Process raw images for unified mystical style."""
# Source: Pillow documentation

from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from pathlib import Path

RAW_DIR = Path("assets/images/raw")
OUTPUT_DIR = Path("assets/images/processed")
SIZE = (1024, 1024)

# Style parameters
BRIGHTNESS = 0.65      # Darken to 65%
CONTRAST = 1.2         # Boost contrast 20%
PURPLE_TINT = 0.15     # 15% purple overlay
PURPLE_COLOR = (75, 0, 130)  # Indigo


def apply_mystical_style(input_path: Path, output_path: Path):
    """Apply unified mystical style."""
    img = Image.open(input_path)

    # 1. Resize and crop to square
    img = ImageOps.fit(img, SIZE, method=Image.Resampling.LANCZOS)

    # 2. Ensure RGB mode
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # 3. Darken
    img = ImageEnhance.Brightness(img).enhance(BRIGHTNESS)

    # 4. Boost contrast
    img = ImageEnhance.Contrast(img).enhance(CONTRAST)

    # 5. Purple tint overlay
    purple = Image.new('RGB', SIZE, PURPLE_COLOR)
    img = Image.blend(img, purple, alpha=PURPLE_TINT)

    # 6. Final contrast adjustment
    img = ImageEnhance.Contrast(img).enhance(1.1)

    # 7. Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"Processed: {output_path.name}")


def main():
    # Find all raw images
    raw_files = list(RAW_DIR.rglob("*_raw.jpg"))

    if not raw_files:
        print(f"No raw images found in {RAW_DIR}")
        return

    for raw_path in raw_files:
        # Construct output path: remove _raw suffix, change extension
        relative = raw_path.relative_to(RAW_DIR)
        output_name = relative.stem.replace("_raw", "") + ".png"
        output_path = OUTPUT_DIR / relative.parent / output_name

        apply_mystical_style(raw_path, output_path)

    print(f"\nAll images processed to: {OUTPUT_DIR.absolute()}")


if __name__ == "__main__":
    main()
```

### Getting Pexels API Key
```bash
# 1. Go to https://www.pexels.com/api/
# 2. Click "Get Started" and create account (FREE)
# 3. Request API access (instant approval)
# 4. Copy API key

# Add to .env:
echo "PEXELS_API_KEY=your_key_here" >> .env
```

### Estimated Time
- Скачивание: 17 images x 2s delay = ~35 секунд
- Обработка: 17 images x ~1s = ~20 секунд
- **Итого: < 1 минута** (vs 10 минут для AI генерации)

## Ручной подход (Backup)

Если автоматизация не найдет подходящие изображения:

### Шаг 1: Ручной поиск
1. Открыть https://www.pexels.com/
2. Искать по ключевым словам из таблицы выше
3. Скачать понравившиеся изображения
4. Сохранить в `assets/images/raw/`

### Шаг 2: Обработка
Запустить только `process_images.py` — он обработает все raw файлы.

### Шаг 3: Ревью
Проверить результаты, при необходимости заменить неудачные исходники.

## Open Questions

### 1. Наличие качественных zodiac symbol изображений
- **What we know:** Pexels имеет категорию astrology
- **What's unclear:** Есть ли 12 отдельных изображений символов знаков
- **Recommendation:** Сначала выполнить тестовый поиск для 2-3 знаков

### 2. Единообразие результатов обработки
- **What we know:** Pillow применяет идентичные фильтры
- **What's unclear:** Как разные исходники будут выглядеть после обработки
- **Recommendation:** Тестировать на небольшом batch, корректировать параметры

### 3. Fallback на AI если stock не подойдет
- **What we know:** Gemini 2.5 Flash Image работает (предыдущее исследование)
- **What's unclear:** Потребуется ли fallback
- **Recommendation:** Попробовать stock подход первым, AI как backup

## Sources

### Primary (HIGH confidence)
- [Unsplash License](https://unsplash.com/license) - Лицензионные условия
- [Pexels License](https://help.pexels.com/hc/en-us/articles/360042295174) - Коммерческое использование
- [Pillow ImageEnhance](https://pillow.readthedocs.io/en/stable/reference/ImageEnhance.html) - Официальная документация
- [Pillow Image](https://pillow.readthedocs.io/en/stable/reference/Image.html) - blend, composite, resize

### Secondary (MEDIUM confidence)
- [pexels-api-py GitHub](https://github.com/meetsohail/pexels-api-py) - Python SDK
- [Pexels API Rate Limits](https://help.pexels.com/hc/en-us/articles/900005852323) - 200 req/hour
- [Unsplash API Docs](https://unsplash.com/documentation) - 50 req/hour demo

### Tertiary (LOW confidence)
- WebSearch results about Pexels/Unsplash image availability for zodiac themes

## Metadata

**Confidence breakdown:**
- Лицензирование: HIGH - Официальные страницы лицензий
- API доступ: HIGH - Официальная документация
- Pillow обработка: HIGH - Официальная документация, уже установлен
- Наличие изображений: MEDIUM - Зависит от качества поиска
- Единый стиль: MEDIUM - Требует тестирования

**Research date:** 2026-01-24
**Valid until:** 60 дней (лицензии стабильны, API редко меняются)

---

## Сравнение подходов

| Аспект | Stock Images (NEW) | AI Generation (OLD) |
|--------|-------------------|---------------------|
| Стоимость | Бесплатно | Бесплатно (Gemini) |
| Время генерации | < 1 минуты | ~10 минут |
| Качество | Зависит от поиска | Стабильно хорошее |
| Единообразие | Через обработку | Через промпты |
| Лицензия | Четкая (Pexels/Unsplash) | Gemini ToS |
| Контроль | Выбор из существующих | Генерация по описанию |
| Fallback | AI generation | Ручной дизайн |

**Рекомендация:** Попробовать stock подход — быстрее, проще, лицензионно чище. При неудаче — вернуться к AI.
