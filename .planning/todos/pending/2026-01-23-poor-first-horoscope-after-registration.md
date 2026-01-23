---
created: 2026-01-23T08:00
title: Первый прогноз после регистрации отвратительный и неполный
area: ai
files:
  - src/bot/handlers/onboarding.py
  - src/services/ai/prompts.py:HoroscopePrompt
  - src/services/ai/client.py:generate_horoscope
---

## Problem

**Наблюдение:** После ввода даты рождения пользователь получает "отвратительный и неполный" прогноз.

**Почему это критично:**
1. Первое впечатление от AI качества
2. Immediate value после регистрации
3. Влияет на retention и доверие к боту
4. Может быть mock horoscope вместо AI

**Возможные причины:**
- Используется mock horoscope вместо AI
- HoroscopePrompt недостаточно детальный
- Timeout на AI и показывается fallback
- Неправильная валидация (урезает текст)

## Solution

**Investigation:**
1. Проверить какой прогноз показывается после регистрации (mock или AI)
2. Прочитать код onboarding flow
3. Проверить logs для первого horoscope показа

**Fixes:**
- Убедиться что используется AI, не mock
- Улучшить HoroscopePrompt для первого показа
- Добавить специальный "welcome horoscope" с персонализацией по дате рождения
- Увеличить timeout для первого запроса
- Добавить retry logic

**Альтернатива:**
- Показывать "Карту дня" таро вместо гороскопа (быстрее, визуальнее)

**Приоритет:** CRITICAL - первое впечатление от AI
