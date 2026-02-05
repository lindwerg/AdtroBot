"""Global discount service — fetch active discounts and calculate prices."""

from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.global_discount import GlobalDiscount
from src.services.payment.schemas import PLAN_PRICES, PLAN_PRICES_STR, PaymentPlan

logger = structlog.get_logger()


async def get_active_discount(
    session: AsyncSession,
    plan: PaymentPlan,
) -> GlobalDiscount | None:
    """Get the active global discount for a plan (if any)."""
    now = datetime.now(timezone.utc)

    stmt = (
        select(GlobalDiscount)
        .where(
            GlobalDiscount.is_active.is_(True),
            GlobalDiscount.target_plan.in_([plan.value, "all"]),
            GlobalDiscount.active_from <= now,
        )
        .where((GlobalDiscount.active_until.is_(None)) | (GlobalDiscount.active_until > now))
        .order_by(GlobalDiscount.discount_percent.desc())
        .limit(1)
    )

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def calculate_discounted_price(
    plan: PaymentPlan,
    discount: GlobalDiscount | None,
) -> tuple[int, str]:
    """Calculate price with discount applied.

    Returns:
        (price_kopeks, price_str_for_yookassa)
        Example: (14950, "149.50")
    """
    base_kopeks = PLAN_PRICES[plan]

    if not discount:
        return base_kopeks, PLAN_PRICES_STR[plan]

    discounted_kopeks = int(base_kopeks * (100 - discount.discount_percent) / 100)
    discounted_str = f"{discounted_kopeks / 100:.2f}"

    logger.info(
        "discount_applied",
        plan=plan.value,
        discount_name=discount.name,
        percent=discount.discount_percent,
        original=base_kopeks,
        discounted=discounted_kopeks,
    )

    return discounted_kopeks, discounted_str


def format_button_price(
    plan: PaymentPlan,
    discount: GlobalDiscount | None,
) -> str:
    """Format price text for Telegram inline button (plain text only).

    With discount:    "150 р. (было 299)"
    Without discount: "299 р."
    """
    base_rub = PLAN_PRICES[plan] // 100

    if not discount:
        return f"{base_rub} р."

    discounted_kopeks, _ = calculate_discounted_price(plan, discount)
    discounted_rub = discounted_kopeks // 100
    return f"{discounted_rub} р. (было {base_rub})"
