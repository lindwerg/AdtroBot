"""AI usage tracking model for cost analytics."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.sql import func

from src.db.models.base import Base


class AIUsage(Base):
    """Tracks AI API usage for cost analytics and unit economics."""

    __tablename__ = "ai_usage"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), index=True, nullable=True
    )  # nullable for system operations
    created_at = Column(DateTime, default=func.now(), index=True)
    operation = Column(
        String(50), index=True
    )  # horoscope, tarot, natal_chart, card_of_day, celtic_cross
    model = Column(String(100))  # openai/gpt-4o-mini
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_dollars = Column(Float, nullable=True)  # from OpenRouter response or calculated
    generation_id = Column(String(100), nullable=True)  # OpenRouter generation ID
    latency_ms = Column(Integer, nullable=True)  # request duration
