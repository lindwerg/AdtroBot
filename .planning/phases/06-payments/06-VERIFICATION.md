---
phase: 06-payments
verified: 2026-01-23T02:10:00Z
status: passed
score: 6/6 must-haves verified
re_verification: false
---

# Phase 6: Payments Integration Verification Report

**Phase Goal:** Пользователь может оформить и управлять платной подпиской через ЮКасса

**Verified:** 2026-01-23T02:10:00Z

**Status:** PASSED (с human verification required)

**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Пользователь нажимает Подписка и видит тарифы | ✓ VERIFIED | subscription.py:38 show_plans(), menu.py:46 menu_subscription, keyboards:9 get_plans_keyboard() |
| 2 | Пользователь получает ссылку на оплату ЮКасса | ✓ VERIFIED | subscription.py:77 create_payment(), line 87 confirmation_url отправляется |
| 3 | Пользователь может отменить подписку в Профиле | ✓ VERIFIED | menu.py:85-100 показывает status + кнопку "Отменить", subscription.py:107 cancel flow |
| 4 | Лимит раскладов проверяется атомарно | ✓ VERIFIED | tarot.py:81-91 atomic UPDATE WHERE count < limit RETURNING |
| 5 | Пользователь получает уведомление за 3 дня до истечения | ✓ VERIFIED | scheduler.py:141 check_expiring_subscriptions, job registered line 42 cron 10:00 MSK |
| 6 | Подписка автоматически продлевается через recurring payment | ✓ VERIFIED | scheduler.py:198 auto_renew_subscriptions, creates recurring payment line 243, job registered line 33 cron 09:00 MSK |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/bot/handlers/subscription.py` | Subscription flow handlers | ✓ VERIFIED | 158 lines, show_plans + 4 handlers (plan/cancel/confirm/keep), imported by menu.py, no stubs, no TODOs |
| `src/bot/keyboards/subscription.py` | Subscription keyboards | ✓ VERIFIED | 40 lines, get_plans_keyboard (monthly/yearly) + cancel confirmation, imported by subscription.py, no stubs |
| `src/bot/handlers/tarot.py` | Updated limit check | ✓ VERIFIED | 349 lines, check_and_use_tarot_limit with atomic update, daily_spread_limit used on lines 85/98/245, no stubs |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| src/bot/handlers/subscription.py | src/services/payment/client.py | create_payment call | ✓ WIRED | Line 18 imports create_payment, line 77 calls it, line 87 uses result.confirmation.confirmation_url |
| src/bot/handlers/tarot.py | src/db/models/user.py | atomic limit check | ✓ WIRED | Line 10 imports update, line 85 WHERE User.tarot_spread_count < User.daily_spread_limit, line 88 RETURNING, line 91 checks None for race protection |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| PAY-01: YooKassa SDK интеграция | ✓ SATISFIED | 06-01-SUMMARY: yookassa 3.9.0 installed, payment/client.py uses SDK |
| PAY-02: Месячная подписка | ✓ SATISFIED | keyboards/subscription.py:14 "Месяц — 299 р.", PaymentPlan.MONTHLY |
| PAY-03: Автопродление | ✓ SATISFIED | scheduler.py:198 auto_renew_subscriptions with recurring payment |
| PAY-04: Отмена подписки | ✓ SATISFIED | subscription.py:107 cancel flow, menu.py:96-100 button in profile |
| PAY-05: Webhook idempotent | ✓ SATISFIED | main.py:85 /webhook/yookassa, service.py webhook_processed flag |
| PAY-06: Webhook обновляет статус | ✓ SATISFIED | 06-02-SUMMARY: process_webhook_event in service.py |
| PAY-07: Лимиты отслеживаются | ✓ SATISFIED | tarot.py:64 daily_spread_limit, menu.py:103 shows remaining |
| PAY-08: Atomic operations | ✓ SATISFIED | tarot.py:81-91 UPDATE WHERE count < limit RETURNING |
| PAY-09: Показываются лимиты | ✓ SATISFIED | menu.py:103 "Раскладов сегодня: X/Y", tarot.py:339-348 after spread |
| PAY-10: Уведомление об истечении | ✓ SATISFIED | scheduler.py:141 check_expiring_subscriptions 3 days before |
| BOT-05: Красивое форматирование | ✓ SATISFIED | subscription.py:27 PREMIUM_FEATURES formatted, retention offer line 126 |

**Coverage:** 11/11 requirements satisfied (10 PAY + 1 BOT)

### Anti-Patterns Found

**None** - All checks passed:

- ✓ No TODO/FIXME/placeholder comments
- ✓ No stub patterns (return null, empty handlers)
- ✓ No unused exports
- ✓ All handlers have real implementation
- ✓ `poetry run ruff check` passes without errors

### Human Verification Required

#### 1. Full Subscription Payment Flow

**Test:**
1. Start bot and navigate to "Подписка"
2. View premium features and plans
3. Select "Месяц — 299 р."
4. Click payment link
5. Complete payment on YooKassa
6. Return to bot

**Expected:**
- User sees premium features list (20 spreads, celtic cross, detailed horoscopes)
- Payment link opens YooKassa payment page
- After successful payment, webhook activates subscription
- User.is_premium becomes True
- User.daily_spread_limit becomes 20
- User receives confirmation message

**Why human:** Requires real YooKassa credentials, live payment gateway, webhook delivery

#### 2. Subscription Cancellation with Retention

**Test:**
1. Open "Профиль" with active subscription
2. See subscription status and cancel button
3. Click "Отменить подписку"
4. View retention offer ("скидка 20%")
5. Confirm cancellation

**Expected:**
- Profile shows "Премиум до DD.MM.YYYY" and cancel button
- Cancel confirmation shows retention message
- After confirmation: "Подписка отменена. Премиум-доступ сохранится до DD.MM.YYYY"
- Subscription.status becomes "canceled"
- Premium access continues until current_period_end

**Why human:** Requires active subscription, UI interaction with keyboard callbacks

#### 3. Auto-Renewal Before Expiry

**Test:**
1. Create subscription expiring tomorrow with saved payment_method_id
2. Wait for scheduler job at 09:00 Moscow time
3. Check subscription status and user notification

**Expected:**
- Scheduler job auto_renew_subscriptions runs at 09:00
- Creates recurring payment using saved payment_method_id
- On success: extends current_period_end by plan duration
- User receives "Подписка продлена до DD.MM.YYYY!"
- On failure: subscription.status becomes "past_due", user notified

**Why human:** Requires running scheduler, real subscription with payment_method_id, time-dependent cron trigger

### Gaps Summary

**NO GAPS FOUND** - All must-haves verified:

1. ✓ Subscription handlers fully implemented with YooKassa integration
2. ✓ Plan selection creates payment and returns URL
3. ✓ Cancel flow has retention offer ("скидка 20%")
4. ✓ Profile shows subscription status and cancel button
5. ✓ Tarot limits use atomic operations (race condition protection)
6. ✓ Auto-renewal job runs daily at 09:00 Moscow (1 day before expiry)
7. ✓ Expiry notification job runs daily at 10:00 Moscow (3 days before expiry)
8. ✓ Subscription router registered in bot dispatcher
9. ✓ No stub patterns or placeholder implementations

**Human verification required** for end-to-end flows involving real payment gateway and scheduler execution.

## Verification Details

### Artifact-Level Verification

**src/bot/handlers/subscription.py**
- Level 1 (Exists): ✓ EXISTS (158 lines)
- Level 2 (Substantive): ✓ SUBSTANTIVE
  - Length: 158 lines (exceeds 15 line minimum for handlers)
  - Exports: show_plans, router with 4 callbacks
  - No stub patterns (no TODO/FIXME/placeholder)
  - No empty returns
- Level 3 (Wired): ✓ WIRED
  - Imported by: menu.py:11 (show_plans function)
  - Router registered: bot.py:26 (subscription_router)
  - Uses: payment/client.py:create_payment, payment/service.py:get_user_subscription, cancel_subscription

**src/bot/keyboards/subscription.py**
- Level 1 (Exists): ✓ EXISTS (40 lines)
- Level 2 (Substantive): ✓ SUBSTANTIVE
  - Length: 40 lines (exceeds 10 line minimum)
  - Exports: get_plans_keyboard, get_cancel_confirmation_keyboard
  - No stub patterns
- Level 3 (Wired): ✓ WIRED
  - Imported by: subscription.py:10-12
  - Used by: subscription.py:54 (show_plans), line 127 (cancel confirmation)

**src/bot/handlers/tarot.py**
- Level 1 (Exists): ✓ EXISTS (349 lines)
- Level 2 (Substantive): ✓ SUBSTANTIVE
  - Length: 349 lines (well above minimum)
  - Contains: check_and_use_tarot_limit with atomic update
  - Uses daily_spread_limit on lines 64, 80, 85, 98, 245
  - No stub patterns
- Level 3 (Wired): ✓ WIRED
  - Registered: bot.py (tarot_router)
  - Uses: User.daily_spread_limit for limit checks

### Link-Level Verification

**Link 1: subscription.py → payment/client.py**
```python
# subscription.py:18
from src.services.payment import create_payment

# subscription.py:77
payment = await create_payment(
    user_id=callback.from_user.id,
    amount=price,
    description=f"AdtroBot {plan_names[plan]}",
    save_payment_method=True,
    metadata={"plan_type": plan.value},
)

# subscription.py:87
confirmation_url = payment.confirmation.confirmation_url
await callback.message.edit_text(f"Отлично! Перейдите по ссылке для оплаты:\n\n{confirmation_url}")
```
Status: ✓ FULLY WIRED (imports, calls, uses result)

**Link 2: tarot.py → user.daily_spread_limit**
```python
# tarot.py:81-89
stmt = (
    update(User)
    .where(
        User.id == user.id,
        User.tarot_spread_count < User.daily_spread_limit,  # ATOMIC CHECK
    )
    .values(tarot_spread_count=User.tarot_spread_count + 1)
    .returning(User.tarot_spread_count)
)
result = await session.execute(stmt)
new_count = result.scalar_one_or_none()  # None if limit exceeded

# tarot.py:98
remaining = user.daily_spread_limit - new_count
```
Status: ✓ FULLY WIRED (atomic WHERE condition, uses field for calculation)

### Router Registration Verification

```python
# bot.py:12
from src.bot.handlers import subscription_router

# bot.py:26
dp.include_routers(
    start_router,
    menu_router,
    subscription_router,  # REGISTERED
    horoscope_router,
    tarot_router,
    profile_settings_router,
    common_router,
)
```
Status: ✓ REGISTERED

### Scheduler Jobs Verification

```python
# scheduler.py:33-39
_scheduler.add_job(
    auto_renew_subscriptions,
    CronTrigger(hour=9, minute=0, timezone="Europe/Moscow"),
    id="auto_renew_subscriptions",
    replace_existing=True,
    misfire_grace_time=3600,
)

# scheduler.py:42-47
_scheduler.add_job(
    check_expiring_subscriptions,
    CronTrigger(hour=10, minute=0, timezone="Europe/Moscow"),
    id="check_expiring_subscriptions",
    replace_existing=True,
    misfire_grace_time=3600,
)
```
Status: ✓ BOTH JOBS REGISTERED

## Production Readiness

### Prerequisites Before Production

**Required manual configuration:**

1. Add `YOOKASSA_SHOP_ID` to Railway environment variables
   - Source: YooKassa Dashboard → Settings → Shop ID

2. Add `YOOKASSA_SECRET_KEY` to Railway environment variables
   - Source: YooKassa Dashboard → Settings → Secret Key

3. Configure YooKassa webhook URL
   - URL: `https://adtrobot-production.up.railway.app/webhook/yookassa`
   - Set in: YooKassa Dashboard → Webhooks

4. Run migration on Railway
   - Command: `alembic upgrade head`
   - Adds: Subscription, Payment, PromoCode tables + User premium fields

### Known Limitations

- YooKassa IP whitelist only checked in production (railway_environment set)
- Auto-renewal runs once daily (09:00 MSK) - subscriptions expiring mid-day won't renew until next morning
- Failed recurring payments marked as past_due, require manual user intervention

---

*Verified: 2026-01-23T02:10:00Z*
*Verifier: Claude (gsd-verifier)*
*Verification Mode: Initial (no previous verification)*
