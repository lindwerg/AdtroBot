---
created: 2026-01-23T07:59
title: Долгий ответ при первом /start
area: performance
files:
  - src/bot/handlers/start.py:cmd_start
  - src/db/models/user.py
  - src/bot/middlewares/db_middleware.py
---

## Problem

**Наблюдение:** При первом нажатии /start пользователь долго ждет ответа.

**Возможные причины:**
1. Медленный DB query (первое подключение)
2. Синхронная обработка onboarding
3. Долгая инициализация middleware
4. Webhook latency
5. Cold start на Railway (если dyno спит)

**Почему это критично:**
- Первое впечатление
- Пользователь может закрыть бота до ответа
- Высокий bounce rate на onboarding

## Solution

**Investigation needed:**
1. Добавить timing logs в cmd_start handler
2. Замерить DB query time
3. Проверить Railway cold start time
4. Добавить health check warming

**Potential fixes:**
- Оптимизировать DB queries (indexes, connection pooling)
- Async всё что можно
- Keep-alive для Railway dyno (scheduled ping)
- Preload ресурсов (deck, prompts)
- Показать "Загружаю..." сразу, потом обновить

**Приоритет:** HIGH - влияет на retention
