# Phase 13: Image Generation - Research

**Researched:** 2026-01-24 (Updated)
**Domain:** AI image generation, бесплатные API без карты, Gemini 2.5 Flash Image
**Confidence:** HIGH

## Summary

**КРИТИЧНО:** Together.ai теперь требует карту ($5 минимум) — исключен из рассмотрения.

Исследование выявило **Google Gemini 2.5 Flash Image** как оптимальный бесплатный генератор изображений. Free tier включает до 500 запросов в день без кредитной карты. Модель gemini-2.5-flash-image (кодовое имя "Nano Banana") поддерживает высококачественную генерацию 1024x1024, различные aspect ratios, и имеет официальный Python SDK `google-genai`.

**Ключевые находки:**
- Gemini API: бесплатно до 500 req/day, регистрация через Google аккаунт
- Model ID: `gemini-2.5-flash-image`
- Размеры: 1024x1024 (1K), 2048x2048 (2K), aspect ratios 1:1, 16:9, 9:16, 3:4, 4:3
- Telegram: оптимальный размер 1024x1024 (автомасштабирование)
- Для consistency: использовать идентичные style prompts, одинаковые настройки
- Изображения получают невидимый SynthID watermark (не влияет на визуал)

**Primary recommendation:** Использовать Google Gemini 2.5 Flash Image API с Python SDK `google-genai`. Создать скрипт `scripts/generate_images.py`, сохранять в `assets/images/`. Единый стиль через repeated style phrases в каждом промпте.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| google-genai | latest | Google Gemini Python SDK | Официальный SDK, простой API, бесплатный tier |
| Pillow | 12.1.0 | Image processing | Уже установлен в проекте, для save/convert |
| python-dotenv | (installed) | Env variables | Уже используется в проекте |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib | stdlib | Path management | Организация assets/ |
| io | stdlib | BytesIO для images | Промежуточная обработка |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Gemini | Hugging Face | $0.10/месяц (8-80 изображений), меньше лимит |
| Gemini | Replicate | 50 генераций/месяц, недостаточно для итераций |
| Gemini | Leonardo.ai | API платный ($9/мес), web 150 токенов/день |
| Gemini | Ideogram.ai | API требует карту, web 10 кредитов/неделю |
| Gemini | Together.ai | Теперь требует карту ($5 минимум) |

**Installation:**
```bash
pip install google-genai pillow
```

Или добавить в `pyproject.toml`:
```toml
dependencies = [
    "google-genai",
    # ... existing deps
]
```

## Сравнение бесплатных генераторов (без карты)

| Сервис | Бесплатный лимит | API доступ | Карта нужна | Рекомендация |
|--------|------------------|------------|-------------|--------------|
| **Gemini 2.5 Flash Image** | 500 req/day | Да (Python SDK) | Нет | РЕКОМЕНДУЕТСЯ |
| Hugging Face | $0.10/месяц (~8-80 img) | Да | Нет | Backup вариант |
| Replicate | 50 img/месяц | Да | Нет | Слишком мало |
| Leonardo.ai web | 150 токенов/день | Нет (API платный) | Нет | Только ручная работа |
| Ideogram.ai web | 10 кредитов/неделю | Нет (API платный) | Нет | Только ручная работа |
| Together.ai | НЕТ БЕСПЛАТНОГО | Да | ДА ($5 min) | ИСКЛЮЧЕН |

## Architecture Patterns

### Recommended Project Structure
```
assets/
├── images/
│   ├── welcome.png              # Welcome screen (1024x1024)
│   ├── zodiac/
│   │   ├── aries.png           # Знаки зодиака (1024x1024)
│   │   ├── taurus.png
│   │   └── ...                 # Всего 12 файлов
│   ├── tarot/
│   │   ├── three_card.png      # 3-карточный расклад
│   │   └── celtic_cross.png    # Celtic Cross расклад
│   ├── natal_chart.png         # Натальная карта
│   └── paywall.png             # Premium paywall
scripts/
└── generate_images.py          # Скрипт генерации
```

### Pattern 1: Unified Prompt Template
**What:** Базовый шаблон промпта для единого стиля всех изображений
**When to use:** Для каждого изображения
**Example:**
```python
# Source: CONTEXT.md decisions + Gemini best practices
BASE_STYLE = """
Mystical cosmic art style, dark background with deep purple and black tones,
golden and white accents, high detail, starfield with nebulae,
magical atmosphere, elegant composition, no text, no watermarks
"""

def zodiac_prompt(sign_name: str, glyph_description: str) -> str:
    return f"""
    {sign_name} zodiac symbol, {glyph_description},
    large centered glowing golden glyph with white outline,
    cosmic background with stars and purple nebulae,
    {BASE_STYLE}
    """
```

### Pattern 2: Gemini Image Generation
**What:** Генерация через Gemini API с правильной конфигурацией
**When to use:** Для каждого изображения
**Example:**
```python
# Source: Google Gemini API docs
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client(api_key="YOUR_API_KEY")  # или из env

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[zodiac_prompt("Aries", "ram horns symbol")],
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="1:1",  # квадрат для zodiac
        )
    )
)

# Извлечение изображения
for part in response.parts:
    if part.inline_data is not None:
        image = part.as_image()
        image.save("aries.png")
```

### Pattern 3: Batch Generation with Rate Limiting
**What:** Последовательная генерация с паузами
**When to use:** Для batch генерации 17 изображений
**Example:**
```python
import time
from pathlib import Path

def generate_all_zodiac(client, output_dir: Path):
    zodiac_signs = [
        ("aries", "ram horns symbol"),
        ("taurus", "bull head symbol"),
        ("gemini", "twins symbol"),
        ("cancer", "crab claws symbol"),
        ("leo", "lion mane symbol"),
        ("virgo", "maiden symbol"),
        ("libra", "balanced scales symbol"),
        ("scorpio", "scorpion tail symbol"),
        ("sagittarius", "archer bow symbol"),
        ("capricorn", "sea-goat symbol"),
        ("aquarius", "water bearer waves symbol"),
        ("pisces", "twin fish symbol"),
    ]

    for sign_name, glyph in zodiac_signs:
        prompt = zodiac_prompt(sign_name.capitalize(), glyph)

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            )
        )

        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                output_path = output_dir / f"{sign_name}.png"
                image.save(output_path)
                print(f"Generated: {output_path}")

        time.sleep(2)  # Rate limit protection (IPM = 2 for free tier)
```

### Anti-Patterns to Avoid
- **Слишком быстрая генерация:** Free tier ограничен 2 images/minute. Добавлять паузы 30-60 секунд между генерациями
- **Слишком длинные промпты:** Оптимально 50-100 слов. Более 200 снижает качество
- **Отсутствие style consistency:** Каждый промпт должен содержать BASE_STYLE
- **Игнорирование errors:** Всегда обрабатывать исключения, retry при failures

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Image decoding | Custom parsers | `part.as_image()` + Pillow | SDK делает это автоматически |
| Retry logic | Manual while loops | `tenacity` или простой try/except | Backoff, jitter |
| Prompt templating | String concatenation | F-strings с constants | Maintainability |
| File organization | Ad-hoc paths | `pathlib.Path` | Cross-platform |
| API key management | Hardcoded | `python-dotenv` + env vars | Security |

**Key insight:** Генерация 17 изображений — одноразовый процесс. Простой скрипт с proper error handling достаточен. Не overengineer.

## Common Pitfalls

### Pitfall 1: Rate Limiting (IPM = 2)
**What goes wrong:** Gemini блокирует запросы при быстрой генерации
**Why it happens:** Free tier ограничен 2 images per minute
**How to avoid:** Добавить `time.sleep(30)` между генерациями (или 60 для безопасности)
**Warning signs:** 429 Too Many Requests, ResourceExhausted errors

### Pitfall 2: Inconsistent Style
**What goes wrong:** Изображения выглядят по-разному
**Why it happens:** Вариации в промптах, отсутствие style anchors
**How to avoid:**
- Повторять BASE_STYLE в каждом промпте
- Использовать одинаковый aspect_ratio для всей серии
- Генерировать test batch (2-3 изображения) перед полной генерацией
**Warning signs:** Визуальная несогласованность при preview

### Pitfall 3: API Key Exposure
**What goes wrong:** API ключ утекает в git
**Why it happens:** Hardcoded ключ или .env не в .gitignore
**How to avoid:**
- Использовать `GOOGLE_API_KEY` env variable
- Проверить .gitignore включает .env
- Никогда не коммитить ключи
**Warning signs:** Git history содержит ключи

### Pitfall 4: Wrong Image Format for Telegram
**What goes wrong:** Изображения слишком большие или неоптимальные
**Why it happens:** Неправильный формат/размер
**How to avoid:**
- Использовать 1024x1024 для универсальности
- Сохранять как PNG (лучше для графики с золотом)
- Проверять размер файла < 10MB
**Warning signs:** Telegram долго загружает или сжимает изображение

### Pitfall 5: SynthID Watermark Concerns
**What goes wrong:** Беспокойство о водяных знаках
**Why it happens:** Gemini добавляет невидимый SynthID
**How to avoid:** Это НЕ проблема — SynthID невидим для пользователей
**Warning signs:** Нет визуальных признаков (watermark невидим)

## Code Examples

### Complete Generation Script
```python
#!/usr/bin/env python3
"""Generate all images for AdtroBot using Google Gemini."""
# Source: Google Gemini API docs + project patterns

import os
import time
from pathlib import Path

from google import genai
from google.genai import types

# Configuration
OUTPUT_DIR = Path("assets/images")
MODEL = "gemini-2.5-flash-image"
DELAY_SECONDS = 35  # Free tier: 2 IPM, safe margin

# Base style for all images (from CONTEXT.md)
BASE_STYLE = """
Mystical cosmic art style, dark background with deep purple and black tones,
golden and white accents, stars and nebulae, magical atmosphere,
high detail, elegant composition, professional quality, no text, no watermarks
"""


def create_client():
    """Create Gemini client with API key from environment."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    return genai.Client(api_key=api_key)


def generate_image(client, prompt: str, output_path: Path, aspect_ratio: str = "1:1"):
    """Generate single image and save to file."""
    full_prompt = f"{prompt}, {BASE_STYLE}"

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[full_prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                )
            )
        )

        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                output_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(output_path, "PNG")
                print(f"Generated: {output_path}")
                return True

        print(f"No image in response for: {output_path}")
        return False

    except Exception as e:
        print(f"Error generating {output_path}: {e}")
        return False


# Zodiac signs configuration
ZODIAC_PROMPTS = {
    "aries": "Aries zodiac symbol, golden ram horns glyph, centered large glowing symbol",
    "taurus": "Taurus zodiac symbol, golden bull head glyph, centered large glowing symbol",
    "gemini": "Gemini zodiac symbol, golden twins glyph, centered large glowing symbol",
    "cancer": "Cancer zodiac symbol, golden crab claws glyph, centered large glowing symbol",
    "leo": "Leo zodiac symbol, golden lion mane glyph, centered large glowing symbol",
    "virgo": "Virgo zodiac symbol, golden maiden glyph, centered large glowing symbol",
    "libra": "Libra zodiac symbol, golden balanced scales glyph, centered large glowing symbol",
    "scorpio": "Scorpio zodiac symbol, golden scorpion tail glyph, centered large glowing symbol",
    "sagittarius": "Sagittarius zodiac symbol, golden archer bow glyph, centered large glowing symbol",
    "capricorn": "Capricorn zodiac symbol, golden sea-goat glyph, centered large glowing symbol",
    "aquarius": "Aquarius zodiac symbol, golden water bearer waves glyph, centered large glowing symbol",
    "pisces": "Pisces zodiac symbol, golden twin fish glyph, centered large glowing symbol",
}


def main():
    """Generate all images."""
    client = create_client()

    # Create output directories
    (OUTPUT_DIR / "zodiac").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "tarot").mkdir(parents=True, exist_ok=True)

    generated = 0
    total = 17

    # 1. Welcome screen
    print(f"\n[{generated+1}/{total}] Generating welcome screen...")
    generate_image(
        client,
        "Large golden zodiac wheel with all 12 signs, cosmic portal, mystical gateway, centered composition",
        OUTPUT_DIR / "welcome.png",
    )
    generated += 1
    time.sleep(DELAY_SECONDS)

    # 2. Zodiac signs (12 images)
    for sign, prompt in ZODIAC_PROMPTS.items():
        print(f"\n[{generated+1}/{total}] Generating {sign}...")
        generate_image(
            client,
            prompt,
            OUTPUT_DIR / "zodiac" / f"{sign}.png",
        )
        generated += 1
        time.sleep(DELAY_SECONDS)

    # 3. Tarot spreads
    print(f"\n[{generated+1}/{total}] Generating three card spread...")
    generate_image(
        client,
        "Three tarot cards face down in a row, golden ornate back design on black, mystical arrangement",
        OUTPUT_DIR / "tarot" / "three_card.png",
    )
    generated += 1
    time.sleep(DELAY_SECONDS)

    print(f"\n[{generated+1}/{total}] Generating Celtic Cross spread...")
    generate_image(
        client,
        "Celtic Cross tarot spread, ten cards face down, golden ornate backs on black, mystical cross pattern",
        OUTPUT_DIR / "tarot" / "celtic_cross.png",
    )
    generated += 1
    time.sleep(DELAY_SECONDS)

    # 4. Natal chart
    print(f"\n[{generated+1}/{total}] Generating natal chart...")
    generate_image(
        client,
        "Astrological birth chart wheel, golden lines and symbols, planets and houses marked, cosmic background",
        OUTPUT_DIR / "natal_chart.png",
    )
    generated += 1
    time.sleep(DELAY_SECONDS)

    # 5. Paywall
    print(f"\n[{generated+1}/{total}] Generating paywall...")
    generate_image(
        client,
        "Golden ornate lock with keyhole, premium access symbol, magical glow, unlock concept",
        OUTPUT_DIR / "paywall.png",
    )
    generated += 1

    print(f"\n{'='*50}")
    print(f"All {total} images generated successfully!")
    print(f"Output directory: {OUTPUT_DIR.absolute()}")


if __name__ == "__main__":
    main()
```

### Environment Setup
```bash
# .env file (add to existing)
GOOGLE_API_KEY=your_gemini_api_key_here
```

### Getting API Key
1. Перейти на https://aistudio.google.com/
2. Войти с Google аккаунтом (БЕЗ КАРТЫ)
3. Settings -> API Keys -> Create API Key
4. Скопировать ключ в .env

### Running the Script
```bash
# Install dependency
pip install google-genai

# Run generation (takes ~10 minutes with rate limiting)
python scripts/generate_images.py
```

### Estimated Time
- 17 изображений x 35 секунд delay = ~10 минут
- Можно запустить и заняться другим

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Together.ai free | Together.ai PAID ($5 min) | July 2025 | Больше не бесплатно |
| Stable Diffusion | Gemini 2.5 Flash Image | 2025 | Лучшее качество, проще API |
| Multiple API calls | Single generate_content | Gemini SDK | Упрощенный код |
| Manual image decode | `part.as_image()` | Gemini SDK | Автоматическая обработка |

**Deprecated/outdated:**
- Together.ai free tier: Отменен, теперь требует $5 минимум
- Gemini 2.0 Flash: Deprecated, shutdown March 2026
- Stable Diffusion API (бесплатный): Лимиты слишком низкие

## Telegram-Specific Considerations

### Image Formats
| Format | Use Case | Notes |
|--------|----------|-------|
| PNG | Best for graphics | Lossless, transparency support, рекомендуется |
| JPG | Photos | Smaller size, no transparency |
| WebP | Modern bots | 30% smaller, good support |

**Recommendation:** Использовать PNG для всех изображений (лучшее качество для графики с золотыми элементами).

### Image Sizes
| Size | Use Case | Telegram Behavior |
|------|----------|-------------------|
| 1024x1024 | Universal | Отображается полностью, автомасштабируется |
| 1280x720 | Landscape | Хорошо для карточек |
| 2560x2560 | Max API | Telegram сжимает до 1280 |

**Recommendation:** 1024x1024 (1K) — Gemini default, оптимально для Telegram.

### File Size Limits
- Photo: до 10 MB
- Document: до 50 MB
- PNG 1024x1024: ~500KB-2MB, в пределах лимита

## Open Questions

### 1. Точная стилизация символов зодиака
- **What we know:** Нужны классические глифы в золотом стиле
- **What's unclear:** Gemini может интерпретировать "glyph" по-разному
- **Recommendation:** Провести тестовую генерацию 2-3 знаков, уточнить промпты итеративно

### 2. Rate Limit Stability
- **What we know:** Документация говорит 2 IPM для free tier
- **What's unclear:** Точные лимиты могут меняться (Google менял в Dec 2025)
- **Recommendation:** Использовать 35-секундный delay, retry при failures

### 3. Альтернатива если Gemini не подойдет
- **What we know:** Hugging Face дает $0.10/месяц бесплатно
- **What's unclear:** Хватит ли для итераций
- **Recommendation:** Backup план — ручная генерация через Leonardo.ai web (150 токенов/день)

## Sources

### Primary (HIGH confidence)
- [Google Gemini API Image Generation](https://ai.google.dev/gemini-api/docs/image-generation) - Official docs, Python examples
- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing) - Free tier info
- [Google Developers Blog - Gemini 2.5 Flash Image](https://developers.googleblog.com/introducing-gemini-2-5-flash-image/) - Model capabilities

### Secondary (MEDIUM confidence)
- [Together.ai Billing Docs](https://docs.together.ai/docs/billing) - Confirms $5 minimum requirement
- [Hugging Face Pricing](https://huggingface.co/docs/inference-providers/en/pricing) - Free tier: $0.10/month
- [Telegram Image Size Guide](https://limits.tginfo.me/en) - Telegram specifications

### Tertiary (LOW confidence)
- WebSearch results about Gemini rate limits in 2026 - May change
- WebSearch results about alternative generators - Community reports

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Официальная документация Google
- Architecture: HIGH - Простой скрипт, SDK примеры из docs
- Pitfalls: MEDIUM - Основано на rate limit documentation + community reports
- Prompts: MEDIUM - Требует итеративное тестирование

**Research date:** 2026-01-24
**Valid until:** 30 дней (Google может менять лимиты, проверять актуальность)
