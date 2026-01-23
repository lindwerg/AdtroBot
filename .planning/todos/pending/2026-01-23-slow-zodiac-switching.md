---
created: 2026-01-23T08:03
title: Долгое переключение между знаками зодиака
area: performance
files:
  - src/bot/handlers/horoscope.py:handle_zodiac_callback
  - src/services/ai/client.py:generate_horoscope
  - src/bot/keyboards/horoscope.py
---

## Problem

**Наблюдение:** Пользователь переключается между знаками зодиака (inline keyboard 4x3) и каждый раз ждет 3-5 секунд.

**Почему это плохо:**
1. Плохой UX при сравнении знаков
2. Пользователь не будет исследовать другие знаки
3. Каждый клик = новый AI запрос (неэффективно)

**Связь с todo #1:** Если 12 гороскопов будут pre-generated, эта проблема решится автоматически.

## Solution

**Primary fix:** Реализовать background generation (см. todo #1)
- 12 гороскопов генерируются заранее
- Переключение мгновенное (читаем из кэша)

**Quick win (до background generation):**
- Aggressive caching с длинным TTL (6 часов)
- Preload первых 3 знаков при входе в меню
- Показать "loading..." animation при переключении

**UI improvement:**
- Добавить индикатор текущего знака в keyboard
- Disable кнопку текущего знака

**Приоритет:** HIGH - связан с todo #1
