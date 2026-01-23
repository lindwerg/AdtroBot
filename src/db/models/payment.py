from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class PaymentStatus(str, Enum):
    PENDING = "pending"
    WAITING_FOR_CAPTURE = "waiting_for_capture"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"


class Payment(Base):
    __tablename__ = "payments"

    # YooKassa payment ID as primary key
    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Amount in kopeks (29900 = 299.00 RUB)
    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(
        String(3), default="RUB", server_default="RUB"
    )
    status: Mapped[str] = mapped_column(String(30))

    # Recurring payment flag
    is_recurring: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    # Idempotency flag for webhook processing
    webhook_processed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
