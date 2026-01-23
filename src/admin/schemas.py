from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    """JWT token response schema."""

    access_token: str
    token_type: str = "bearer"


class AdminInfo(BaseModel):
    """Admin info response schema."""

    id: int
    username: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# User management schemas


class UserListItem(BaseModel):
    """User item in list response."""

    id: int
    telegram_id: int
    username: str | None
    zodiac_sign: str | None
    is_premium: bool
    premium_until: datetime | None
    created_at: datetime
    tarot_spread_count: int
    daily_spread_limit: int
    detailed_natal_purchased_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Paginated user list response."""

    items: list[UserListItem]
    total: int
    page: int
    page_size: int
    pages: int


class PaymentHistoryItem(BaseModel):
    """Payment item in user detail."""

    id: str
    amount: int  # kopeks
    status: str
    description: str | None
    created_at: datetime
    paid_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionInfo(BaseModel):
    """Subscription info in user detail."""

    id: int
    plan: str
    status: str
    started_at: datetime
    current_period_end: datetime
    canceled_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class TarotSpreadHistoryItem(BaseModel):
    """Tarot spread item in user detail."""

    id: int
    spread_type: str
    question: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserDetail(BaseModel):
    """Full user detail with history."""

    id: int
    telegram_id: int
    username: str | None
    birth_date: date | None
    zodiac_sign: str | None
    birth_time: str | None  # HH:MM format
    birth_city: str | None
    timezone: str | None
    notifications_enabled: bool
    notification_hour: int | None
    is_premium: bool
    premium_until: datetime | None
    daily_spread_limit: int
    tarot_spread_count: int
    detailed_natal_purchased_at: datetime | None
    created_at: datetime

    subscription: SubscriptionInfo | None
    payments: list[PaymentHistoryItem]
    recent_spreads: list[TarotSpreadHistoryItem]

    model_config = ConfigDict(from_attributes=True)


class UpdateSubscriptionRequest(BaseModel):
    """Request to update user subscription."""

    action: Literal["activate", "cancel", "extend"]
    days: int | None = None  # For extend action


class GiftRequest(BaseModel):
    """Request to give gift to user."""

    gift_type: Literal["premium_days", "detailed_natal", "tarot_spreads"]
    value: int  # days for premium, count for spreads


class BulkActionRequest(BaseModel):
    """Request for bulk action on users."""

    user_ids: list[int]
    action: Literal["activate_premium", "cancel_premium", "gift_spreads"]
    value: int | None = None  # For gift_spreads


class BulkActionResponse(BaseModel):
    """Response for bulk action."""

    success_count: int
    failed_count: int
    errors: list[str]


# === Dashboard Schemas ===


class SparklinePoint(BaseModel):
    """Single data point for sparkline chart."""

    date: str  # YYYY-MM-DD
    value: float


class KPIMetric(BaseModel):
    """KPI metric with trend and sparkline."""

    value: float | int | str
    trend: float  # percentage change vs previous period
    sparkline: list[SparklinePoint]


class DashboardMetrics(BaseModel):
    """Dashboard KPI metrics response."""

    # Growth & Activity
    active_users_dau: KPIMetric
    active_users_mau: KPIMetric
    new_users_today: KPIMetric
    retention_d7: KPIMetric

    # Product Metrics
    horoscopes_today: KPIMetric
    tarot_spreads_today: KPIMetric
    most_active_zodiac: str

    # Revenue
    revenue_today: KPIMetric
    revenue_month: KPIMetric
    conversion_rate: KPIMetric
    arpu: KPIMetric

    # Bot Health (placeholder - requires logging)
    error_rate: KPIMetric | None
    avg_response_time: KPIMetric | None

    # API Costs (placeholder - requires OpenRouter tracking)
    api_costs_today: KPIMetric | None
    api_costs_month: KPIMetric | None


class FunnelStage(BaseModel):
    """Single stage in conversion funnel."""

    name: str
    name_ru: str
    value: int
    conversion_from_prev: float | None  # None for first stage
    dropoff_count: int | None  # None for first stage
    dropoff_percent: float | None  # None for first stage


class FunnelData(BaseModel):
    """Conversion funnel data."""

    stages: list[FunnelStage]
    period_days: int


# === Payments & Subscriptions Management Schemas ===


class PaymentListItem(BaseModel):
    """Payment item in list response."""

    id: str
    user_id: int
    subscription_id: int | None
    amount: int  # kopeks
    currency: str
    status: str
    is_recurring: bool
    description: str | None
    created_at: datetime
    paid_at: datetime | None

    # Joined user info
    user_telegram_id: int | None = None
    user_username: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PaymentListResponse(BaseModel):
    """Paginated payment list response."""

    items: list[PaymentListItem]
    total: int
    page: int
    page_size: int
    total_amount: int  # Sum of succeeded payments (kopeks)


class SubscriptionListItem(BaseModel):
    """Subscription item in list response."""

    id: int
    user_id: int
    plan: str
    status: str
    payment_method_id: str | None
    started_at: datetime
    current_period_start: datetime
    current_period_end: datetime
    canceled_at: datetime | None
    created_at: datetime

    # Joined user info
    user_telegram_id: int | None = None
    user_username: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionListResponse(BaseModel):
    """Paginated subscription list response."""

    items: list[SubscriptionListItem]
    total: int
    page: int
    page_size: int


class UpdateSubscriptionStatusRequest(BaseModel):
    """Request to update subscription status."""

    status: str  # active, canceled, expired


# === Messaging Schemas ===


class SendMessageRequest(BaseModel):
    """Request to send or schedule a message."""

    text: str
    target_user_id: int | None = None  # For single user
    filters: dict | None = None  # For broadcast: {"is_premium": true, "zodiac_sign": "aries"}
    scheduled_at: datetime | None = None  # For scheduling


class MessageHistoryItem(BaseModel):
    """Single message in history."""

    id: int
    text: str
    filters: dict
    target_user_id: int | None
    scheduled_at: datetime | None
    sent_at: datetime | None
    total_recipients: int
    delivered_count: int
    failed_count: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageHistoryResponse(BaseModel):
    """Paginated message history response."""

    items: list[MessageHistoryItem]
    total: int
    page: int
    page_size: int


class SendMessageResponse(BaseModel):
    """Response after sending or scheduling message."""

    message_id: int
    status: str
    recipients_count: int


# === Tarot Spreads Schemas ===


class TarotSpreadListItem(BaseModel):
    """Tarot spread item in list response."""

    id: int
    user_id: int
    telegram_id: int | None = None
    username: str | None = None
    spread_type: str
    question: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TarotSpreadListResponse(BaseModel):
    """Paginated tarot spread list response."""

    items: list[TarotSpreadListItem]
    total: int
    page: int
    page_size: int


class CardPosition(BaseModel):
    """Card position in spread detail."""

    position: int
    position_name: str
    card_name: str
    is_reversed: bool


class TarotSpreadDetail(BaseModel):
    """Full tarot spread detail with cards and interpretation."""

    id: int
    user_id: int
    telegram_id: int | None = None
    username: str | None = None
    spread_type: str
    question: str
    cards: list[CardPosition]
    interpretation: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === Horoscope Content Management Schemas ===


class HoroscopeContentItem(BaseModel):
    """Horoscope content item for a zodiac sign."""

    id: int
    zodiac_sign: str
    base_text: str
    notes: str | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HoroscopeContentListResponse(BaseModel):
    """List of horoscope content for all zodiac signs."""

    items: list[HoroscopeContentItem]


class UpdateHoroscopeContentRequest(BaseModel):
    """Request to update horoscope content for a zodiac sign."""

    base_text: str
    notes: str | None = None


# === Promo Code Management Schemas ===


class CreatePromoCodeRequest(BaseModel):
    """Request to create a new promo code."""

    code: str
    discount_percent: int  # 10 = 10%
    valid_until: datetime | None = None
    max_uses: int | None = None  # None = unlimited
    partner_id: int | None = None
    partner_commission_percent: int | None = None


class PromoCodeListItem(BaseModel):
    """Promo code item in list response."""

    id: int
    code: str
    discount_percent: int
    valid_from: datetime
    valid_until: datetime | None
    max_uses: int | None
    current_uses: int
    partner_id: int | None
    partner_commission_percent: int | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromoCodeListResponse(BaseModel):
    """Paginated promo code list response."""

    items: list[PromoCodeListItem]
    total: int
    page: int
    page_size: int


class UpdatePromoCodeRequest(BaseModel):
    """Request to update a promo code."""

    discount_percent: int | None = None
    valid_until: datetime | None = None
    max_uses: int | None = None
    is_active: bool | None = None


# === A/B Experiments Schemas ===


class CreateExperimentRequest(BaseModel):
    """Request to create a new A/B experiment."""

    name: str
    description: str | None = None
    metric: str  # conversion, retention, revenue
    variant_b_percent: int = 50  # 0-100


class ExperimentListItem(BaseModel):
    """Experiment item in list response."""

    id: int
    name: str
    description: str | None
    metric: str
    variant_b_percent: int
    status: str
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperimentVariantStats(BaseModel):
    """Stats for a single variant in experiment results."""

    variant: str
    users: int
    conversions: int
    conversion_rate: float


class ExperimentResults(BaseModel):
    """Experiment results with variant stats."""

    experiment: ExperimentListItem
    variant_a: ExperimentVariantStats
    variant_b: ExperimentVariantStats
    winner: str | None  # "A", "B", or None if not significant


class UTMSourceStats(BaseModel):
    """Stats for a single UTM source."""

    source: str
    users: int
    premium_users: int
    conversion_rate: float
    total_revenue: int  # kopeks


class UTMAnalyticsResponse(BaseModel):
    """UTM analytics response with source breakdown."""

    sources: list[UTMSourceStats]
    total_users: int
