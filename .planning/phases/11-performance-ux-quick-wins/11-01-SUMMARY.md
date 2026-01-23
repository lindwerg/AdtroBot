---
phase: 11
plan: 01
subsystem: bot-ux
tags: [typing-indicator, progress-feedback, aiogram, ux]

dependency_graph:
  requires: []
  provides:
    - progress-feedback-helper
    - typing-indicators-for-ai
  affects:
    - phase-12 (caching may reduce typing duration)

tech_stack:
  added: []
  patterns:
    - aiogram.ChatActionSender context manager
    - progress message + auto-delete pattern

key_files:
  created:
    - src/bot/utils/progress.py
  modified:
    - src/bot/handlers/horoscope.py
    - src/bot/handlers/tarot.py
    - src/bot/handlers/natal.py

decisions:
  - name: typing-interval-4s
    choice: interval=4.0 seconds
    reason: Telegram typing indicator expires after 5s, 4s refresh ensures continuous feedback

metrics:
  duration: ~3 min
  completed: 2026-01-23
---

# Phase 11 Plan 01: Typing Indicator & Progress Messages Summary

**One-liner:** Typing indicator + progress message helper для AI операций (гороскоп, таро, натальная карта)

## What Was Built

1. **Progress Helper (`src/bot/utils/progress.py`)**
   - `PROGRESS_MESSAGES` dict с 4 ключами: horoscope, tarot, natal, default
   - `generate_with_feedback()` - обертка для AI корутин с typing indicator
   - Автоматическое удаление progress message в finally блоке
   - ChatActionSender.typing() с interval=4.0 секунды

2. **Horoscope Handler Integration**
   - Premium horoscope в `show_zodiac_horoscope` обернут в progress helper
   - Premium horoscope в `show_horoscope_message` обернут в progress helper

3. **Tarot Handler Integration**
   - 3-card spread AI interpretation обернут в progress helper
   - Celtic Cross AI interpretation обернут в progress helper
   - Удален ручной `thinking_msg` в Celtic Cross

4. **Natal Handler Integration**
   - `show_natal_chart` обернут в progress helper (calculate + png + AI)
   - `show_detailed_natal` обернут в progress helper
   - Удалены ручные `loading_msg` сообщения

## Commits

| Hash | Message |
|------|---------|
| bb1bf1c | feat(11-01): add progress.py helper for AI feedback |
| fec87aa | feat(11-01): add typing indicator to horoscope handler |
| a831c66 | feat(11-01): add typing indicator to tarot and natal handlers |

## Technical Details

**Progress message flow:**
1. Пользователь запрашивает AI генерацию
2. Бот показывает progress message ("Генерирую гороскоп...")
3. Бот начинает typing indicator (обновляется каждые 4 сек)
4. AI завершает генерацию
5. Progress message автоматически удаляется
6. Результат отправляется пользователю

**Key pattern:**
```python
result = await generate_with_feedback(
    message=message,
    operation_type="horoscope",
    ai_coro=ai_service.generate_premium_horoscope(...),
)
```

## Deviations from Plan

None - план выполнен точно.

## Success Criteria Verification

- [x] `src/bot/utils/progress.py` создан с generate_with_feedback helper
- [x] Horoscope handler использует typing при AI генерации
- [x] Tarot handler использует typing при AI генерации (3-card и Celtic)
- [x] Natal handler использует typing при AI генерации
- [x] Все handlers компилируются без ошибок
- [x] Ручные loading сообщения заменены на единый progress helper

## Next Phase Readiness

**Blockers:** None
**Ready for:** Phase 11 Plan 02 (text formatting) or any other Phase 11 plan
