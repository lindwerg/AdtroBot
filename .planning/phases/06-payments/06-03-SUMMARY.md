---
phase: 06-payments
plan: 03
subsystem: bot-handlers
tags: [subscription, payments, handlers, scheduler]
depends_on: ["06-02"]
provides: ["subscription-handlers", "profile-integration", "expiry-notifications"]
affects: ["07-admin"]
tech-stack:
  added: []
  patterns: ["atomic-update", "cron-jobs"]
key-files:
  created:
    - src/bot/callbacks/subscription.py
    - src/bot/keyboards/subscription.py
    - src/bot/handlers/subscription.py
  modified:
    - src/bot/handlers/menu.py
    - src/bot/handlers/tarot.py
    - src/bot/handlers/__init__.py
    - src/bot/bot.py
    - src/services/scheduler.py
decisions:
  - key: retention-offer
    choice: "20% скидка при попытке отмены"
    rationale: "Retention strategy для уменьшения churn"
  - key: atomic-limit-check
    choice: "UPDATE ... WHERE count < limit RETURNING"
    rationale: "Предотвращает race conditions при конкурентных запросах"
  - key: auto-renewal-time
    choice: "09:00 MSK, за 1 день до истечения"
    rationale: "Дает время исправить failed payment до expiry notification"
metrics:
  duration: 4 min
  completed: 2026-01-23
---

# Phase 06 Plan 03: Subscription Handlers Summary

Subscription flow handlers с YooKassa интеграцией, profile статусом и автопродлением

## What Was Built

### Subscription Handlers (src/bot/handlers/subscription.py)

```python
# show_plans - показывает премиум фичи и тарифы
async def show_plans(message: Message, session: AsyncSession) -> None

# handle_plan_selection - создает payment и возвращает URL
@router.callback_query(SubscriptionCallback.filter(F.action == "plan"))
async def handle_plan_selection(...)

# Cancel flow с retention offer
@router.callback_query(SubscriptionCallback.filter(F.action == "cancel"))
async def handle_cancel_request(...)  # "скидка 20% если останетесь"

@router.callback_query(SubscriptionCallback.filter(F.action == "confirm_cancel"))
async def handle_confirm_cancel(...)  # Отменяет, сохраняет доступ до period_end
```

### Keyboards (src/bot/keyboards/subscription.py)

```python
def get_plans_keyboard() -> InlineKeyboardMarkup:
    # "Месяц — 299 р." -> SubscriptionCallback(action="plan", plan="monthly")
    # "Год — 2499 р. (-30%)" -> SubscriptionCallback(action="plan", plan="yearly")

def get_cancel_confirmation_keyboard() -> InlineKeyboardMarkup:
    # "Да, отменить" -> confirm_cancel
    # "Нет, остаюсь" -> keep
```

### Profile Integration (menu.py/menu_profile)

```python
# Subscription status in profile
subscription = await get_user_subscription(session, message.from_user.id)
if subscription and user.is_premium:
    lines.append(f"\nПодписка: Премиум до {until_str}")
    # Add cancel button if active
    builder.button(text="Отменить подписку", callback_data=SubscriptionCallback(action="cancel"))
else:
    lines.append("\nПодписка: Бесплатный тариф")
    lines.append(f"Раскладов сегодня: {user.tarot_spread_count}/{user.daily_spread_limit}")
```

### Atomic Limit Check (tarot.py)

```python
# Атомарный инкремент предотвращает race conditions
stmt = (
    update(User)
    .where(
        User.id == user.id,
        User.tarot_spread_count < User.daily_spread_limit,  # 1 free, 20 premium
    )
    .values(tarot_spread_count=User.tarot_spread_count + 1)
    .returning(User.tarot_spread_count)
)
result = await session.execute(stmt)
new_count = result.scalar_one_or_none()  # None if limit exceeded
```

### Scheduler Jobs (scheduler.py)

```python
# Auto-renewal: 09:00 Moscow, за 1 день до истечения
async def auto_renew_subscriptions():
    # Находит subscriptions с payment_method_id expiring in 1-2 days
    # Создает recurring payment
    # При успехе - продлевает period
    # При неудаче - status = past_due, уведомляет пользователя

# Expiry notification: 10:00 Moscow, за 3 дня до истечения
async def check_expiring_subscriptions():
    # "Напоминаем: ваша подписка истекает {date}"
```

## User Flow

1. **Пользователь нажимает "Подписка":**
   - Видит премиум фичи (20 раскладов, кельтский крест, детальные гороскопы)
   - Выбирает тариф: Месяц 299р или Год 2499р

2. **Оплата:**
   - Получает ссылку на YooKassa
   - После оплаты webhook активирует подписку

3. **Профиль:**
   - Показывает статус: "Премиум до DD.MM.YYYY" или "Бесплатный тариф"
   - Кнопка "Отменить подписку" для активных

4. **Отмена:**
   - Retention offer: "скидка 20% если останетесь"
   - При подтверждении: доступ сохраняется до period_end

5. **Автопродление:**
   - За 1 день: попытка recurring payment
   - За 3 дня: уведомление об истечении
   - При неудаче: статус past_due + уведомление

## Files Changed

| File | Change |
|------|--------|
| src/bot/callbacks/subscription.py | Created - SubscriptionCallback |
| src/bot/keyboards/subscription.py | Created - plans, cancel keyboards |
| src/bot/handlers/subscription.py | Created - show_plans, plan/cancel handlers |
| src/bot/handlers/menu.py | Updated - profile subscription status |
| src/bot/handlers/tarot.py | Updated - atomic limit check |
| src/bot/handlers/__init__.py | Added subscription_router export |
| src/bot/bot.py | Registered subscription_router |
| src/services/scheduler.py | Added auto_renew, expiry_check jobs |

## Decisions Made

1. **Retention offer при отмене** - "скидка 20%" для снижения churn
2. **Atomic limit check** - UPDATE...RETURNING предотвращает race conditions
3. **Auto-renewal в 09:00** - за час до expiry notification в 10:00
4. **past_due status** - при failed renewal, сохраняет доступ до period_end

## Deviations from Plan

None - план выполнен точно как написано.

## Verification Results

```
poetry run python -c "from src.bot.handlers.subscription import show_plans; print('OK')"
# OK

poetry run python -c "from src.bot.bot import dp; names = [r.name for r in dp.chain_tail]; assert 'subscription' in names"
# Router OK

poetry run python -c "from src.services.scheduler import get_scheduler; s = get_scheduler(); jobs = [j.id for j in s.get_jobs()]; assert 'check_expiring_subscriptions' in jobs; assert 'auto_renew_subscriptions' in jobs"
# Scheduler OK

poetry run ruff check src/
# No errors
```

## Next Phase Readiness

Phase 6 (Payments) complete. Ready for Phase 7 (Premium Features).

**Prerequisites for production:**
- [ ] Add YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY to Railway
- [ ] Configure YooKassa webhook URL: https://adtrobot-production.up.railway.app/webhook/yookassa
- [ ] Run `alembic upgrade head` on Railway (subscription/payment tables)
