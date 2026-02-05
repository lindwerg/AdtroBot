"""Global discount model for time-limited promotions."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class GlobalDiscount(Base):
    __tablename__ = "global_discounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    target_plan: Mapped[str] = mapped_column(String(20))  # "monthly", "yearly", "all"
    discount_percent: Mapped[int] = mapped_column(SmallInteger)
    active_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    active_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
