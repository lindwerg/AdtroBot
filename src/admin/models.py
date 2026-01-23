from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class Admin(Base):
    """Admin user model for panel authentication."""

    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ScheduledMessage(Base):
    """Scheduled or sent broadcast messages."""

    __tablename__ = "scheduled_messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Message content
    text: Mapped[str] = mapped_column(Text)

    # Target filters (JSON): {"is_premium": true, "zodiac_sign": "aries"}
    # Empty dict = all users
    filters: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")

    # Single user target (if not broadcast)
    target_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Scheduling
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # None = send immediately
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Stats
    total_recipients: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    delivered_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    failed_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Status: pending, sending, sent, canceled
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)  # admin id


class HoroscopeContent(Base):
    """Editable horoscope content for each zodiac sign."""

    __tablename__ = "horoscope_content"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Zodiac sign: aries, taurus, gemini, cancer, leo, virgo,
    # libra, scorpio, sagittarius, capricorn, aquarius, pisces
    zodiac_sign: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    # Base horoscope text (admin can edit this)
    # Used as template or additional context for AI generation
    base_text: Mapped[str] = mapped_column(Text, default="")

    # Additional context or notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Last updated
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    updated_by: Mapped[int | None] = mapped_column(Integer, nullable=True)  # admin id
