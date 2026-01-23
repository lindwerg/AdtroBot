# Phase 6: Payments - Research

**Researched:** 2026-01-23
**Domain:** YooKassa payment integration, subscriptions, recurring billing
**Confidence:** MEDIUM

## Summary

Исследована интеграция с ЮКасса для подписочной модели. ЮКасса предоставляет официальный Python SDK (синхронный), но для async-проекта лучше использовать неофициальные async-обёртки или запускать официальный SDK в thread pool. Рекуррентные платежи (автоплатежи) реализуются через сохранение payment_method_id при первом платеже, затем списание без участия пользователя.

**Ключевые моменты:**
- Trial 3 дня реализуется через zero-amount binding (привязка карты без списания) + отложенный первый платёж
- Webhook от ЮКасса требует немедленный HTTP 200, обработка асинхронно
- Idempotency через Idempotence-Key header (24 часа), webhook - через хранение processed payment_id
- НДС с 01.01.2026 = 22% (важно для чеков)

**Primary recommendation:** Использовать официальный `yookassa` SDK v3.9.0 с обёрткой в asyncio.to_thread() для async-совместимости. Не изобретать свой клиент.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yookassa | 3.9.0 | Официальный SDK для YooKassa API | Официальная библиотека от YooMoney, актуальная (dec 2025), поддержка НДС 22% |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncio.to_thread | stdlib | Запуск sync SDK в async контексте | Все вызовы YooKassa SDK |
| uuid | stdlib | Генерация Idempotence-Key | Каждый POST/DELETE запрос к API |
| hmac/hashlib | stdlib | Верификация webhook signature | Опционально (можно использовать IP whitelist) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| yookassa (official) | aioyookassa | Нативно async, но неофициальный, менее стабилен |
| yookassa (official) | async_yookassa | httpx-based, Pydantic v2, но меньше документации |
| asyncio.to_thread | aiohttp custom client | Полный контроль, но много работы и поддержки |

**Recommendation:** Официальный SDK надёжнее. async-обёртки имеют риски: меньше пользователей, возможны баги при обновлениях API. `asyncio.to_thread()` добавляет ~1-2ms overhead, что приемлемо для платёжных операций.

**Installation:**
```bash
poetry add yookassa
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── services/
│   └── payment/
│       ├── __init__.py
│       ├── client.py         # YooKassa client wrapper (async)
│       ├── schemas.py        # Pydantic models for plans, subscriptions
│       └── service.py        # Business logic: subscribe, cancel, check_limits
├── db/
│   └── models/
│       ├── subscription.py   # Subscription model
│       ├── payment.py        # Payment history
│       └── promo.py          # Promo codes
├── api/
│   └── routes/
│       └── yookassa.py       # Webhook endpoint
└── bot/
    └── handlers/
        └── subscription.py   # Bot handlers for subscription flow
```

### Pattern 1: Async Wrapper for Sync SDK

**What:** Обёртка официального SDK через asyncio.to_thread()
**When to use:** Все вызовы YooKassa API в async-контексте
**Example:**
```python
# Source: Python asyncio documentation + YooKassa SDK
import asyncio
from yookassa import Payment, Configuration

Configuration.account_id = settings.yookassa_shop_id
Configuration.secret_key = settings.yookassa_secret_key

async def create_payment(amount: str, description: str, return_url: str,
                         save_method: bool = False, idempotency_key: str = None) -> dict:
    """Create payment with optional payment method saving."""
    def _create():
        return Payment.create({
            "amount": {"value": amount, "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "capture": True,
            "save_payment_method": save_method,
            "description": description,
        }, idempotency_key=idempotency_key)

    return await asyncio.to_thread(_create)
```

### Pattern 2: Webhook Immediate Response + Background Processing

**What:** Немедленный HTTP 200, обработка в фоне
**When to use:** Все webhook endpoints от ЮКасса
**Rationale:** ЮКасса ждёт ответ, ретраит 24 часа при не-200. Тяжёлая логика (update DB, send notification) не должна блокировать response.
**Example:**
```python
# Source: YooKassa Notifications documentation
from fastapi import BackgroundTasks

@app.post("/webhook/yookassa")
async def yookassa_webhook(request: Request, background_tasks: BackgroundTasks):
    # 1. Verify signature or IP (fast)
    # 2. Parse payload (fast)
    # 3. Schedule background processing
    background_tasks.add_task(process_payment_event, payload)
    # 4. Return 200 immediately
    return Response(status_code=200)
```

### Pattern 3: Subscription State Machine

**What:** Явные состояния подписки с валидными переходами
**When to use:** Любые изменения статуса подписки
**States:**
- `trial` - пробный период (карта привязана, но не списано)
- `active` - активная подписка (оплачено)
- `past_due` - просрочен платёж (retry в процессе)
- `canceled` - отменена пользователем (доступ до end_date)
- `expired` - истекла (нет доступа)

**Valid transitions:**
```
trial -> active (первый платёж успешен)
trial -> expired (платёж не прошёл после trial)
active -> active (renewal успешен)
active -> past_due (renewal failed)
active -> canceled (user canceled)
past_due -> active (retry успешен)
past_due -> expired (все retry исчерпаны)
canceled -> expired (end_date прошла)
```

### Pattern 4: Idempotent Webhook Processing

**What:** Хранение processed event IDs для дедупликации
**When to use:** Обработка всех webhook событий
**Example:**
```python
# Source: Payment webhook best practices
async def process_payment_event(event: dict, session: AsyncSession):
    payment_id = event["object"]["id"]

    # Check if already processed (idempotency)
    existing = await session.get(Payment, payment_id)
    if existing and existing.webhook_processed:
        return  # Already processed, skip

    # Process event...

    # Mark as processed
    existing.webhook_processed = True
    await session.commit()
```

### Anti-Patterns to Avoid

- **Sync SDK в async без обёртки:** Блокирует event loop, убивает производительность бота
- **Обработка webhook синхронно до response:** ЮКасса timeout, повторные доставки, дубликаты
- **Хранение payment_method_id без шифрования:** Хотя это не CVV, это sensitive data
- **Проверка лимитов после действия:** Race conditions, превышение лимитов
- **Hardcoded цены в коде:** Сложно менять без деплоя

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Payment processing | Custom HTTP client | yookassa SDK | Signature, errors, retries - всё уже сделано |
| Webhook signature | Manual HMAC | IP whitelist или SDK методы | Проще, надёжнее |
| Recurring scheduling | Custom cron | APScheduler (уже есть) | Job persistence, retries |
| UUID generation | Random strings | uuid4() | RFC compliant, collision-free |
| Date calculations | Manual datetime | dateutil.relativedelta | Edge cases (31 -> 28 feb) |

**Key insight:** Платёжная интеграция критична. Ошибки = потеря денег или юридические проблемы. Максимально использовать проверенные решения.

## Common Pitfalls

### Pitfall 1: Trial без привязки карты

**What goes wrong:** Пользователь получает trial, но карта не привязана. После trial нечего списывать.
**Why it happens:** Неправильное понимание flow - trial это не "бесплатный доступ", а "привязка + отложенный платёж"
**How to avoid:**
- Trial начинается ТОЛЬКО после успешного zero-amount binding
- Сохранить payment_method_id сразу
**Warning signs:** Много trial users без payment_method_id

### Pitfall 2: Race condition при проверке лимитов

**What goes wrong:** Два параллельных запроса проходят проверку лимитов, оба делают действие
**Why it happens:** Проверка и инкремент не атомарны
**How to avoid:**
```sql
UPDATE users SET tarot_spread_count = tarot_spread_count + 1
WHERE id = :id AND tarot_spread_count < :limit
RETURNING tarot_spread_count
```
Если rows affected = 0, лимит превышен.
**Warning signs:** tarot_spread_count > limit в БД

### Pitfall 3: Webhook replay attacks

**What goes wrong:** Злоумышленник отправляет старые валидные webhook'и
**Why it happens:** Только проверка signature, без проверки timestamp/idempotency
**How to avoid:**
- Хранить processed payment_id
- Проверять created_at события (не старше N минут)
- IP whitelist как дополнительный слой
**Warning signs:** Дублирование записей в payment history

### Pitfall 4: НДС 22% не учтён

**What goes wrong:** Чеки формируются с НДС 20%, ФНС штрафует
**Why it happens:** Устаревший SDK или hardcoded значения
**How to avoid:**
- Обновить yookassa SDK до 3.9.0+
- Проверить что Receipt создаётся с vat_code для 22%
**Warning signs:** Чеки с 20% после 01.01.2026

### Pitfall 5: Отмена подписки = немедленное отключение

**What goes wrong:** Пользователь отменил, сразу потерял доступ, требует refund
**Why it happens:** cancel_at = now() вместо cancel_at = current_period_end
**How to avoid:**
- При отмене: status = 'canceled', end_date остаётся прежним
- Доступ проверять по end_date, не по status
**Warning signs:** Жалобы пользователей на "украденные дни"

### Pitfall 6: Autopayment без уведомления

**What goes wrong:** Деньги списались неожиданно, пользователь в шоке, chargeback
**Why it happens:** Нет reminder за 3 дня
**How to avoid:**
- APScheduler job за 3 дня до renewal
- Уведомление с суммой и датой
**Warning signs:** Chargebacks, жалобы на "без предупреждения"

## Code Examples

### YooKassa Configuration

```python
# Source: YooKassa SDK documentation
# src/config.py
class Settings(BaseSettings):
    # ... existing fields ...

    # YooKassa
    yookassa_shop_id: str = Field(
        default="",
        validation_alias="YOOKASSA_SHOP_ID",
    )
    yookassa_secret_key: str = Field(
        default="",
        validation_alias="YOOKASSA_SECRET_KEY",
    )
    yookassa_return_url: str = Field(
        default="https://t.me/YourBotName",
        validation_alias="YOOKASSA_RETURN_URL",
    )
```

### Creating First Payment with Method Saving

```python
# Source: YooKassa recurring payments documentation
from yookassa import Payment
import uuid

async def create_subscription_payment(
    user_id: int,
    plan_type: str,  # "monthly" | "yearly"
    is_trial: bool = False,
) -> dict:
    """Create payment for subscription with card saving."""

    prices = {
        "monthly": "299.00",
        "yearly": "2499.00",
    }

    idempotency_key = str(uuid.uuid4())

    def _create():
        return Payment.create({
            "amount": {
                "value": prices[plan_type],
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": settings.yookassa_return_url
            },
            "capture": True,
            "save_payment_method": True,  # CRITICAL for recurring
            "description": f"Подписка AdtroBot ({plan_type})",
            "metadata": {
                "user_id": user_id,
                "plan_type": plan_type,
                "is_trial": is_trial,
            }
        }, idempotency_key)

    return await asyncio.to_thread(_create)
```

### Zero-Amount Binding for Trial

```python
# Source: YooKassa zero-amount binding documentation
from yookassa import PaymentMethod

async def create_trial_binding(user_id: int) -> dict:
    """Bind card without charging for trial period."""

    idempotency_key = str(uuid.uuid4())

    def _create():
        # PaymentMethod endpoint for zero-amount binding
        return PaymentMethod.create({
            "confirmation": {
                "type": "redirect",
                "return_url": settings.yookassa_return_url
            },
            "type": "bank_card",
            "metadata": {
                "user_id": user_id,
                "action": "trial_binding",
            }
        }, idempotency_key)

    return await asyncio.to_thread(_create)
```

### Recurring Payment with Saved Method

```python
# Source: YooKassa autopayments documentation
async def charge_recurring_payment(
    payment_method_id: str,
    amount: str,
    user_id: int,
    subscription_id: int,
) -> dict:
    """Charge recurring payment using saved method."""

    idempotency_key = str(uuid.uuid4())

    def _create():
        return Payment.create({
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "capture": True,
            "payment_method_id": payment_method_id,  # Use saved method
            "description": f"Продление подписки AdtroBot",
            "metadata": {
                "user_id": user_id,
                "subscription_id": subscription_id,
                "type": "recurring",
            }
        }, idempotency_key)

    return await asyncio.to_thread(_create)
```

### Webhook IP Verification

```python
# Source: YooKassa notifications documentation
from ipaddress import ip_address, ip_network

YOOKASSA_IPS = [
    ip_network("185.71.76.0/27"),
    ip_network("185.71.77.0/27"),
    ip_network("77.75.153.0/25"),
    ip_network("77.75.154.128/25"),
    ip_address("77.75.156.11"),
    ip_address("77.75.156.35"),
    ip_network("2a02:5180::/32"),
]

def is_yookassa_ip(ip_str: str) -> bool:
    """Check if IP is from YooKassa allowed ranges."""
    try:
        ip = ip_address(ip_str)
        for allowed in YOOKASSA_IPS:
            if isinstance(allowed, ip_network):
                if ip in allowed:
                    return True
            elif ip == allowed:
                return True
        return False
    except ValueError:
        return False
```

### Atomic Limit Check

```python
# Source: PostgreSQL atomic operations best practice
from sqlalchemy import text

async def use_tarot_spread(session: AsyncSession, user_id: int, limit: int) -> bool:
    """
    Atomically check and increment spread count.
    Returns True if spread was allowed, False if limit exceeded.
    """
    result = await session.execute(
        text("""
            UPDATE users
            SET tarot_spread_count = tarot_spread_count + 1
            WHERE id = :user_id
              AND tarot_spread_count < :limit
              AND (spread_reset_date IS NULL OR spread_reset_date < CURRENT_DATE)
            RETURNING id
        """),
        {"user_id": user_id, "limit": limit}
    )

    if result.fetchone() is None:
        # Limit exceeded or already reset needed
        return False

    await session.commit()
    return True
```

## DB Schema Design

### Subscription Model

```python
# Based on: SaaS subscription data model best practices
class SubscriptionStatus(str, enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"

class SubscriptionPlan(str, enum.Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Plan info
    plan: Mapped[str] = mapped_column(String(20))  # monthly, yearly
    status: Mapped[str] = mapped_column(String(20), default="trial")

    # Payment method (for recurring)
    payment_method_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Dates
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    trial_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Promo
    promo_code_id: Mapped[int | None] = mapped_column(ForeignKey("promo_codes.id"), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### Payment Model

```python
class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    WAITING_FOR_CAPTURE = "waiting_for_capture"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # YooKassa payment ID
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id"), nullable=True)

    # Amount
    amount: Mapped[int] = mapped_column(Integer)  # In kopeks (29900 = 299.00 RUB)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")

    # Status
    status: Mapped[str] = mapped_column(String(30))

    # Type
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Webhook processing
    webhook_processed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

### PromoCode Model (Partner-Ready)

```python
class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    # Discount
    discount_percent: Mapped[int] = mapped_column(SmallInteger)  # 10 = 10%

    # Validity
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None = unlimited
    current_uses: Mapped[int] = mapped_column(Integer, default=0)

    # Partner program (future)
    partner_id: Mapped[int | None] = mapped_column(ForeignKey("partners.id"), nullable=True)
    partner_commission_percent: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

### User Model Updates

```python
# Add to existing User model
class User(Base):
    # ... existing fields ...

    # Subscription status (denormalized for quick access)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    premium_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Limits (premium vs free)
    daily_spread_limit: Mapped[int] = mapped_column(SmallInteger, default=1, server_default="1")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Telegram Payments API | External payment (YooKassa redirect) | Context decision | Полный контроль над подписками, но редирект из бота |
| НДС 20% | НДС 22% | 01.01.2026 | Обязательно SDK 3.9.0+ для корректных чеков |
| Sync SDK | Async wrappers available | 2024-2025 | Можно выбрать, но official sync надёжнее |

**Deprecated/outdated:**
- yookassa SDK 2.x: Не поддерживает новые ставки НДС, Python 2.7 ориентация
- Telegram Bot Payments для рекуррентов: Не подходит для автопродления, только разовые платежи

## Open Questions

### 1. Webhook signature vs IP whitelist

**What we know:** ЮКасса поддерживает оба метода верификации
**What's unclear:** Webhook-Signature header - точный формат HMAC, как получить webhook_key
**Recommendation:** Начать с IP whitelist (проще), добавить signature позже если нужно

### 2. Trial период - точная механика

**What we know:** Zero-amount binding + scheduler для первого платежа
**What's unclear:** Как обрабатывать если binding failed - retry? сразу отказ?
**Recommendation:** При fail binding - показать ошибку, предложить retry без trial

### 3. Retry logic для failed recurring

**What we know:** ЮКасса не делает автоматические retry за нас
**What's unclear:** Оптимальная стратегия retry (через сколько, сколько раз)
**Recommendation:** 3 retry: day 1, day 3, day 7. После этого - expired.

## Sources

### Primary (HIGH confidence)
- [YooKassa Python SDK GitHub](https://github.com/yoomoney/yookassa-sdk-python) - официальный SDK, примеры кода
- [YooKassa API Documentation](https://yookassa.ru/developers) - полная документация API
- [YooKassa Webhooks](https://yookassa.ru/developers/using-api/webhooks) - формат уведомлений, верификация
- [YooKassa Recurring Payments](https://yookassa.ru/developers/payment-acceptance/scenario-extensions/recurring-payments/basics) - автоплатежи

### Secondary (MEDIUM confidence)
- [YooKassa Interaction Format](https://yookassa.ru/developers/using-api/interaction-format) - Idempotence-Key, authentication
- [SaaS Subscription Schema](https://github.com/vercel/nextjs-subscription-payments/blob/main/schema.sql) - reference DB schema
- [PyPI yookassa](https://pypi.org/project/yookassa/) - версия 3.9.0, release notes

### Tertiary (LOW confidence)
- [aioyookassa PyPI](https://pypi.org/project/aioyookassa/) - async альтернатива (неофициальная)
- [async_yookassa GitHub](https://github.com/proDreams/async_yookassa) - httpx-based async SDK

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - официальный SDK, документация актуальна
- Architecture: MEDIUM - паттерны общеприняты, но специфика ЮКасса требует проверки
- DB Schema: MEDIUM - основано на best practices, но не тестировано с ЮКасса
- Pitfalls: HIGH - документированы в официальных источниках

**Research date:** 2026-01-23
**Valid until:** 2026-02-23 (30 дней - API стабилен)
