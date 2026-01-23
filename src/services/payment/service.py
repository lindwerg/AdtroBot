"""Subscription business logic."""
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address, ip_network

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.payment import Payment
from src.db.models.subscription import Subscription, SubscriptionStatus
from src.db.models.user import User
from src.services.payment.schemas import PLAN_DURATION_DAYS, PaymentPlan

logger = structlog.get_logger()

# YooKassa IP whitelist
YOOKASSA_IPS = [
    ip_network("185.71.76.0/27"),
    ip_network("185.71.77.0/27"),
    ip_network("77.75.153.0/25"),
    ip_network("77.75.154.128/25"),
    ip_network("2a02:5180::/32"),
]


def is_yookassa_ip(ip_str: str) -> bool:
    """Check if IP is from YooKassa allowed ranges."""
    try:
        ip = ip_address(ip_str)
        for allowed in YOOKASSA_IPS:
            if ip in allowed:
                return True
        return False
    except ValueError:
        return False


async def get_user_subscription(
    session: AsyncSession, user_id: int
) -> Subscription | None:
    """Get active subscription for user (by telegram_id)."""
    # First get user by telegram_id
    stmt = select(User).where(User.telegram_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None

    # Then get active subscription
    stmt = select(Subscription).where(
        Subscription.user_id == user.id,
        Subscription.status.in_([
            SubscriptionStatus.TRIAL.value,
            SubscriptionStatus.ACTIVE.value,
            SubscriptionStatus.CANCELED.value,  # Still has access until end
        ]),
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def activate_subscription(
    session: AsyncSession,
    user_telegram_id: int,
    plan: PaymentPlan,
    payment_method_id: str | None = None,
    is_trial: bool = False,
) -> Subscription:
    """
    Create or activate subscription for user.

    Args:
        session: DB session
        user_telegram_id: Telegram user ID
        plan: Subscription plan
        payment_method_id: Saved payment method for recurring
        is_trial: Whether this is a trial activation

    Returns:
        Created/updated Subscription
    """
    # Get user
    stmt = select(User).where(User.telegram_id == user_telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError(f"User not found: {user_telegram_id}")

    now = datetime.now(timezone.utc)
    duration = timedelta(days=PLAN_DURATION_DAYS[plan])

    # Check for existing subscription
    existing = await get_user_subscription(session, user_telegram_id)

    if existing:
        # Extend existing subscription
        existing.current_period_end = existing.current_period_end + duration
        existing.status = SubscriptionStatus.ACTIVE.value
        if payment_method_id:
            existing.payment_method_id = payment_method_id
        subscription = existing
    else:
        # Create new subscription
        subscription = Subscription(
            user_id=user.id,
            plan=plan.value,
            status=SubscriptionStatus.TRIAL.value if is_trial else SubscriptionStatus.ACTIVE.value,
            payment_method_id=payment_method_id,
            started_at=now,
            current_period_start=now,
            current_period_end=now + duration,
            trial_end=now + timedelta(days=3) if is_trial else None,
        )
        session.add(subscription)

    # Update user premium status
    user.is_premium = True
    user.premium_until = subscription.current_period_end
    user.daily_spread_limit = 20  # Premium limit

    await session.commit()

    await logger.ainfo(
        "Subscription activated",
        user_id=user_telegram_id,
        plan=plan.value,
        until=subscription.current_period_end.isoformat(),
    )

    return subscription


async def cancel_subscription(
    session: AsyncSession,
    user_telegram_id: int,
) -> Subscription | None:
    """
    Cancel subscription (access remains until period end).

    Returns:
        Updated Subscription or None if not found
    """
    subscription = await get_user_subscription(session, user_telegram_id)

    if not subscription:
        return None

    subscription.status = SubscriptionStatus.CANCELED.value
    subscription.canceled_at = datetime.now(timezone.utc)
    # Note: user keeps access until premium_until

    await session.commit()

    await logger.ainfo(
        "Subscription canceled",
        user_id=user_telegram_id,
        access_until=subscription.current_period_end.isoformat(),
    )

    return subscription


async def process_webhook_event(
    session: AsyncSession,
    event: dict,
) -> bool:
    """
    Process YooKassa webhook event idempotently.

    Args:
        session: DB session
        event: Webhook event payload

    Returns:
        True if processed, False if duplicate
    """
    event_type = event.get("event")
    payment_data = event.get("object", {})
    payment_id = payment_data.get("id")

    if not payment_id:
        await logger.awarning("Webhook missing payment_id", event=event)
        return False

    # Check idempotency - already processed?
    existing = await session.get(Payment, payment_id)
    if existing and existing.webhook_processed:
        await logger.ainfo("Webhook duplicate, skipping", payment_id=payment_id)
        return False

    metadata = payment_data.get("metadata", {})
    user_id = metadata.get("user_id")
    plan_type = metadata.get("plan_type")

    await logger.ainfo(
        "Processing webhook",
        event_type=event_type,
        payment_id=payment_id,
        user_id=user_id,
    )

    if event_type == "payment.succeeded":
        status = payment_data.get("status")
        amount_value = payment_data.get("amount", {}).get("value", "0")
        amount_kopeks = int(float(amount_value) * 100)
        payment_method = payment_data.get("payment_method", {})
        payment_method_id = payment_method.get("id") if payment_method.get("saved") else None

        # Get user by telegram_id to get internal user_id for Payment FK
        internal_user_id = 0
        if user_id:
            stmt = select(User).where(User.telegram_id == int(user_id))
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                internal_user_id = user.id

        # Create or update payment record
        if existing:
            existing.status = status
            existing.webhook_processed = True
            existing.paid_at = datetime.now(timezone.utc)
        else:
            payment = Payment(
                id=payment_id,
                user_id=internal_user_id,
                amount=amount_kopeks,
                status=status,
                description=payment_data.get("description"),
                is_recurring=metadata.get("type") == "recurring",
                webhook_processed=True,
                paid_at=datetime.now(timezone.utc),
            )
            session.add(payment)

        # Activate subscription if this is a subscription payment
        if user_id and plan_type:
            plan = PaymentPlan(plan_type)
            await activate_subscription(
                session,
                int(user_id),
                plan,
                payment_method_id=payment_method_id,
            )
        elif user_id:
            # Commit payment record even without plan_type
            await session.commit()

        return True

    elif event_type == "payment.canceled":
        if existing:
            existing.status = "canceled"
            existing.webhook_processed = True
            await session.commit()
        return True

    return False
