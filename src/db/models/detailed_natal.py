"""Model for caching detailed natal interpretations."""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class DetailedNatal(Base):
    """Cached detailed natal chart interpretation.

    Stores AI-generated detailed interpretation (3000-5000 words).
    Cache valid for 7 days (natal chart doesn't change, but AI may improve).
    """

    __tablename__ = "detailed_natals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    interpretation: Mapped[str] = mapped_column(Text, nullable=False)
    telegraph_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
