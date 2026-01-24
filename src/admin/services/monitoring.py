"""Monitoring data aggregation for admin dashboard."""

from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.ai_usage import AIUsage
from src.db.models.payment import Payment
from src.db.models.tarot_spread import TarotSpread


TimeRange = Literal["24h", "7d", "30d"]


def get_time_range_start(range_type: TimeRange) -> datetime:
    """Get start datetime for time range."""
    now = datetime.now(timezone.utc)
    if range_type == "24h":
        return now - timedelta(hours=24)
    elif range_type == "7d":
        return now - timedelta(days=7)
    else:  # 30d
        return now - timedelta(days=30)


async def get_active_users(
    session: AsyncSession,
    range_type: TimeRange,
) -> dict[str, int]:
    """Get DAU/WAU/MAU based on tarot spreads activity.

    Returns dict with dau, wau, mau counts.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # DAU - users with activity today
    dau = await session.scalar(
        select(func.count(distinct(TarotSpread.user_id)))
        .where(TarotSpread.created_at >= today_start)
    ) or 0

    # WAU - users with activity in last 7 days
    wau = await session.scalar(
        select(func.count(distinct(TarotSpread.user_id)))
        .where(TarotSpread.created_at >= week_ago)
    ) or 0

    # MAU - users with activity in last 30 days
    mau = await session.scalar(
        select(func.count(distinct(TarotSpread.user_id)))
        .where(TarotSpread.created_at >= month_ago)
    ) or 0

    return {"dau": dau, "wau": wau, "mau": mau}


async def get_api_costs_data(
    session: AsyncSession,
    range_type: TimeRange,
) -> dict:
    """Get API costs breakdown by operation.

    Returns dict with:
    - total_cost: float
    - total_tokens: int
    - by_operation: list of {operation, cost, tokens, requests}
    - by_day: list of {date, cost, tokens}
    """
    range_start = get_time_range_start(range_type)

    # Total cost and tokens
    totals = await session.execute(
        select(
            func.coalesce(func.sum(AIUsage.cost_dollars), 0).label("total_cost"),
            func.coalesce(func.sum(AIUsage.total_tokens), 0).label("total_tokens"),
            func.count(AIUsage.id).label("total_requests"),
        )
        .where(AIUsage.created_at >= range_start)
    )
    total_row = totals.first()

    # Breakdown by operation
    by_operation_query = (
        select(
            AIUsage.operation,
            func.coalesce(func.sum(AIUsage.cost_dollars), 0).label("cost"),
            func.coalesce(func.sum(AIUsage.total_tokens), 0).label("tokens"),
            func.count(AIUsage.id).label("requests"),
        )
        .where(AIUsage.created_at >= range_start)
        .group_by(AIUsage.operation)
        .order_by(func.sum(AIUsage.cost_dollars).desc())
    )
    by_operation_result = await session.execute(by_operation_query)
    by_operation = [
        {
            "operation": row.operation or "unknown",
            "cost": float(row.cost),
            "tokens": int(row.tokens),
            "requests": int(row.requests),
        }
        for row in by_operation_result.all()
    ]

    # Breakdown by day (for chart)
    by_day_query = (
        select(
            func.date_trunc("day", AIUsage.created_at).label("day"),
            func.coalesce(func.sum(AIUsage.cost_dollars), 0).label("cost"),
            func.coalesce(func.sum(AIUsage.total_tokens), 0).label("tokens"),
        )
        .where(AIUsage.created_at >= range_start)
        .group_by(func.date_trunc("day", AIUsage.created_at))
        .order_by(func.date_trunc("day", AIUsage.created_at))
    )
    by_day_result = await session.execute(by_day_query)
    by_day = [
        {
            "date": row.day.strftime("%Y-%m-%d"),
            "cost": float(row.cost),
            "tokens": int(row.tokens),
        }
        for row in by_day_result.all()
    ]

    return {
        "total_cost": float(total_row.total_cost) if total_row else 0,
        "total_tokens": int(total_row.total_tokens) if total_row else 0,
        "total_requests": int(total_row.total_requests) if total_row else 0,
        "by_operation": by_operation,
        "by_day": by_day,
    }


async def get_unit_economics(
    session: AsyncSession,
    range_type: TimeRange,
) -> dict:
    """Get unit economics: cost per user metrics.

    Returns dict with:
    - cost_per_dau: float
    - cost_per_paying_user: float
    - total_users: int
    - paying_users: int
    """
    range_start = get_time_range_start(range_type)

    # Get total cost in period
    total_cost = await session.scalar(
        select(func.coalesce(func.sum(AIUsage.cost_dollars), 0))
        .where(AIUsage.created_at >= range_start)
    ) or 0

    # Get active users in period
    active_users = await session.scalar(
        select(func.count(distinct(TarotSpread.user_id)))
        .where(TarotSpread.created_at >= range_start)
    ) or 0

    # Get paying users (ever paid)
    paying_users = await session.scalar(
        select(func.count(distinct(Payment.user_id)))
        .where(Payment.status == "succeeded")
    ) or 0

    # Active paying users in period
    active_paying = await session.scalar(
        select(func.count(distinct(TarotSpread.user_id)))
        .where(TarotSpread.created_at >= range_start)
        .where(
            TarotSpread.user_id.in_(
                select(distinct(Payment.user_id))
                .where(Payment.status == "succeeded")
            )
        )
    ) or 0

    return {
        "total_cost": float(total_cost),
        "active_users": active_users,
        "paying_users": paying_users,
        "active_paying_users": active_paying,
        "cost_per_active_user": float(total_cost) / max(active_users, 1),
        "cost_per_paying_user": float(total_cost) / max(active_paying, 1),
    }


async def get_error_stats(
    session: AsyncSession,
    range_type: TimeRange,
) -> dict:
    """Get error statistics (placeholder - from Prometheus or logs).

    For now returns zeros - real implementation would query Prometheus or logs.
    """
    # TODO: Query Prometheus for actual error rates
    return {
        "error_count": 0,
        "error_rate": 0.0,
        "avg_response_time_ms": 0,
    }


async def get_monitoring_data(
    session: AsyncSession,
    range_type: TimeRange = "7d",
) -> dict:
    """Get all monitoring data for dashboard.

    Combines active users, API costs, unit economics, error stats.
    """
    active_users = await get_active_users(session, range_type)
    api_costs = await get_api_costs_data(session, range_type)
    unit_economics = await get_unit_economics(session, range_type)
    error_stats = await get_error_stats(session, range_type)

    return {
        "range": range_type,
        "active_users": active_users,
        "api_costs": api_costs,
        "unit_economics": unit_economics,
        "error_stats": error_stats,
    }
