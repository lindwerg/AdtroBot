---
created: 2026-01-23T08:04
title: Интегрировать FCM для push notifications
area: notifications
files:
  - src/services/notifications/fcm_service.py
  - src/services/scheduler/jobs.py:send_daily_notifications
---

## Problem

**Context:** Пользователь предоставил FCM credentials для настройки push notifications.

**Текущее состояние:**
- Notifications работают через Telegram Bot API (send_message)
- Нет native push notifications
- Зависимость от Telegram API availability

**FCM credentials provided:**
```
Test configuration:
149.154.167.40:443 DC 2
Production configuration:
149.154.167.50:443 DC 2
Public keys: [RSA keys provided]
```

**Зачем нужно FCM:**
1. Native push notifications (даже если бот закрыт)
2. Более надежная доставка
3. Аналитика delivery rate
4. Возможность персонализировать notifications

## Solution

**1. Setup FCM:**
- Установить firebase-admin SDK
- Инициализировать с provided credentials
- Создать FCM service wrapper

**2. Интеграция:**
- Сохранять FCM token пользователя (User.fcm_token)
- Обновлять при каждом входе
- Использовать FCM для daily notifications

**3. Fallback strategy:**
- Попробовать FCM push
- Если failed → fallback to Telegram Bot API send_message
- Log delivery status

**4. MTProto integration:**
- Использовать provided MTProto servers
- Test vs Production configuration
- Может улучшить delivery rate

**Research needed:**
- Как Telegram Bot API использует FCM
- Нужен ли отдельный Firebase project
- Совместимость MTProto с Bot API

**Приоритет:** MEDIUM - улучшение reliability
