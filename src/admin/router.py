from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.auth import create_access_token, get_current_admin, verify_password
from src.admin.models import Admin
from src.admin.schemas import (
    AdminInfo,
    BulkActionRequest,
    BulkActionResponse,
    CreateExperimentRequest,
    CreatePromoCodeRequest,
    DashboardMetrics,
    ExperimentListItem,
    ExperimentResults,
    FunnelData,
    GiftRequest,
    HoroscopeContentItem,
    HoroscopeContentListResponse,
    MessageHistoryResponse,
    MonitoringResponse,
    PaymentListResponse,
    PromoCodeListItem,
    PromoCodeListResponse,
    SendMessageRequest,
    SendMessageResponse,
    SubscriptionListResponse,
    TarotSpreadDetail,
    TarotSpreadListResponse,
    Token,
    UpdateHoroscopeContentRequest,
    UpdatePromoCodeRequest,
    UpdateSubscriptionRequest,
    UpdateSubscriptionStatusRequest,
    UserDetail,
    UserListResponse,
    UTMAnalyticsResponse,
)
from src.admin.services.monitoring import get_monitoring_data
from src.admin.services.analytics import get_dashboard_metrics, get_funnel_data
from src.admin.services.experiments import (
    create_experiment,
    get_experiment_results,
    get_utm_analytics,
    list_experiments,
    start_experiment,
    stop_experiment,
)
from src.admin.services.content import (
    get_all_horoscope_content,
    get_horoscope_content,
    update_horoscope_content,
)
from src.admin.services.export import (
    export_metrics_csv,
    export_payments_csv,
    export_users_csv,
)
from src.admin.services.promo import (
    create_promo_code,
    delete_promo_code,
    list_promo_codes,
    update_promo_code,
)
from src.admin.services.payments import (
    list_payments,
    list_subscriptions,
    update_subscription_status,
)
from src.admin.services.messaging import (
    cancel_scheduled_message,
    get_message_history,
    send_or_schedule_message,
)
from src.admin.services.spreads import get_spread_detail, get_spreads
from src.admin.services.users import (
    bulk_action,
    get_user_detail,
    gift_to_user,
    list_users,
    update_user_subscription,
)
from src.config import settings
from src.db.engine import get_session

admin_router = APIRouter(prefix="/admin/api", tags=["admin"])


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


# Tarot spreads endpoints


@admin_router.get("/tarot-spreads", response_model=TarotSpreadListResponse)
async def list_tarot_spreads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int | None = Query(None),
    search: str | None = Query(None, description="Search in question text"),
    spread_type: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> TarotSpreadListResponse:
    """Get tarot spreads with filters."""
    return await get_spreads(
        session,
        page=page,
        page_size=page_size,
        user_id=user_id,
        search=search,
        spread_type=spread_type,
        date_from=date_from,
        date_to=date_to,
    )


@admin_router.get("/tarot-spreads/{spread_id}", response_model=TarotSpreadDetail)
async def get_tarot_spread(
    spread_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> TarotSpreadDetail:
    """Get detailed spread info with cards and interpretation."""
    spread = await get_spread_detail(session, spread_id)
    if not spread:
        raise HTTPException(status_code=404, detail="Spread not found")
    return spread


# Messaging endpoints


@admin_router.post("/messages", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> SendMessageResponse:
    """Send or schedule a message."""
    return await send_or_schedule_message(session, request, current_admin.id)


@admin_router.get("/messages", response_model=MessageHistoryResponse)
async def messages_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> MessageHistoryResponse:
    """Get message history."""
    return await get_message_history(session, page, page_size)


@admin_router.delete("/messages/{message_id}")
async def cancel_message(
    message_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> dict[str, str]:
    """Cancel a scheduled message."""
    success = await cancel_scheduled_message(session, message_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel message")
    return {"status": "canceled"}


# Content management endpoints


@admin_router.get("/content/horoscopes", response_model=HoroscopeContentListResponse)
async def list_horoscope_content(
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> HoroscopeContentListResponse:
    """Get horoscope content for all zodiac signs."""
    return await get_all_horoscope_content(session)


@admin_router.get(
    "/content/horoscopes/{zodiac_sign}", response_model=HoroscopeContentItem
)
async def get_content_by_sign(
    zodiac_sign: str = Path(...),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> HoroscopeContentItem:
    """Get horoscope content for specific zodiac sign."""
    content = await get_horoscope_content(session, zodiac_sign)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return HoroscopeContentItem.model_validate(content)


@admin_router.put(
    "/content/horoscopes/{zodiac_sign}", response_model=HoroscopeContentItem
)
async def update_content_by_sign(
    request: UpdateHoroscopeContentRequest,
    zodiac_sign: str = Path(...),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> HoroscopeContentItem:
    """Update horoscope content for specific zodiac sign."""
    content = await update_horoscope_content(
        session, zodiac_sign, request, current_admin.id
    )
    return HoroscopeContentItem.model_validate(content)


# Promo codes management endpoints


@admin_router.post("/promo-codes", response_model=PromoCodeListItem)
async def create_promo(
    request: CreatePromoCodeRequest,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> PromoCodeListItem:
    """Create a new promo code."""
    try:
        promo = await create_promo_code(session, request)
        return PromoCodeListItem.model_validate(promo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@admin_router.get("/promo-codes", response_model=PromoCodeListResponse)
async def promo_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> PromoCodeListResponse:
    """List promo codes."""
    return await list_promo_codes(session, page, page_size, is_active)


@admin_router.patch("/promo-codes/{promo_id}")
async def update_promo(
    promo_id: int = Path(...),
    request: UpdatePromoCodeRequest = ...,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> dict[str, str]:
    """Update a promo code."""
    success = await update_promo_code(session, promo_id, request)
    if not success:
        raise HTTPException(status_code=404, detail="Promo code not found")
    return {"status": "ok"}


@admin_router.delete("/promo-codes/{promo_id}")
async def delete_promo(
    promo_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> dict[str, str]:
    """Delete a promo code."""
    success = await delete_promo_code(session, promo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Promo code not found")
    return {"status": "deleted"}


# Export endpoints


@admin_router.get("/export/users")
async def export_users(
    zodiac_sign: str | None = Query(None),
    is_premium: bool | None = Query(None),
    has_detailed_natal: bool | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> StreamingResponse:
    """Export users to CSV."""
    stream = await export_users_csv(
        session,
        zodiac_sign=zodiac_sign,
        is_premium=is_premium,
        has_detailed_natal=has_detailed_natal,
    )
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
    )


@admin_router.get("/export/payments")
async def export_payments(
    status: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> StreamingResponse:
    """Export payments to CSV."""
    stream = await export_payments_csv(session, status=status)
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=payments.csv"},
    )


@admin_router.get("/export/metrics")
async def export_metrics(
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> StreamingResponse:
    """Export daily metrics to CSV."""
    stream = await export_metrics_csv(session, days=days)
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=metrics.csv"},
    )


# A/B Experiments endpoints


@admin_router.post("/experiments", response_model=ExperimentListItem)
async def create_exp(
    request: CreateExperimentRequest,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> ExperimentListItem:
    """Create a new A/B experiment."""
    exp = await create_experiment(session, request)
    return ExperimentListItem.model_validate(exp)


@admin_router.get("/experiments")
async def list_exps(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> dict:
    """List all experiments."""
    experiments, total = await list_experiments(session, page, page_size)
    return {
        "items": [ExperimentListItem.model_validate(e) for e in experiments],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@admin_router.post("/experiments/{experiment_id}/start")
async def start_exp(
    experiment_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> dict[str, str]:
    """Start an experiment."""
    success = await start_experiment(session, experiment_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot start experiment")
    return {"status": "running"}


@admin_router.post("/experiments/{experiment_id}/stop")
async def stop_exp(
    experiment_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> dict[str, str]:
    """Stop an experiment."""
    success = await stop_experiment(session, experiment_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot stop experiment")
    return {"status": "completed"}


@admin_router.get("/experiments/{experiment_id}/results", response_model=ExperimentResults)
async def exp_results(
    experiment_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> ExperimentResults:
    """Get experiment results."""
    results = await get_experiment_results(session, experiment_id)
    if not results:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return results


@admin_router.get("/utm-analytics", response_model=UTMAnalyticsResponse)
async def utm_analytics(
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> UTMAnalyticsResponse:
    """Get UTM source analytics."""
    return await get_utm_analytics(session)


# === Monitoring Endpoints ===


@admin_router.get("/monitoring", response_model=MonitoringResponse)
async def monitoring_dashboard(
    range: str = Query("7d", pattern="^(24h|7d|30d)$", description="Time range"),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> MonitoringResponse:
    """Get monitoring dashboard data.

    Args:
        range: Time range - 24h, 7d, or 30d

    Returns:
        Monitoring data with active users, API costs, unit economics
    """
    from typing import Literal

    range_type: Literal["24h", "7d", "30d"] = range  # type: ignore

    try:
        data = await get_monitoring_data(session, range_type)
        return MonitoringResponse(**data)
    except Exception as e:
        # If ai_usage table doesn't exist or other DB error, return default values
        import logging
        logging.error(f"Monitoring data error: {e}")
        return MonitoringResponse(
            range=range_type,
            active_users={"dau": 0, "wau": 0, "mau": 0},
            api_costs={
                "total_cost": 0,
                "total_tokens": 0,
                "total_requests": 0,
                "by_operation": [],
                "by_day": [],
            },
            unit_economics={
                "total_cost": 0,
                "active_users": 0,
                "paying_users": 0,
                "active_paying_users": 0,
                "cost_per_active_user": 0,
                "cost_per_paying_user": 0,
            },
            error_stats={
                "error_count": 0,
                "error_rate": 0.0,
                "avg_response_time_ms": 0,
            },
        )
