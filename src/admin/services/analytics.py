"""Dashboard analytics calculations."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.schemas import (
    DashboardMetrics,
    FunnelData,
    FunnelStage,
    KPIMetric,
    SparklinePoint,
)
from src.db.models.payment import Payment
from src.db.models.tarot_spread import TarotSpread
from src.db.models.user import User


def calc_trend(current: float, previous: float) -> float:
    """Calculate percentage change."""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round((current - previous) / previous * 100, 1)


async def get_sparkline_data(
    session: AsyncSession,
    metric_type: str,
    days: int = 7,
) -> list[SparklinePoint]:
    """Get daily values for sparkline chart."""
    now = datetime.now(timezone.utc)
    points = []

    for i in range(days - 1, -1, -1):
        day_start = (now - timedelta(days=i)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        day_end = day_start + timedelta(days=1)

        if metric_type == "new_users":
            value = await session.scalar(
                select(func.count(User.id))
                .where(User.created_at >= day_start)
                .where(User.created_at < day_end)
            )
        elif metric_type == "revenue":
            value = (
                await session.scalar(
                    select(func.coalesce(func.sum(Payment.amount), 0))
                    .where(Payment.paid_at >= day_start)
                    .where(Payment.paid_at < day_end)
                    .where(Payment.status == "succeeded")
                )
                or 0
            )
            value = value / 100  # Convert kopeks to rubles
        elif metric_type == "tarot_spreads":
            value = await session.scalar(
                select(func.count(TarotSpread.id))
                .where(TarotSpread.created_at >= day_start)
                .where(TarotSpread.created_at < day_end)
            )
        else:
            value = 0

        points.append(
            SparklinePoint(date=day_start.strftime("%Y-%m-%d"), value=float(value or 0))
        )

    return points


async def get_dashboard_metrics(session: AsyncSession) -> DashboardMetrics:
    """Calculate all dashboard KPI metrics."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # === Total Users ===
    total_users = await session.scalar(select(func.count(User.id))) or 0

    # === DAU (users with activity today - approximation: users who used tarot) ===
    dau = (
        await session.scalar(
            select(func.count(distinct(TarotSpread.user_id))).where(
                TarotSpread.created_at >= today_start
            )
        )
        or 0
    )
    dau_yesterday = (
        await session.scalar(
            select(func.count(distinct(TarotSpread.user_id)))
            .where(TarotSpread.created_at >= yesterday_start)
            .where(TarotSpread.created_at < today_start)
        )
        or 0
    )

    # === MAU (users active in last 30 days) ===
    mau = (
        await session.scalar(
            select(func.count(distinct(TarotSpread.user_id))).where(
                TarotSpread.created_at >= month_ago
            )
        )
        or 0
    )

    # === New Users Today ===
    new_today = (
        await session.scalar(
            select(func.count(User.id)).where(User.created_at >= today_start)
        )
        or 0
    )
    new_yesterday = (
        await session.scalar(
            select(func.count(User.id))
            .where(User.created_at >= yesterday_start)
            .where(User.created_at < today_start)
        )
        or 0
    )

    # === Retention D7 ===
    cohort_date = today_start - timedelta(days=7)
    cohort_end = cohort_date + timedelta(days=1)
    cohort_users = (
        await session.scalar(
            select(func.count(User.id))
            .where(User.created_at >= cohort_date)
            .where(User.created_at < cohort_end)
        )
        or 0
    )
    retained_users = (
        await session.scalar(
            select(func.count(distinct(TarotSpread.user_id)))
            .where(TarotSpread.created_at >= cohort_end)
            .where(
                TarotSpread.user_id.in_(
                    select(User.id)
                    .where(User.created_at >= cohort_date)
                    .where(User.created_at < cohort_end)
                )
            )
        )
        or 0
    )
    retention_d7 = (retained_users / cohort_users * 100) if cohort_users > 0 else 0

    # === Horoscopes Today (placeholder - need to track horoscope views) ===
    horoscopes_today = 0  # TODO: Add tracking table

    # === Tarot Spreads Today ===
    spreads_today = (
        await session.scalar(
            select(func.count(TarotSpread.id)).where(
                TarotSpread.created_at >= today_start
            )
        )
        or 0
    )
    spreads_yesterday = (
        await session.scalar(
            select(func.count(TarotSpread.id))
            .where(TarotSpread.created_at >= yesterday_start)
            .where(TarotSpread.created_at < today_start)
        )
        or 0
    )

    # === Most Active Zodiac ===
    zodiac_query = (
        select(User.zodiac_sign, func.count(TarotSpread.id).label("cnt"))
        .join(TarotSpread, User.id == TarotSpread.user_id)
        .where(TarotSpread.created_at >= today_start)
        .where(User.zodiac_sign.isnot(None))
        .group_by(User.zodiac_sign)
        .order_by(func.count(TarotSpread.id).desc())
        .limit(1)
    )
    zodiac_result = await session.execute(zodiac_query)
    most_active_zodiac = zodiac_result.scalar() or "N/A"

    # === Revenue Today ===
    revenue_today = (
        await session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.paid_at >= today_start)
            .where(Payment.status == "succeeded")
        )
        or 0
    )
    revenue_yesterday = (
        await session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.paid_at >= yesterday_start)
            .where(Payment.paid_at < today_start)
            .where(Payment.status == "succeeded")
        )
        or 0
    )

    # === Revenue This Month ===
    revenue_month = (
        await session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.paid_at >= month_start)
            .where(Payment.status == "succeeded")
        )
        or 0
    )

    # === Conversion Rate (paid users / total users who registered 7+ days ago) ===
    eligible_users = (
        await session.scalar(
            select(func.count(User.id)).where(User.created_at <= week_ago)
        )
        or 0
    )
    paid_users = (
        await session.scalar(
            select(func.count(distinct(Payment.user_id))).where(
                Payment.status == "succeeded"
            )
        )
        or 0
    )
    conversion_rate = (paid_users / eligible_users * 100) if eligible_users > 0 else 0

    # === ARPU (Average Revenue Per User) ===
    arpu = revenue_month / 100 / max(total_users, 1)  # rubles

    # === Get sparklines ===
    sparkline_new_users = await get_sparkline_data(session, "new_users", 7)
    sparkline_revenue = await get_sparkline_data(session, "revenue", 7)
    sparkline_spreads = await get_sparkline_data(session, "tarot_spreads", 7)

    return DashboardMetrics(
        active_users_dau=KPIMetric(
            value=dau,
            trend=calc_trend(dau, dau_yesterday),
            sparkline=sparkline_new_users,  # Reuse for now
        ),
        active_users_mau=KPIMetric(
            value=mau,
            trend=0,  # No comparison for MAU
            sparkline=[],
        ),
        new_users_today=KPIMetric(
            value=new_today,
            trend=calc_trend(new_today, new_yesterday),
            sparkline=sparkline_new_users,
        ),
        retention_d7=KPIMetric(
            value=f"{retention_d7:.1f}%",
            trend=0,
            sparkline=[],
        ),
        horoscopes_today=KPIMetric(
            value=horoscopes_today,
            trend=0,
            sparkline=[],
        ),
        tarot_spreads_today=KPIMetric(
            value=spreads_today,
            trend=calc_trend(spreads_today, spreads_yesterday),
            sparkline=sparkline_spreads,
        ),
        most_active_zodiac=most_active_zodiac,
        revenue_today=KPIMetric(
            value=f"{revenue_today / 100:.0f}",  # rubles
            trend=calc_trend(revenue_today, revenue_yesterday),
            sparkline=sparkline_revenue,
        ),
        revenue_month=KPIMetric(
            value=f"{revenue_month / 100:.0f}",
            trend=0,
            sparkline=[],
        ),
        conversion_rate=KPIMetric(
            value=f"{conversion_rate:.2f}%",
            trend=0,
            sparkline=[],
        ),
        arpu=KPIMetric(
            value=f"{arpu:.2f}",
            trend=0,
            sparkline=[],
        ),
        error_rate=None,
        avg_response_time=None,
        api_costs_today=None,
        api_costs_month=None,
    )


async def get_funnel_data(session: AsyncSession, days: int = 30) -> FunnelData:
    """Get conversion funnel data."""
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=days)

    stages = []

    # Stage 1: Registration (/start)
    registered = (
        await session.scalar(
            select(func.count(User.id)).where(User.created_at >= period_start)
        )
        or 0
    )
    stages.append(
        FunnelStage(
            name="registered",
            name_ru="Регистрация",
            value=registered,
            conversion_from_prev=None,
            dropoff_count=None,
            dropoff_percent=None,
        )
    )

    # Stage 2: Onboarding complete (has zodiac_sign)
    onboarded = (
        await session.scalar(
            select(func.count(User.id))
            .where(User.created_at >= period_start)
            .where(User.zodiac_sign.isnot(None))
        )
        or 0
    )
    stages.append(
        FunnelStage(
            name="onboarded",
            name_ru="Onboarding завершен",
            value=onboarded,
            conversion_from_prev=(
                round(onboarded / registered * 100, 1) if registered > 0 else 0
            ),
            dropoff_count=registered - onboarded,
            dropoff_percent=(
                round((registered - onboarded) / registered * 100, 1)
                if registered > 0
                else 0
            ),
        )
    )

    # Stage 3: First action (made at least 1 tarot spread)
    first_action = (
        await session.scalar(
            select(func.count(distinct(TarotSpread.user_id))).where(
                TarotSpread.user_id.in_(
                    select(User.id).where(User.created_at >= period_start)
                )
            )
        )
        or 0
    )
    stages.append(
        FunnelStage(
            name="first_action",
            name_ru="Первое действие",
            value=first_action,
            conversion_from_prev=(
                round(first_action / onboarded * 100, 1) if onboarded > 0 else 0
            ),
            dropoff_count=onboarded - first_action,
            dropoff_percent=(
                round((onboarded - first_action) / onboarded * 100, 1)
                if onboarded > 0
                else 0
            ),
        )
    )

    # Stage 4: Saw premium teaser (approximation: hit spread limit)
    saw_teaser = (
        await session.scalar(
            select(func.count(User.id)).where(
                User.id.in_(
                    select(TarotSpread.user_id)
                    .where(
                        TarotSpread.user_id.in_(
                            select(User.id).where(User.created_at >= period_start)
                        )
                    )
                    .group_by(TarotSpread.user_id)
                    .having(func.count(TarotSpread.id) >= 2)
                )
            )
        )
        or 0
    )
    stages.append(
        FunnelStage(
            name="saw_teaser",
            name_ru="Увидел premium teaser",
            value=saw_teaser,
            conversion_from_prev=(
                round(saw_teaser / first_action * 100, 1) if first_action > 0 else 0
            ),
            dropoff_count=first_action - saw_teaser,
            dropoff_percent=(
                round((first_action - saw_teaser) / first_action * 100, 1)
                if first_action > 0
                else 0
            ),
        )
    )

    # Stage 5: Started payment (created payment record)
    started_payment = (
        await session.scalar(
            select(func.count(distinct(Payment.user_id))).where(
                Payment.user_id.in_(
                    select(User.id).where(User.created_at >= period_start)
                )
            )
        )
        or 0
    )
    stages.append(
        FunnelStage(
            name="started_payment",
            name_ru="Перешел к оплате",
            value=started_payment,
            conversion_from_prev=(
                round(started_payment / saw_teaser * 100, 1) if saw_teaser > 0 else 0
            ),
            dropoff_count=saw_teaser - started_payment,
            dropoff_percent=(
                round((saw_teaser - started_payment) / saw_teaser * 100, 1)
                if saw_teaser > 0
                else 0
            ),
        )
    )

    # Stage 6: Completed payment
    paid = (
        await session.scalar(
            select(func.count(distinct(Payment.user_id)))
            .where(
                Payment.user_id.in_(
                    select(User.id).where(User.created_at >= period_start)
                )
            )
            .where(Payment.status == "succeeded")
        )
        or 0
    )
    stages.append(
        FunnelStage(
            name="paid",
            name_ru="Оплатил",
            value=paid,
            conversion_from_prev=(
                round(paid / started_payment * 100, 1) if started_payment > 0 else 0
            ),
            dropoff_count=started_payment - paid,
            dropoff_percent=(
                round((started_payment - paid) / started_payment * 100, 1)
                if started_payment > 0
                else 0
            ),
        )
    )

    return FunnelData(stages=stages, period_days=days)
