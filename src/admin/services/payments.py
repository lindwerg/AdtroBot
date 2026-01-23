"""Payments and subscriptions service."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.schemas import (
    PaymentListItem,
    PaymentListResponse,
    SubscriptionListItem,
    SubscriptionListResponse,
    UpdateSubscriptionStatusRequest,
)
from src.db.models.payment import Payment
from src.db.models.subscription import Subscription
from src.db.models.user import User


async def list_payments(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    user_search: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> PaymentListResponse:
    """List payments with filters and pagination."""
    query = select(
        Payment,
        User.telegram_id.label("user_telegram_id"),
        User.username.label("user_username"),
    ).join(User, Payment.user_id == User.id)

    # Build filter conditions
    conditions = []

    if status:
        conditions.append(Payment.status == status)

    if user_search:
        if user_search.isdigit():
            conditions.append(User.telegram_id == int(user_search))
        else:
            conditions.append(User.username.ilike(f"%{user_search}%"))

    if date_from:
        conditions.append(Payment.created_at >= date_from)
    if date_to:
        conditions.append(Payment.created_at <= date_to)

    # Apply filters to main query
    for condition in conditions:
        query = query.where(condition)

    # Count total
    count_query = select(func.count()).select_from(Payment).join(User, Payment.user_id == User.id)
    for condition in conditions:
        count_query = count_query.where(condition)
    total = await session.scalar(count_query) or 0

    # Sum succeeded payments amount
    sum_query = select(func.coalesce(func.sum(Payment.amount), 0)).join(
        User, Payment.user_id == User.id
    )
    sum_conditions = [c for c in conditions]
    # Only sum succeeded payments unless filtering by specific status
    if not status:
        sum_conditions.append(Payment.status == "succeeded")
    elif status == "succeeded":
        pass  # Already filtering by succeeded
    else:
        # For other status filters, sum those filtered payments
        pass

    for condition in sum_conditions:
        sum_query = sum_query.where(condition)
    total_amount = await session.scalar(sum_query) or 0

    # Order and paginate
    query = query.order_by(Payment.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    rows = result.all()

    items = []
    for row in rows:
        payment = row[0]
        item = PaymentListItem(
            id=payment.id,
            user_id=payment.user_id,
            subscription_id=payment.subscription_id,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            is_recurring=payment.is_recurring,
            description=payment.description,
            created_at=payment.created_at,
            paid_at=payment.paid_at,
            user_telegram_id=row[1],
            user_username=row[2],
        )
        items.append(item)

    return PaymentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_amount=total_amount,
    )


async def list_subscriptions(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    plan: str | None = None,
    user_search: str | None = None,
) -> SubscriptionListResponse:
    """List subscriptions with filters and pagination."""
    query = select(
        Subscription,
        User.telegram_id.label("user_telegram_id"),
        User.username.label("user_username"),
    ).join(User, Subscription.user_id == User.id)

    # Build filter conditions
    conditions = []

    if status:
        conditions.append(Subscription.status == status)
    if plan:
        conditions.append(Subscription.plan == plan)
    if user_search:
        if user_search.isdigit():
            conditions.append(User.telegram_id == int(user_search))
        else:
            conditions.append(User.username.ilike(f"%{user_search}%"))

    # Apply filters
    for condition in conditions:
        query = query.where(condition)

    # Count total
    count_query = (
        select(func.count())
        .select_from(Subscription)
        .join(User, Subscription.user_id == User.id)
    )
    for condition in conditions:
        count_query = count_query.where(condition)
    total = await session.scalar(count_query) or 0

    # Order and paginate
    query = query.order_by(Subscription.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    rows = result.all()

    items = []
    for row in rows:
        sub = row[0]
        item = SubscriptionListItem(
            id=sub.id,
            user_id=sub.user_id,
            plan=sub.plan,
            status=sub.status,
            payment_method_id=sub.payment_method_id,
            started_at=sub.started_at,
            current_period_start=sub.current_period_start,
            current_period_end=sub.current_period_end,
            canceled_at=sub.canceled_at,
            created_at=sub.created_at,
            user_telegram_id=row[1],
            user_username=row[2],
        )
        items.append(item)

    return SubscriptionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def update_subscription_status(
    session: AsyncSession,
    subscription_id: int,
    request: UpdateSubscriptionStatusRequest,
) -> bool:
    """Update subscription status."""
    sub = await session.get(Subscription, subscription_id)
    if not sub:
        return False

    sub.status = request.status

    # Update user premium status accordingly
    user = await session.get(User, sub.user_id)
    if user:
        if request.status in ("canceled", "expired"):
            user.is_premium = False
            user.daily_spread_limit = 1
        elif request.status == "active":
            user.is_premium = True
            user.daily_spread_limit = 20

    await session.commit()
    return True
