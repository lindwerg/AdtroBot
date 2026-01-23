"""TarotSpread model for storing spread history."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class TarotSpread(Base):
    """Store tarot spread history for users."""

    __tablename__ = "tarot_spreads"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    # Spread type: "three_card" | "celtic_cross"
    spread_type: Mapped[str] = mapped_column(String(20))

    # User's question
    question: Mapped[str] = mapped_column(Text)

    # Cards drawn: [{"card_id": "ar01", "reversed": false, "position": 1}, ...]
    cards: Mapped[dict] = mapped_column(JSON)

    # Stored AI interpretation for history viewing
    interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
