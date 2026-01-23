from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Birth data for astrology
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    zodiac_sign: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Notification settings
    timezone: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default="Europe/Moscow"
    )
    notification_hour: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, default=9
    )  # 0-23
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    # Tarot - Card of the day cache
    card_of_day_id: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # name_short (e.g., "ar00")
    card_of_day_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )  # Cache valid until this date (user timezone)
    card_of_day_reversed: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )  # True if card is reversed

    # Tarot - Daily spread limits
    tarot_spread_count: Mapped[int] = mapped_column(
        SmallInteger, default=0, server_default="0"
    )  # Spreads used today
    spread_reset_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )  # Date of last reset (user timezone)

    # Subscription status (denormalized for quick access)
    is_premium: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    premium_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Daily spread limit (1 for free, 20 for premium)
    daily_spread_limit: Mapped[int] = mapped_column(
        SmallInteger, default=1, server_default="1"
    )
