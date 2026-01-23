"""User management service."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.schemas import (
    BulkActionRequest,
    BulkActionResponse,
    GiftRequest,
    PaymentHistoryItem,
    SubscriptionInfo,
    TarotSpreadHistoryItem,
    UpdateSubscriptionRequest,
    UserDetail,
    UserListItem,
    UserListResponse,
)
from src.db.models.payment import Payment
from src.db.models.subscription import Subscription
from src.db.models.tarot_spread import TarotSpread
from src.db.models.user import User


async def list_users(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    zodiac_sign: str | None = None,
    is_premium: bool | None = None,
    has_detailed_natal: bool | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> UserListResponse:
    """List users with filters and pagination."""
    query = select(User)

    # Search filter (telegram_id or username)
    if search:
        if search.isdigit():
            query = query.where(User.telegram_id == int(search))
        else:
            query = query.where(User.username.ilike(f"%{search}%"))

    # Zodiac filter
    if zodiac_sign:
        query = query.where(User.zodiac_sign == zodiac_sign)

    # Premium filter
    if is_premium is not None:
        query = query.where(User.is_premium == is_premium)

    # Detailed natal filter
    if has_detailed_natal is not None:
        if has_detailed_natal:
            query = query.where(User.detailed_natal_purchased_at.isnot(None))
        else:
            query = query.where(User.detailed_natal_purchased_at.is_(None))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query) or 0

    # Sort
    sort_column = getattr(User, sort_by, User.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    users = result.scalars().all()

    items = [UserListItem.model_validate(u) for u in users]

    return UserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


async def get_user_detail(session: AsyncSession, user_id: int) -> UserDetail | None:
    """Get detailed user info including history."""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None

    # Get subscription
    sub_result = await session.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    subscription = sub_result.scalar_one_or_none()

    # Get payments
    pay_result = await session.execute(
        select(Payment)
        .where(Payment.user_id == user_id)
        .order_by(Payment.created_at.desc())
        .limit(20)
    )
    payments = pay_result.scalars().all()

    # Get recent spreads
    spread_result = await session.execute(
        select(TarotSpread)
        .where(TarotSpread.user_id == user_id)
        .order_by(TarotSpread.created_at.desc())
        .limit(10)
    )
    spreads = spread_result.scalars().all()

    return UserDetail(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        birth_date=user.birth_date,
        zodiac_sign=user.zodiac_sign,
        birth_time=user.birth_time.strftime("%H:%M") if user.birth_time else None,
        birth_city=user.birth_city,
        timezone=user.timezone,
        notifications_enabled=user.notifications_enabled,
        notification_hour=user.notification_hour,
        is_premium=user.is_premium,
        premium_until=user.premium_until,
        daily_spread_limit=user.daily_spread_limit,
        tarot_spread_count=user.tarot_spread_count,
        detailed_natal_purchased_at=user.detailed_natal_purchased_at,
        created_at=user.created_at,
        subscription=SubscriptionInfo.model_validate(subscription)
        if subscription
        else None,
        payments=[PaymentHistoryItem.model_validate(p) for p in payments],
        recent_spreads=[TarotSpreadHistoryItem.model_validate(s) for s in spreads],
    )


async def update_user_subscription(
    session: AsyncSession,
    user_id: int,
    request: UpdateSubscriptionRequest,
) -> bool:
    """Update user subscription status."""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False

    now = datetime.now(timezone.utc)

    if request.action == "activate":
        user.is_premium = True
        user.premium_until = now + timedelta(days=30)
        user.daily_spread_limit = 20
    elif request.action == "cancel":
        user.is_premium = False
        user.premium_until = None
        user.daily_spread_limit = 1
    elif request.action == "extend" and request.days:
        if user.premium_until and user.premium_until > now:
            user.premium_until = user.premium_until + timedelta(days=request.days)
        else:
            user.is_premium = True
            user.premium_until = now + timedelta(days=request.days)
            user.daily_spread_limit = 20

    await session.commit()
    return True


async def gift_to_user(
    session: AsyncSession,
    user_id: int,
    request: GiftRequest,
) -> bool:
    """Give gift to user."""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False

    now = datetime.now(timezone.utc)

    if request.gift_type == "premium_days":
        if user.premium_until and user.premium_until > now:
            user.premium_until = user.premium_until + timedelta(days=request.value)
        else:
            user.is_premium = True
            user.premium_until = now + timedelta(days=request.value)
            user.daily_spread_limit = 20
    elif request.gift_type == "detailed_natal":
        user.detailed_natal_purchased_at = now
    elif request.gift_type == "tarot_spreads":
        user.daily_spread_limit = user.daily_spread_limit + request.value

    await session.commit()
    return True


async def bulk_action(
    session: AsyncSession,
    request: BulkActionRequest,
) -> BulkActionResponse:
    """Perform bulk action on users."""
    success = 0
    failed = 0
    errors: list[str] = []

    for user_id in request.user_ids:
        try:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                failed += 1
                errors.append(f"User {user_id} not found")
                continue

            now = datetime.now(timezone.utc)

            if request.action == "activate_premium":
                user.is_premium = True
                user.premium_until = now + timedelta(days=30)
                user.daily_spread_limit = 20
            elif request.action == "cancel_premium":
                user.is_premium = False
                user.premium_until = None
                user.daily_spread_limit = 1
            elif request.action == "gift_spreads" and request.value:
                user.daily_spread_limit = user.daily_spread_limit + request.value

            success += 1
        except Exception as e:
            failed += 1
            errors.append(f"User {user_id}: {str(e)}")

    await session.commit()
    return BulkActionResponse(
        success_count=success,
        failed_count=failed,
        errors=errors,
    )
