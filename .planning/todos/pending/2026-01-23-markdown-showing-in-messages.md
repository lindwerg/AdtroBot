---
created: 2026-01-23T08:01
title: Видна разметка markdown в сообщениях
area: ui
files:
  - src/bot/handlers/horoscope.py
  - src/bot/handlers/tarot.py
  - src/bot/handlers/natal.py
  - src/services/ai/client.py
---

## Problem

**Наблюдение:** "Много где присутствует маркдаун, разметка" - пользователь видит сырой markdown вместо форматированного текста.

**Примеры где может быть:**
- Гороскопы (если AI генерирует markdown)
- Таро интерпретации
- Натальная карта описание
- Системные сообщения

**Почему это плохо:**
1. Выглядит непрофессионально
2. Текст трудно читать
3. AI очевидна (должна быть invisible)

**Возможные причины:**
- AI генерирует markdown (**, *, _)
- parse_mode не установлен
- Экранирование символов неправильное
- aiogram.utils.formatting не используется везде

## Solution

**Investigation:**
1. Найти все места где отправляются AI тексты
2. Проверить parse_mode в каждом answer/send
3. Проверить AI output (генерирует ли markdown)

**Fixes:**
- Убедиться что parse_mode='HTML' или 'Markdown' установлен
- Если AI генерирует markdown - использовать aiogram.utils.markdown parser
- Если не нужен markdown - попросить AI генерировать plain text
- Post-process AI output: удалять markdown символы если parse_mode не установлен

**Технически:**
```python
# Вариант 1: использовать markdown
await message.answer(text, parse_mode='Markdown')

# Вариант 2: strip markdown
import re
clean_text = re.sub(r'[*_`~]', '', ai_text)
```

**Приоритет:** MEDIUM - UX проблема
