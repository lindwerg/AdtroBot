# Phase 13: Image Generation (500 Cosmic Images) - Research

**Researched:** 2026-01-24
**Domain:** Pexels API batch download + Pillow image processing
**Confidence:** HIGH

## Summary

Исследование нового подхода: скачать ~500 космических изображений с Pexels для рандомной отправки при каждом запросе гороскопа/таро/натальной карты. Вместо 17 специфических изображений - 500 разнообразных космических фонов.

**Ключевые находки:**
- **Pexels API** — 200 req/hour, per_page max 80. Для 500 изображений нужно 7 запросов (7 страниц по 80 фото) = **<1 минута API вызовов**
- **Rate limit НЕ проблема** — 7 запросов из 200/hour = 3.5% лимита
- **Наличие контента** — 9,000+ galaxy фото, 1,000+ nebula фото на Pexels
- **Pillow 12.1.0** — уже установлен в проекте, resize до 1280x720 (Telegram оптимум)
- **Лицензия** — Pexels разрешает коммерческое использование без атрибуции

**Primary recommendation:** Использовать Pexels API с per_page=80 для быстрого скачивания 500 изображений (7 API запросов = 560 фото). Обработка Pillow: resize до 1280x720 (16:9, Telegram оптимум), JPEG качество 85%.

## Расчет времени

| Этап | Операции | Время |
|------|----------|-------|
| API запросы | 7 запросов x 2s delay | ~15 секунд |
| Скачивание | 500 файлов x ~300KB | ~3-5 минут (зависит от сети) |
| Обработка | 500 файлов x 0.1s | ~50 секунд |
| **ИТОГО** | | **~5-7 минут** |

**Сравнение с лимитами:**
- 200 req/hour = можем скачать 200 x 80 = 16,000 изображений за час
- Нам нужно 500 = **7 запросов** = никаких проблем с лимитами

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | (installed) | HTTP для скачивания | Стандарт Python, уже в проекте |
| Pillow | 12.1.0 | Image resize/processing | УЖЕ УСТАНОВЛЕН в проекте |
| pathlib | stdlib | Path management | Cross-platform |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| time | stdlib | Delay между запросами | Rate limit safety |
| json | stdlib | Parsing API response | Альтернатива SDK |
| concurrent.futures | stdlib | Parallel downloads | Ускорение скачивания |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| raw requests | pexels-api-py | SDK добавляет зависимость, но мало функционала сверх requests |
| requests | httpx | async, но для 500 файлов не критично |
| sequential | asyncio + aiohttp | Быстрее, но сложнее, не нужно для разовой задачи |

**Installation:**
```bash
# Ничего нового не нужно!
# Pillow и requests уже установлены
```

## API Details

### Pexels Search Endpoint
```
GET https://api.pexels.com/v1/search

Headers:
  Authorization: YOUR_API_KEY

Parameters:
  query: string (required) - "space nebula galaxy cosmos"
  page: int (1-based) - страница результатов
  per_page: int (max 80) - фото на страницу
  orientation: "landscape" | "portrait" | "square"
  size: "large" | "medium" | "small"
  color: string (optional)
```

### Response Structure
```json
{
  "total_results": 9000,
  "page": 1,
  "per_page": 80,
  "photos": [
    {
      "id": 123456,
      "width": 4000,
      "height": 3000,
      "photographer": "John Doe",
      "src": {
        "original": "https://...",
        "large2x": "https://...",
        "large": "https://...",     // ~1920x1280
        "medium": "https://...",    // ~1280x853
        "small": "https://...",     // ~640x426
        "portrait": "https://...",
        "landscape": "https://...",
        "tiny": "https://..."
      }
    }
  ],
  "next_page": "https://api.pexels.com/v1/search?page=2&..."
}
```

### Ключевые слова для поиска

| Query | Ожидаемое количество | Описание |
|-------|---------------------|----------|
| "galaxy" | 9,000+ | Галактики, космические виды |
| "nebula" | 1,000+ | Туманности, яркие цвета |
| "space stars" | 5,000+ | Звездное небо |
| "cosmos" | 3,000+ | Общий космос |
| "milky way" | 2,000+ | Млечный путь |

**Рекомендуемая стратегия:**
```python
QUERIES = [
    ("galaxy", 150),      # 2 страницы
    ("nebula", 120),      # 2 страницы
    ("space stars", 120), # 2 страницы
    ("cosmos", 80),       # 1 страница
    ("milky way", 30),    # 1 страница (часть)
]
# Итого: ~500 уникальных изображений
```

## Architecture Patterns

### Recommended Project Structure
```
assets/
└── images/
    └── cosmic/                 # 500 космических изображений
        ├── galaxy_001.jpg
        ├── galaxy_002.jpg
        ├── nebula_001.jpg
        ├── ...
        └── cosmos_500.jpg

scripts/
└── download_cosmic_images.py   # Единый скрипт скачивания + обработки
```

### Pattern 1: Direct API + Download (No SDK)
**What:** Прямые HTTP запросы без SDK для максимальной простоты
**When to use:** Разовая задача скачивания
**Example:**
```python
#!/usr/bin/env python3
"""Download 500 cosmic images from Pexels."""
# Source: Pexels API documentation

import os
import time
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
OUTPUT_DIR = Path("assets/images/cosmic")
TARGET_SIZE = (1280, 720)  # Telegram optimal
QUALITY = 85  # JPEG quality

QUERIES = [
    ("galaxy", 2),       # 2 pages x 80 = 160 images
    ("nebula", 2),       # 2 pages x 80 = 160 images
    ("space stars", 2),  # 2 pages x 80 = 160 images
    ("cosmos", 1),       # 1 page x 80 = 80 images
]

def fetch_page(query: str, page: int) -> list[dict]:
    """Fetch one page of results from Pexels."""
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "page": page,
        "per_page": 80,
        "orientation": "landscape",
        "size": "large",
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json().get("photos", [])


def download_and_process(photo: dict, output_path: Path) -> bool:
    """Download image and resize to Telegram optimal size."""
    try:
        # Use 'large' src for good quality without huge download
        image_url = photo["src"]["large"]
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        # Open and resize
        img = Image.open(BytesIO(response.content))
        img = img.convert("RGB")

        # Resize maintaining aspect ratio, then crop to exact size
        img.thumbnail((TARGET_SIZE[0] * 2, TARGET_SIZE[1] * 2), Image.Resampling.LANCZOS)

        # Center crop to exact dimensions
        width, height = img.size
        left = (width - TARGET_SIZE[0]) // 2
        top = (height - TARGET_SIZE[1]) // 2
        img = img.crop((left, top, left + TARGET_SIZE[0], top + TARGET_SIZE[1]))

        # Save
        img.save(output_path, "JPEG", quality=QUALITY, optimize=True)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    if not PEXELS_API_KEY:
        raise ValueError("Set PEXELS_API_KEY environment variable")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    seen_ids = set()  # Avoid duplicates

    for query, pages in QUERIES:
        for page in range(1, pages + 1):
            print(f"Fetching: {query} (page {page})...")
            photos = fetch_page(query, page)

            for photo in photos:
                if photo["id"] in seen_ids:
                    continue
                seen_ids.add(photo["id"])

                filename = f"{query.replace(' ', '_')}_{downloaded:04d}.jpg"
                output_path = OUTPUT_DIR / filename

                if download_and_process(photo, output_path):
                    downloaded += 1
                    print(f"  [{downloaded}] {filename}")

                if downloaded >= 500:
                    print(f"\nDownloaded {downloaded} images to {OUTPUT_DIR}")
                    return

            time.sleep(2)  # Rate limit safety

    print(f"\nDownloaded {downloaded} images to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
```

### Pattern 2: Concurrent Downloads (Faster)
**What:** Параллельное скачивание для ускорения
**When to use:** Если нужно быстрее
**Example:**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_batch(photos: list[dict], start_index: int) -> int:
    """Download batch of photos concurrently."""
    downloaded = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}
        for i, photo in enumerate(photos):
            filename = f"cosmic_{start_index + i:04d}.jpg"
            output_path = OUTPUT_DIR / filename
            futures[executor.submit(download_and_process, photo, output_path)] = filename

        for future in as_completed(futures):
            if future.result():
                downloaded += 1

    return downloaded
```

### Anti-Patterns to Avoid
- **Слишком много запросов** — соблюдать 2s delay между API calls
- **Скачивание original** — слишком большие файлы, использовать 'large'
- **Игнорирование дубликатов** — один и тот же photo.id может быть в разных queries
- **Hardcoded API key** — использовать environment variable

## Telegram Image Optimization

### Optimal Sizes
| Use Case | Size | Format | Notes |
|----------|------|--------|-------|
| Photo message | 1280x720 | JPEG 85% | Telegram сжимает до 720p |
| Document mode | Original | Any | Без сжатия, но неудобно |
| Thumbnail | 320x180 | JPEG | Preview |

### Why 1280x720
- Telegram автоматически сжимает фото до 1280x720 (720p HD)
- Отправка большего размера = лишний трафик + ожидание сжатия
- 16:9 aspect ratio = красиво на всех устройствах

### File Size Target
- Target: 100-300KB per image
- JPEG quality 85% дает отличное качество при малом размере
- PNG не рекомендуется для фотографий (больше размер, нет преимуществ)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Image resize | Manual pixel loops | `PIL.Image.thumbnail()` | Optimized, handles aspect ratio |
| Aspect ratio crop | Complex math | `PIL.ImageOps.fit()` | Battle-tested |
| HTTP requests | Socket code | `requests.get()` | Handles everything |
| Concurrent downloads | Manual threading | `ThreadPoolExecutor` | Clean API, exception handling |
| Rate limiting | Busy loops | `time.sleep()` | Simple, effective |

**Key insight:** Для разовой задачи (скачать 500 файлов один раз) простота важнее оптимизации. Скрипт < 100 строк.

## Common Pitfalls

### Pitfall 1: Rate Limit 429
**What goes wrong:** API возвращает 429 Too Many Requests
**Why it happens:** Слишком быстрые запросы к API (не к скачиванию!)
**How to avoid:**
- `time.sleep(2)` между API calls (search requests)
- Скачивание файлов НЕ считается в rate limit (это CDN, не API)
**Warning signs:** HTTP 429, X-Ratelimit-Remaining: 0

### Pitfall 2: Дубликаты
**What goes wrong:** Одно и то же изображение скачивается несколько раз
**Why it happens:** Разные queries возвращают одни и те же популярные фото
**How to avoid:**
- Отслеживать `photo.id` в set
- Пропускать уже скачанные
**Warning signs:** Визуально одинаковые файлы

### Pitfall 3: Битые изображения
**What goes wrong:** Некоторые файлы не открываются
**Why it happens:** Сетевые ошибки, таймауты
**How to avoid:**
- try/except при скачивании
- Проверка size > 0 после скачивания
- Retry с backoff
**Warning signs:** FileNotFoundError, PIL.UnidentifiedImageError

### Pitfall 4: Слишком большие файлы
**What goes wrong:** Медленная отправка в Telegram
**Why it happens:** Использование 'original' вместо 'large'
**How to avoid:**
- Использовать src.large (~1920px)
- Resize до 1280x720
- JPEG quality 85%
**Warning signs:** Файлы > 1MB

### Pitfall 5: API Key в репозитории
**What goes wrong:** Ключ утекает публично
**Why it happens:** Hardcoded или .env в git
**How to avoid:**
- `os.getenv("PEXELS_API_KEY")`
- .env в .gitignore
**Warning signs:** Git history содержит ключ

## Лицензирование

### Pexels License (подтверждено)
| Аспект | Статус | Детали |
|--------|--------|--------|
| Коммерческое использование | **ДА** | Разрешено в приложениях, ботах |
| Атрибуция | **НЕ ТРЕБУЕТСЯ** | Опционально |
| Модификация | **ДА** | Resize, crop, filter — разрешено |
| Количество | **Без лимита** | Можно скачать хоть 10,000 |
| Ограничения | Есть | Нельзя конкурировать с Pexels |

**Источник:** [Pexels License](https://help.pexels.com/hc/en-us/articles/360042295174)

### Что нельзя
- Создавать конкурирующий stock photo сервис
- Продавать изображения без модификации
- Идентифицировать людей на фото без согласия

### Что можно (наш случай)
- Использовать в коммерческом Telegram боте
- Модифицировать (resize, crop)
- НЕ указывать атрибуцию (но приветствуется)

## Getting Pexels API Key

```bash
# 1. Зайти на https://www.pexels.com/api/
# 2. Нажать "Get Started"
# 3. Создать аккаунт (бесплатно)
# 4. Запросить API access (мгновенное одобрение)
# 5. Скопировать API key

# Добавить в .env:
echo "PEXELS_API_KEY=your_key_here" >> .env
```

**Время получения ключа:** ~2 минуты (регистрация + instant approval)

## Open Questions

### 1. Качество космических изображений на Pexels
- **What we know:** 9,000+ galaxy, 1,000+ nebula фото
- **What's unclear:** Сколько из них подходящего качества
- **Recommendation:** Тестовый запрос на 10-20 фото, визуальная проверка

### 2. Дубликаты между queries
- **What we know:** Популярные фото повторяются
- **What's unclear:** Какой % дубликатов между "galaxy" и "cosmos"
- **Recommendation:** Tracking по photo.id, запрашивать с запасом (600 для получения 500 уникальных)

### 3. Хранение в git vs external storage
- **What we know:** 500 x 200KB = ~100MB
- **What's unclear:** Git LFS? S3? Напрямую в repo?
- **Recommendation:** Для MVP - напрямую в repo, потом можно мигрировать

## Sources

### Primary (HIGH confidence)
- [Pexels API Documentation](https://www.pexels.com/api/documentation/) - Endpoints, pagination, rate limits
- [Pexels License](https://help.pexels.com/hc/en-us/articles/360042295174) - Commercial use allowed
- [Pillow Documentation](https://pillow.readthedocs.io/en/stable/) - Image resize methods

### Secondary (MEDIUM confidence)
- [pexels-api-py GitHub](https://github.com/meetsohail/pexels-api-py) - Python SDK reference
- [Telegram Image Guide](https://safeimagekit.com/blog/the-definitive-guide-for-image-sizes-for-telegram) - 1280x720 optimal

### Tertiary (LOW confidence)
- WebSearch results about cosmic image availability on Pexels

## Metadata

**Confidence breakdown:**
- API и rate limits: HIGH - Официальная документация
- Лицензирование: HIGH - Официальная страница лицензии
- Наличие контента: MEDIUM - Подтверждено поиском, нужен тест
- Telegram optimization: HIGH - Официальные данные о сжатии

**Research date:** 2026-01-24
**Valid until:** 60 дней (API стабилен)

---

## Сравнение: 500 vs 17 изображений

| Аспект | 500 космических | 17 специфических |
|--------|-----------------|------------------|
| WOW эффект | Высокий (всегда разное) | Средний (повторяется) |
| Время скачивания | ~5-7 минут | ~1 минута |
| Размер хранения | ~100MB | ~17MB |
| Сложность | Простой скрипт | Сложнее (разные queries) |
| Единый стиль | Естественный (все космос) | Требует обработки |
| Telegram кэширование | Много file_id | Мало file_id |

**Рекомендация:** 500 космических изображений — лучший UX с минимальными затратами времени.
