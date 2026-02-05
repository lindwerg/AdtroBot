"""Global discount management service."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.schemas import (
    CreateGlobalDiscountRequest,
    GlobalDiscountListItem,
    GlobalDiscountListResponse,
    UpdateGlobalDiscountRequest,
)
from src.db.models.global_discount import GlobalDiscount


async def create_global_discount(
    session: AsyncSession,
    request: CreateGlobalDiscountRequest,
) -> GlobalDiscount:
    discount = GlobalDiscount(
        name=request.name,
        target_plan=request.target_plan,
        discount_percent=request.discount_percent,
        active_until=request.active_until,
        is_active=True,
    )
    session.add(discount)
    await session.commit()
    await session.refresh(discount)
    return discount


async def list_global_discounts(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    is_active: bool | None = None,
) -> GlobalDiscountListResponse:
    query = select(GlobalDiscount)
    count_query = select(func.count()).select_from(GlobalDiscount)

    if is_active is not None:
        query = query.where(GlobalDiscount.is_active == is_active)
        count_query = count_query.where(GlobalDiscount.is_active == is_active)

    total = await session.scalar(count_query) or 0

    query = query.order_by(GlobalDiscount.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    discounts = result.scalars().all()
    items = [GlobalDiscountListItem.model_validate(d) for d in discounts]

    return GlobalDiscountListResponse(items=items, total=total, page=page, page_size=page_size)


async def update_global_discount(
    session: AsyncSession,
    discount_id: int,
    request: UpdateGlobalDiscountRequest,
) -> bool:
    discount = await session.get(GlobalDiscount, discount_id)
    if not discount:
        return False

    if request.name is not None:
        discount.name = request.name
    if request.discount_percent is not None:
        discount.discount_percent = request.discount_percent
    if request.active_until is not None:
        discount.active_until = request.active_until
    if request.is_active is not None:
        discount.is_active = request.is_active

    await session.commit()
    return True


async def delete_global_discount(
    session: AsyncSession,
    discount_id: int,
) -> bool:
    discount = await session.get(GlobalDiscount, discount_id)
    if not discount:
        return False

    await session.delete(discount)
    await session.commit()
    return True
