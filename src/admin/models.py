from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
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


class ABExperiment(Base):
    """A/B test experiment."""

    __tablename__ = "ab_experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metric to track: conversion, retention, revenue
    metric: Mapped[str] = mapped_column(String(50))

    # Traffic split percentage for variant B (0-100)
    variant_b_percent: Mapped[int] = mapped_column(SmallInteger, default=50)

    # Status: draft, running, paused, completed
    status: Mapped[str] = mapped_column(String(20), default="draft")

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class ABAssignment(Base):
    """User assignment to A/B experiment variant."""

    __tablename__ = "ab_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("ab_experiments.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    # Variant: "A" or "B"
    variant: Mapped[str] = mapped_column(String(1))

    # Conversion event recorded
    converted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    converted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        # One assignment per user per experiment
        UniqueConstraint(
            "experiment_id", "user_id", name="uq_ab_assignment_user_experiment"
        ),
    )
