# Phase 13: Image Generation - Research

**Researched:** 2026-01-24
**Domain:** AI image generation via Together.ai API, FLUX.1 schnell model, prompt engineering для мистического стиля
**Confidence:** HIGH

## Summary

Исследование подтвердило, что Together.ai + FLUX.1 schnell — оптимальный выбор для генерации изображений. FLUX.1 schnell (12B параметров) генерирует качественные изображения за 1-4 шага, бесплатно на Together.ai. Together Python SDK v1.5.35 полностью поддерживает async через `AsyncTogether`. Проект уже использует `openai` и `httpx` для async запросов — паттерн легко переносится.

**Ключевые находки:**
- Together.ai API: `https://api.together.xyz/v1/images/generations`
- Model ID: `black-forest-labs/FLUX.1-schnell-Free`
- Оптимальные параметры: steps=4, размеры до 1024x1024
- Telegram: оптимальный размер 1024x1024 (или 1280x720 для landscape)
- FLUX не поддерживает negative prompts — использовать positive framing
- Для consistency: фиксировать seed, повторять style phrases

**Primary recommendation:** Использовать Together Python SDK с AsyncTogether для генерации. Создать скрипт генерации в `scripts/generate_images.py`, сохранять в `assets/images/`. Фиксировать seed для единообразия всех 17 изображений.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| together | 1.5.35 | Together.ai Python SDK | Официальный SDK, async support, простой API |
| httpx | (installed) | HTTP клиент | Уже используется в проекте через aiogram |
| Pillow | 12.1.0 | Image processing | Уже установлен, для resize/convert |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| base64 | stdlib | Decode base64 images | Response format b64_json |
| pathlib | stdlib | Path management | Организация assets/ |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Together.ai | Replicate | Платный, но больше моделей |
| Together.ai | fal.ai | Быстрее, но требует отдельный аккаунт |
| FLUX.1 schnell | FLUX.1 pro | Качественнее, но платный |

**Installation:**
```bash
pip install together>=1.5.0
```

Или добавить в `pyproject.toml`:
```toml
"together (>=1.5.0,<2.0.0)",
```

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
# Source: CONTEXT.md decisions + Black Forest Labs prompting guide
BASE_STYLE = """
Mystical cosmic art style, dark background with deep purple and black tones,
golden and white accents, high detail, starfield with nebulae,
magical atmosphere, elegant composition, no text
"""

def zodiac_prompt(sign_name: str, glyph_description: str) -> str:
    return f"""
    {sign_name} zodiac symbol, {glyph_description},
    large centered glowing golden glyph with white outline,
    cosmic background with stars and purple nebulae,
    {BASE_STYLE}
    """
```

### Pattern 2: Seed-Based Consistency
**What:** Фиксированный seed для воспроизводимости стиля
**When to use:** Для всех изображений в серии
**Example:**
```python
# Source: Together.ai docs + FLUX consistency best practices
MASTER_SEED = 42  # Фиксированный seed для всей серии

response = client.images.generate(
    model="black-forest-labs/FLUX.1-schnell-Free",
    prompt=zodiac_prompt("Aries", "ram horns symbol"),
    width=1024,
    height=1024,
    steps=4,
    seed=MASTER_SEED,
    response_format="base64",
)
```

### Pattern 3: Async Batch Generation
**What:** Асинхронная генерация нескольких изображений
**When to use:** Для batch генерации 12 знаков зодиака
**Example:**
```python
# Source: Together Python SDK + asyncio patterns
import asyncio
from together import AsyncTogether

async def generate_zodiac_images():
    client = AsyncTogether()

    zodiac_signs = [
        ("aries", "ram horns symbol ♈"),
        ("taurus", "bull head symbol ♉"),
        # ... остальные знаки
    ]

    tasks = [
        generate_single_zodiac(client, name, glyph)
        for name, glyph in zodiac_signs
    ]

    results = await asyncio.gather(*tasks)
    return results
```

### Anti-Patterns to Avoid
- **Negative prompts:** FLUX.1 НЕ поддерживает negative prompts. Вместо "no text" использовать "clean image without any text or typography"
- **Prompt weights:** FLUX.1 НЕ поддерживает синтаксис `(word:1.5)`. Использовать "with emphasis on" или "featuring prominently"
- **Слишком длинные промпты:** Оптимально 30-80 слов. Более 100 слов снижают качество
- **Разные seeds:** Использование разных seeds нарушает визуальную консистентность

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Image decoding | Custom base64 parser | `base64.b64decode()` + Pillow | Edge cases, memory |
| Retry logic | Manual while loops | `tenacity` decorator | Backoff, jitter |
| Prompt templating | String concatenation | F-strings with constants | Maintainability |
| File organization | Ad-hoc paths | `pathlib.Path` | Cross-platform |

**Key insight:** Генерация изображений — это одноразовый процесс (17 файлов). Не нужна сложная инфраструктура. Простой скрипт с proper error handling достаточен.

## Common Pitfalls

### Pitfall 1: Rate Limiting
**What goes wrong:** Together.ai может ограничить запросы при быстрой batch генерации
**Why it happens:** Free tier имеет rate limits
**How to avoid:** Добавить delay между запросами (1-2 секунды), использовать retry с backoff
**Warning signs:** 429 Too Many Requests, временные таймауты

### Pitfall 2: Inconsistent Style
**What goes wrong:** Изображения выглядят по-разному несмотря на похожие промпты
**Why it happens:** Разные seeds, вариации в промптах, отсутствие style anchors
**How to avoid:**
- Фиксировать seed для всей серии
- Повторять 2-3 ключевых style phrases в каждом промпте
- Генерировать test batch перед финальной генерацией
**Warning signs:** Visual inconsistency при preview

### Pitfall 3: Wrong Image Dimensions
**What goes wrong:** Изображения обрезаются или растягиваются в Telegram
**Why it happens:** Неправильный aspect ratio, слишком большой размер
**How to avoid:** Использовать 1024x1024 для универсальности, или 1280x720 для landscape
**Warning signs:** Telegram preview показывает обрезанное изображение

### Pitfall 4: Unicode in Prompts
**What goes wrong:** Unicode символы (♈, ♉) некорректно обрабатываются
**Why it happens:** Encoding issues, модель не понимает glyphs
**How to avoid:** Использовать текстовые описания: "Aries ram horns symbol" вместо "♈"
**Warning signs:** Странные артефакты или отсутствие символа

### Pitfall 5: API Key Exposure
**What goes wrong:** API ключ утекает в git
**Why it happens:** Hardcoded ключ или .env не в .gitignore
**How to avoid:** Использовать TOGETHER_API_KEY env variable, проверить .gitignore
**Warning signs:** Git history содержит ключи

## Code Examples

### Complete Generation Script
```python
#!/usr/bin/env python3
"""Generate all images for AdtroBot."""
# Source: Together.ai docs + project patterns

import asyncio
import base64
from pathlib import Path

from together import AsyncTogether
from PIL import Image
import io

# Configuration
MASTER_SEED = 42
STEPS = 4
WIDTH = 1024
HEIGHT = 1024
MODEL = "black-forest-labs/FLUX.1-schnell-Free"
OUTPUT_DIR = Path("assets/images")

# Base style for all images (from CONTEXT.md)
BASE_STYLE = """
Mystical cosmic art style, dark background with deep purple and black tones,
golden and white accents, stars and nebulae, magical atmosphere,
high detail, elegant composition, professional quality, no text
"""


async def generate_image(
    client: AsyncTogether,
    prompt: str,
    output_path: Path,
    seed: int = MASTER_SEED,
) -> bool:
    """Generate single image and save to file."""
    try:
        response = await client.images.generate(
            model=MODEL,
            prompt=f"{prompt}, {BASE_STYLE}",
            width=WIDTH,
            height=HEIGHT,
            steps=STEPS,
            seed=seed,
            response_format="base64",
        )

        # Decode and save
        image_data = base64.b64decode(response.data[0].b64_json)
        image = Image.open(io.BytesIO(image_data))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, "PNG", optimize=True)

        print(f"Generated: {output_path}")
        return True

    except Exception as e:
        print(f"Error generating {output_path}: {e}")
        return False


# Zodiac signs configuration
ZODIAC_PROMPTS = {
    "aries": "Aries zodiac symbol, golden ram horns glyph, centered large symbol",
    "taurus": "Taurus zodiac symbol, golden bull head glyph, centered large symbol",
    "gemini": "Gemini zodiac symbol, golden twins glyph, centered large symbol",
    "cancer": "Cancer zodiac symbol, golden crab claws glyph, centered large symbol",
    "leo": "Leo zodiac symbol, golden lion mane glyph, centered large symbol",
    "virgo": "Virgo zodiac symbol, golden maiden glyph, centered large symbol",
    "libra": "Libra zodiac symbol, golden balanced scales glyph, centered large symbol",
    "scorpio": "Scorpio zodiac symbol, golden scorpion tail glyph, centered large symbol",
    "sagittarius": "Sagittarius zodiac symbol, golden archer bow glyph, centered large symbol",
    "capricorn": "Capricorn zodiac symbol, golden sea-goat glyph, centered large symbol",
    "aquarius": "Aquarius zodiac symbol, golden water bearer waves glyph, centered large symbol",
    "pisces": "Pisces zodiac symbol, golden twin fish glyph, centered large symbol",
}


async def main():
    """Generate all images."""
    client = AsyncTogether()

    # Create output directories
    (OUTPUT_DIR / "zodiac").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "tarot").mkdir(parents=True, exist_ok=True)

    # 1. Welcome screen
    await generate_image(
        client,
        "Large golden zodiac wheel with all 12 signs, cosmic portal, mystical gateway",
        OUTPUT_DIR / "welcome.png",
    )
    await asyncio.sleep(1)  # Rate limit protection

    # 2. Zodiac signs (12 images)
    for sign, prompt in ZODIAC_PROMPTS.items():
        await generate_image(
            client,
            prompt,
            OUTPUT_DIR / "zodiac" / f"{sign}.png",
        )
        await asyncio.sleep(1)

    # 3. Tarot spreads
    await generate_image(
        client,
        "Three tarot cards face down in a row, golden ornate back design on black, mystical arrangement",
        OUTPUT_DIR / "tarot" / "three_card.png",
    )
    await asyncio.sleep(1)

    await generate_image(
        client,
        "Celtic Cross tarot spread, ten cards face down, golden ornate backs on black, mystical cross pattern",
        OUTPUT_DIR / "tarot" / "celtic_cross.png",
    )
    await asyncio.sleep(1)

    # 4. Natal chart
    await generate_image(
        client,
        "Astrological birth chart wheel, golden lines and symbols, planets and houses marked, cosmic background",
        OUTPUT_DIR / "natal_chart.png",
    )
    await asyncio.sleep(1)

    # 5. Paywall
    await generate_image(
        client,
        "Golden ornate lock with keyhole, premium access symbol, magical glow, unlock concept",
        OUTPUT_DIR / "paywall.png",
    )

    print("\nAll images generated successfully!")


if __name__ == "__main__":
    asyncio.run(main())
```

### Environment Setup
```bash
# .env file
TOGETHER_API_KEY=your_api_key_here
```

### Running the Script
```bash
# Install dependency
pip install together

# Run generation
TOGETHER_API_KEY=xxx python scripts/generate_images.py
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Stable Diffusion | FLUX.1 | August 2024 | Лучшее качество, естественный язык |
| Many steps (20-50) | Few steps (1-4) | FLUX schnell | Быстрая генерация |
| Negative prompts | Positive framing | FLUX | Изменение prompting подхода |
| Keywords | Natural language | FLUX | Более понятные промпты |

**Deprecated/outdated:**
- Stable Diffusion XL: Всё ещё работает, но FLUX качественнее для мистического стиля
- Prompt weights `(word:1.5)`: Не поддерживается в FLUX

## Telegram-Specific Considerations

### Image Formats
| Format | Use Case | Notes |
|--------|----------|-------|
| PNG | Best for graphics | Lossless, transparency support |
| JPG | Photos | Smaller size, no transparency |
| WebP | Modern bots | 30% smaller, good support |

**Recommendation:** Использовать PNG для всех изображений (лучшее качество для графики с золотыми элементами).

### Image Sizes
| Size | Use Case | Telegram Behavior |
|------|----------|-------------------|
| 1024x1024 | Square (zodiac) | Отображается полностью |
| 1280x720 | Landscape | Хорошо для карточек |
| 720x1280 | Portrait | Вертикальные экраны |

**Recommendation:** 1024x1024 для универсальности. Telegram автоматически масштабирует.

### File Size Limits
- Photo: до 10 MB
- Document: до 50 MB
- При генерации PNG ~500KB-2MB, в пределах лимита

## Open Questions

### 1. Точная стилизация символов зодиака
- **What we know:** Нужны классические глифы (♈, ♉, etc.) в золотом стиле
- **What's unclear:** FLUX может интерпретировать "glyph" по-разному
- **Recommendation:** Провести тестовую генерацию 2-3 знаков, уточнить промпты итеративно

### 2. Интеграция в Phase 14
- **What we know:** Изображения будут отправляться через Telegram Bot API
- **What's unclear:** Использовать file_id caching или InputFile каждый раз
- **Recommendation:** Это scope Phase 14, не блокирует Phase 13

### 3. Together.ai Free Tier Limits
- **What we know:** 3 месяца бесплатно для FLUX.1 schnell
- **What's unclear:** Точные rate limits, что после 3 месяцев
- **Recommendation:** Для 17 изображений достаточно, но добавить 1-2 секунды delay

## Sources

### Primary (HIGH confidence)
- [Together.ai Images Overview](https://docs.together.ai/docs/images-overview) - API parameters, code examples
- [Black Forest Labs Prompting Guide](https://docs.bfl.ml/guides/prompting_summary) - Official FLUX prompting guide
- [Together Python SDK](https://pypi.org/project/together/) - v1.5.35, async support

### Secondary (MEDIUM confidence)
- [FLUX.1 Prompt Guide (giz.ai)](https://www.giz.ai/flux-1-prompt-guide/) - Community best practices
- [Segmind FLUX Prompting Guide](https://blog.segmind.com/flux-prompting-guide-image-creation/) - Style consistency tips
- [Telegram Image Size Guide](https://safeimagekit.com/blog/the-definitive-guide-for-image-sizes-for-telegram) - Telegram specifications

### Tertiary (LOW confidence)
- WebSearch results about zodiac AI generation - Prompt examples only

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Официальная документация Together.ai
- Architecture: HIGH - Простой скрипт, проверенные паттерны
- Pitfalls: MEDIUM - Основано на community best practices
- Prompts: MEDIUM - Требует итеративное тестирование

**Research date:** 2026-01-24
**Valid until:** 90 дней (AI image generation быстро развивается, но FLUX.1 стабилен)
