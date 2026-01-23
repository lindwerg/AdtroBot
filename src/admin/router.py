from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.auth import create_access_token, get_current_admin, verify_password
from src.admin.models import Admin
from src.admin.schemas import (
    AdminInfo,
    BulkActionRequest,
    BulkActionResponse,
    DashboardMetrics,
    FunnelData,
    GiftRequest,
    PaymentListResponse,
    SubscriptionListResponse,
    Token,
    UpdateSubscriptionRequest,
    UpdateSubscriptionStatusRequest,
    UserDetail,
    UserListResponse,
)
from src.admin.services.analytics import get_dashboard_metrics, get_funnel_data
from src.admin.services.payments import (
    list_payments,
    list_subscriptions,
    update_subscription_status,
)
from src.admin.services.users import (
    bulk_action,
    get_user_detail,
    gift_to_user,
    list_users,
    update_user_subscription,
)
from src.config import settings
from src.db.engine import get_session

admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> Token:
    """Authenticate admin and return JWT token."""
    result = await session.execute(
        select(Admin).where(Admin.username == form_data.username)
    )
    admin = result.scalar_one_or_none()

    if not admin or not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": admin.username},
        expires_delta=timedelta(minutes=settings.admin_jwt_expire_minutes),
    )
    return Token(access_token=access_token)


@admin_router.get("/me", response_model=AdminInfo)
async def get_me(current_admin: Admin = Depends(get_current_admin)) -> AdminInfo:
    """Get current admin info."""
    return AdminInfo.model_validate(current_admin)


# Dashboard endpoints


@admin_router.get("/dashboard", response_model=DashboardMetrics)
async def dashboard(
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> DashboardMetrics:
    """Get dashboard KPI metrics."""
    return await get_dashboard_metrics(session)


@admin_router.get("/funnel", response_model=FunnelData)
async def funnel(
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> FunnelData:
    """Get conversion funnel data."""
    return await get_funnel_data(session, days)


# User management endpoints


@admin_router.get("/users", response_model=UserListResponse)
async def users_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    zodiac_sign: str | None = Query(None),
    is_premium: bool | None = Query(None),
    has_detailed_natal: bool | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> UserListResponse:
    """List users with filters and pagination."""
    return await list_users(
        session,
        page=page,
        page_size=page_size,
        search=search,
        zodiac_sign=zodiac_sign,
        is_premium=is_premium,
        has_detailed_natal=has_detailed_natal,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@admin_router.get("/users/{user_id}", response_model=UserDetail)
async def user_detail(
    user_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> UserDetail:
    """Get detailed user info."""
    user = await get_user_detail(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@admin_router.patch("/users/{user_id}/subscription")
async def update_subscription(
    user_id: int = Path(...),
    request: UpdateSubscriptionRequest = ...,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> dict[str, str]:
    """Update user subscription (activate/cancel/extend)."""
    success = await update_user_subscription(session, user_id, request)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}


@admin_router.post("/users/{user_id}/gift")
async def gift_user(
    user_id: int = Path(...),
    request: GiftRequest = ...,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> dict[str, str]:
    """Give gift to user (premium days, detailed natal, spreads)."""
    success = await gift_to_user(session, user_id, request)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}


@admin_router.post("/users/bulk", response_model=BulkActionResponse)
async def users_bulk_action(
    request: BulkActionRequest,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> BulkActionResponse:
    """Perform bulk action on multiple users."""
    return await bulk_action(session, request)


# Payments and Subscriptions endpoints


@admin_router.get("/payments", response_model=PaymentListResponse)
async def payments_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    user_search: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> PaymentListResponse:
    """List payments with filters and pagination."""
    return await list_payments(
        session,
        page=page,
        page_size=page_size,
        status=status,
        user_search=user_search,
    )


@admin_router.get("/subscriptions", response_model=SubscriptionListResponse)
async def subscriptions_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    plan: str | None = Query(None),
    user_search: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> SubscriptionListResponse:
    """List subscriptions with filters and pagination."""
    return await list_subscriptions(
        session,
        page=page,
        page_size=page_size,
        status=status,
        plan=plan,
        user_search=user_search,
    )


@admin_router.patch("/subscriptions/{subscription_id}")
async def update_sub_status(
    subscription_id: int = Path(...),
    request: UpdateSubscriptionStatusRequest = ...,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> dict[str, str]:
    """Update subscription status."""
    success = await update_subscription_status(session, subscription_id, request)
    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"status": "ok"}
