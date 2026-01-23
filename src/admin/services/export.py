"""Data export service."""

import io
from datetime import datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.payment import Payment
from src.db.models.user import User


async def export_users_csv(
    session: AsyncSession,
    zodiac_sign: str | None = None,
    is_premium: bool | None = None,
    has_detailed_natal: bool | None = None,
) -> io.StringIO:
    """Export users to CSV."""
    query = select(User)

    if zodiac_sign:
        query = query.where(User.zodiac_sign == zodiac_sign)
    if is_premium is not None:
        query = query.where(User.is_premium == is_premium)
    if has_detailed_natal is not None:
        if has_detailed_natal:
            query = query.where(User.detailed_natal_purchased_at.isnot(None))
        else:
            query = query.where(User.detailed_natal_purchased_at.is_(None))

    result = await session.execute(query)
    users = result.scalars().all()

    data = [
        {
            "id": u.id,
            "telegram_id": u.telegram_id,
            "username": u.username,
            "zodiac_sign": u.zodiac_sign,
            "birth_date": u.birth_date.isoformat() if u.birth_date else None,
            "birth_city": u.birth_city,
            "is_premium": u.is_premium,
            "premium_until": u.premium_until.isoformat() if u.premium_until else None,
            "daily_spread_limit": u.daily_spread_limit,
            "tarot_spread_count": u.tarot_spread_count,
            "notifications_enabled": u.notifications_enabled,
            "detailed_natal_purchased_at": (
                u.detailed_natal_purchased_at.isoformat()
                if u.detailed_natal_purchased_at
                else None
            ),
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]

    df = pd.DataFrame(data)

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    return stream


async def export_payments_csv(
    session: AsyncSession,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> io.StringIO:
    """Export payments to CSV."""
    query = select(Payment, User.telegram_id, User.username).join(
        User, Payment.user_id == User.id
    )

    if status:
        query = query.where(Payment.status == status)
    if date_from:
        query = query.where(Payment.created_at >= date_from)
    if date_to:
        query = query.where(Payment.created_at <= date_to)

    result = await session.execute(query)
    rows = result.all()

    data = [
        {
            "payment_id": row[0].id,
            "user_id": row[0].user_id,
            "telegram_id": row[1],
            "username": row[2],
            "amount_rub": row[0].amount / 100,
            "currency": row[0].currency,
            "status": row[0].status,
            "is_recurring": row[0].is_recurring,
            "description": row[0].description,
            "created_at": row[0].created_at.isoformat(),
            "paid_at": row[0].paid_at.isoformat() if row[0].paid_at else None,
        }
        for row in rows
    ]

    df = pd.DataFrame(data)

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    return stream


async def export_metrics_csv(
    session: AsyncSession,
    days: int = 30,
) -> io.StringIO:
    """Export daily metrics to CSV."""
    now = datetime.now(timezone.utc)
    data = []

    for i in range(days - 1, -1, -1):
        day_start = (now - timedelta(days=i)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        day_end = day_start + timedelta(days=1)

        # New users
        new_users = (
            await session.scalar(
                select(func.count(User.id))
                .where(User.created_at >= day_start)
                .where(User.created_at < day_end)
            )
            or 0
        )

        # Revenue
        revenue = (
            await session.scalar(
                select(func.coalesce(func.sum(Payment.amount), 0))
                .where(Payment.paid_at >= day_start)
                .where(Payment.paid_at < day_end)
                .where(Payment.status == "succeeded")
            )
            or 0
        )

        data.append(
            {
                "date": day_start.strftime("%Y-%m-%d"),
                "new_users": new_users,
                "revenue_rub": revenue / 100,
            }
        )

    df = pd.DataFrame(data)

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    return stream
