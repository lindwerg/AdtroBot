"""Horoscope cache and view tracking models."""

from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class HoroscopeCache(Base):
    """Cached AI-generated horoscopes.

    Stores daily horoscopes for each zodiac sign to avoid repeated AI calls.
    Entries are unique per (zodiac_sign, horoscope_date) combination.
    """

    __tablename__ = "horoscope_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    zodiac_sign: Mapped[str] = mapped_column(String(20), index=True)
    horoscope_date: Mapped[date] = mapped_column(Date, index=True)
    content: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
    )

    __table_args__ = (
        UniqueConstraint(
            "zodiac_sign", "horoscope_date", name="uq_horoscope_cache_sign_date"
        ),
    )

    def __repr__(self) -> str:
        return f"<HoroscopeCache(sign={self.zodiac_sign}, date={self.horoscope_date})>"


class HoroscopeView(Base):
    """Daily horoscope view counts per zodiac sign.

    Tracks how many times each zodiac sign's horoscope was viewed per day.
    Used for admin dashboard metrics (MON-01).
    """

    __tablename__ = "horoscope_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    zodiac_sign: Mapped[str] = mapped_column(String(20))
    view_date: Mapped[date] = mapped_column(Date)
    view_count: Mapped[int] = mapped_column(Integer, server_default="0")

    __table_args__ = (
        UniqueConstraint(
            "zodiac_sign", "view_date", name="uq_horoscope_views_sign_date"
        ),
    )

    def __repr__(self) -> str:
        return f"<HoroscopeView(sign={self.zodiac_sign}, date={self.view_date}, count={self.view_count})>"


class PremiumHoroscopeCache(Base):
    """Cached premium (personalized) horoscopes with natal chart data.

    Stores premium horoscopes per user and date to avoid regenerating
    if user requests the same horoscope multiple times in a day.
    """

    __tablename__ = "premium_horoscope_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    horoscope_date: Mapped[date] = mapped_column(Date, index=True)
    content: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "horoscope_date", name="uq_premium_horoscope_cache_user_date"
        ),
    )

    def __repr__(self) -> str:
        return f"<PremiumHoroscopeCache(user_id={self.user_id}, date={self.horoscope_date})>"
