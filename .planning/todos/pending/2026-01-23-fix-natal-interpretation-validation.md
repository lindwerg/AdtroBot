---
created: 2026-01-23T17:45
title: Fix natal chart interpretation validation failure
area: ai
files:
  - src/services/ai/prompts.py:NatalChartPrompt
  - src/services/ai/validators.py:validate_natal_interpretation
  - src/bot/handlers/natal.py:handle_natal_chart
---

## Problem

AI генерирует интерпретацию натальной карты, но валидатор отклоняет её с ошибкой:
```
"natal_interpretation_validation_failed"
"error": "Value error, Отсутствуют разделы гороскопа (найдено 0/4)"
```

**Проявление:**
- Натальная карта (PNG) генерируется успешно
- AI запрос к OpenRouter проходит (chars: 2041)
- Но валидатор не находит секции (0/4 найдено)
- Пользователь видит: "Не удалось создать интерпретацию. Попробуй позже."

**Возможные причины:**
1. NatalChartPrompt генерирует output без нужных section headers
2. Валидатор ищет неправильные паттерны (несоответствие prompt ↔ validator)
3. AI модель (GPT-4o-mini) игнорирует структуру в промпте
4. Валидатор слишком строгий для natal интерпретаций

**Context from logs:**
- User: 7655820168 (premium, birth_date: 1997-01-31, time_known: true)
- Generated 2041 chars interpretation
- Validation attempt 1 failed
- Timestamp: 2026-01-23T14:41:35.222934Z

## Solution

**Investigation needed:**
1. Read actual AI output that failed validation (add debug logging)
2. Compare NatalChartPrompt expected structure vs validator patterns
3. Check if validator reuses HoroscopePrompt patterns (different requirements)
4. Test with real AI response to see what's missing

**Potential fixes:**
- Make NatalChartPrompt more explicit about section headers
- Adjust natal validator to match actual AI output format
- Add retry with clearer prompt if first attempt fails
- Use different validation strategy for natal vs horoscope

**Priority:** HIGH - blocks premium feature for all users
