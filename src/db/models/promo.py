from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    # Discount: 10 = 10%
    discount_percent: Mapped[int] = mapped_column(SmallInteger)

    # Validity period
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Usage limits
    max_uses: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # None = unlimited
    current_uses: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )

    # Partner program (no FK yet, just ID for future)
    partner_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    partner_commission_percent: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
