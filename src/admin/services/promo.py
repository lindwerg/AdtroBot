"""Promo code management service."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.schemas import (
    CreatePromoCodeRequest,
    PromoCodeListItem,
    PromoCodeListResponse,
    UpdatePromoCodeRequest,
)
from src.db.models.promo import PromoCode


async def create_promo_code(
    session: AsyncSession,
    request: CreatePromoCodeRequest,
) -> PromoCode:
    """Create a new promo code."""
    # Check if code already exists
    existing = await session.scalar(
        select(PromoCode).where(PromoCode.code == request.code.upper())
    )
    if existing:
        raise ValueError("Promo code already exists")

    promo = PromoCode(
        code=request.code.upper(),
        discount_percent=request.discount_percent,
        valid_until=request.valid_until,
        max_uses=request.max_uses,
        partner_id=request.partner_id,
        partner_commission_percent=request.partner_commission_percent,
        is_active=True,
    )
    session.add(promo)
    await session.commit()
    await session.refresh(promo)
    return promo


async def list_promo_codes(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    is_active: bool | None = None,
) -> PromoCodeListResponse:
    """List promo codes with pagination."""
    query = select(PromoCode)

    if is_active is not None:
        query = query.where(PromoCode.is_active == is_active)

    # Count
    count_query = select(func.count()).select_from(PromoCode)
    if is_active is not None:
        count_query = count_query.where(PromoCode.is_active == is_active)
    total = await session.scalar(count_query) or 0

    # Order and paginate
    query = query.order_by(PromoCode.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    promos = result.scalars().all()

    items = [PromoCodeListItem.model_validate(p) for p in promos]

    return PromoCodeListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def update_promo_code(
    session: AsyncSession,
    promo_id: int,
    request: UpdatePromoCodeRequest,
) -> bool:
    """Update a promo code."""
    promo = await session.get(PromoCode, promo_id)
    if not promo:
        return False

    if request.discount_percent is not None:
        promo.discount_percent = request.discount_percent
    if request.valid_until is not None:
        promo.valid_until = request.valid_until
    if request.max_uses is not None:
        promo.max_uses = request.max_uses
    if request.is_active is not None:
        promo.is_active = request.is_active

    await session.commit()
    return True


async def delete_promo_code(
    session: AsyncSession,
    promo_id: int,
) -> bool:
    """Delete a promo code."""
    promo = await session.get(PromoCode, promo_id)
    if not promo:
        return False

    await session.delete(promo)
    await session.commit()
    return True
