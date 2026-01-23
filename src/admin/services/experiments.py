"""A/B experiments and UTM analytics service."""

import hashlib
from datetime import datetime, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.models import ABAssignment, ABExperiment
from src.admin.schemas import (
    CreateExperimentRequest,
    ExperimentListItem,
    ExperimentResults,
    ExperimentVariantStats,
    UTMAnalyticsResponse,
    UTMSourceStats,
)
from src.db.models.payment import Payment
from src.db.models.user import User


def assign_variant(user_id: int, experiment_id: int, variant_b_percent: int) -> str:
    """Deterministically assign user to variant.

    Uses hash to ensure consistent assignment across sessions.
    """
    hash_input = f"{user_id}:{experiment_id}"
    hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16) % 100
    return "B" if hash_value < variant_b_percent else "A"


async def create_experiment(
    session: AsyncSession,
    request: CreateExperimentRequest,
) -> ABExperiment:
    """Create a new A/B experiment."""
    experiment = ABExperiment(
        name=request.name,
        description=request.description,
        metric=request.metric,
        variant_b_percent=request.variant_b_percent,
        status="draft",
    )
    session.add(experiment)
    await session.commit()
    await session.refresh(experiment)
    return experiment


async def list_experiments(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ABExperiment], int]:
    """List all experiments with pagination."""
    query = select(ABExperiment).order_by(ABExperiment.created_at.desc())

    total = await session.scalar(select(func.count()).select_from(ABExperiment)) or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    experiments = list(result.scalars().all())

    return experiments, total


async def start_experiment(session: AsyncSession, experiment_id: int) -> bool:
    """Start an experiment."""
    exp = await session.get(ABExperiment, experiment_id)
    if not exp or exp.status not in ("draft", "paused"):
        return False

    exp.status = "running"
    exp.started_at = datetime.now(timezone.utc)
    await session.commit()
    return True


async def stop_experiment(session: AsyncSession, experiment_id: int) -> bool:
    """Stop/complete an experiment."""
    exp = await session.get(ABExperiment, experiment_id)
    if not exp or exp.status != "running":
        return False

    exp.status = "completed"
    exp.ended_at = datetime.now(timezone.utc)
    await session.commit()
    return True


async def get_experiment_results(
    session: AsyncSession,
    experiment_id: int,
) -> ExperimentResults | None:
    """Get experiment results with variant stats."""
    exp = await session.get(ABExperiment, experiment_id)
    if not exp:
        return None

    async def get_variant_stats(variant: str) -> ExperimentVariantStats:
        """Get stats for a single variant."""
        # Count users in variant
        users = (
            await session.scalar(
                select(func.count(ABAssignment.id))
                .where(ABAssignment.experiment_id == experiment_id)
                .where(ABAssignment.variant == variant)
            )
            or 0
        )

        # Count conversions
        conversions = (
            await session.scalar(
                select(func.count(ABAssignment.id))
                .where(ABAssignment.experiment_id == experiment_id)
                .where(ABAssignment.variant == variant)
                .where(ABAssignment.converted == True)  # noqa: E712
            )
            or 0
        )

        rate = (conversions / users * 100) if users > 0 else 0

        return ExperimentVariantStats(
            variant=variant,
            users=users,
            conversions=conversions,
            conversion_rate=round(rate, 2),
        )

    variant_a = await get_variant_stats("A")
    variant_b = await get_variant_stats("B")

    # Simple winner determination (> 5% difference and min 100 users per variant)
    winner = None
    if variant_a.users >= 100 and variant_b.users >= 100:
        diff = abs(variant_a.conversion_rate - variant_b.conversion_rate)
        if diff > 5:
            winner = "A" if variant_a.conversion_rate > variant_b.conversion_rate else "B"

    return ExperimentResults(
        experiment=ExperimentListItem.model_validate(exp),
        variant_a=variant_a,
        variant_b=variant_b,
        winner=winner,
    )


async def get_utm_analytics(session: AsyncSession) -> UTMAnalyticsResponse:
    """Get UTM source analytics."""
    # Get all distinct sources with user counts
    sources_query = (
        select(
            User.utm_source,
            func.count(User.id).label("users"),
            func.sum(case((User.is_premium == True, 1), else_=0)).label("premium"),  # noqa: E712
        )
        .where(User.utm_source.isnot(None))
        .group_by(User.utm_source)
        .order_by(func.count(User.id).desc())
    )

    result = await session.execute(sources_query)
    rows = result.all()

    sources = []
    total_users = 0

    for row in rows:
        source = row[0]
        users = row[1]
        premium = row[2] or 0
        total_users += users

        # Get revenue for this source
        revenue = (
            await session.scalar(
                select(func.coalesce(func.sum(Payment.amount), 0))
                .join(User, Payment.user_id == User.id)
                .where(User.utm_source == source)
                .where(Payment.status == "succeeded")
            )
            or 0
        )

        sources.append(
            UTMSourceStats(
                source=source,
                users=users,
                premium_users=premium,
                conversion_rate=round(premium / users * 100, 2) if users > 0 else 0,
                total_revenue=revenue,
            )
        )

    return UTMAnalyticsResponse(sources=sources, total_users=total_users)
