"""AI cost tracking utilities."""

import time
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.ai_usage import AIUsage
from src.monitoring.metrics import (
    AI_COST_TOTAL,
    AI_REQUEST_DURATION,
    AI_REQUESTS_TOTAL,
    AI_TOKENS_TOTAL,
)

logger = structlog.get_logger()

# GPT-4o-mini pricing (per 1M tokens) - fallback if cost not in response
GPT4O_MINI_PRICING = {
    "prompt": 0.15 / 1_000_000,      # $0.15 per 1M input tokens
    "completion": 0.60 / 1_000_000,  # $0.60 per 1M output tokens
}


async def record_ai_usage(
    session: AsyncSession,
    user_id: int | None,
    operation: str,
    model: str,
    response: Any,
    latency_ms: int,
) -> None:
    """Record AI usage to database and update Prometheus metrics.

    Args:
        session: Database session
        user_id: User ID (None for system operations like background horoscope generation)
        operation: Operation type (horoscope, tarot, natal_chart, etc.)
        model: Model name (e.g., "openai/gpt-4o-mini")
        response: OpenAI/OpenRouter response object
        latency_ms: Request duration in milliseconds
    """
    try:
        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens

        # Try to get cost from OpenRouter response, fallback to calculation
        cost_dollars = None
        if hasattr(response, "x_openrouter"):
            cost_dollars = response.x_openrouter.get("cost")

        if cost_dollars is None:
            # Calculate based on token pricing
            cost_dollars = (
                prompt_tokens * GPT4O_MINI_PRICING["prompt"] +
                completion_tokens * GPT4O_MINI_PRICING["completion"]
            )

        generation_id = getattr(response, "id", None)

        # Record to database
        ai_usage = AIUsage(
            user_id=user_id,
            operation=operation,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_dollars=cost_dollars,
            generation_id=generation_id,
            latency_ms=latency_ms,
        )
        session.add(ai_usage)
        await session.commit()

        # Update Prometheus metrics
        model_short = model.split("/")[-1] if "/" in model else model

        AI_TOKENS_TOTAL.labels(
            operation=operation,
            model=model_short,
            token_type="prompt"
        ).inc(prompt_tokens)

        AI_TOKENS_TOTAL.labels(
            operation=operation,
            model=model_short,
            token_type="completion"
        ).inc(completion_tokens)

        if cost_dollars:
            AI_COST_TOTAL.labels(
                operation=operation,
                model=model_short
            ).inc(cost_dollars)

        AI_REQUEST_DURATION.labels(
            operation=operation,
            model=model_short
        ).observe(latency_ms / 1000)  # Convert to seconds

        AI_REQUESTS_TOTAL.labels(
            operation=operation,
            model=model_short,
            status="success"
        ).inc()

        logger.debug(
            "ai_usage_recorded",
            user_id=user_id,
            operation=operation,
            tokens=total_tokens,
            cost=cost_dollars,
            latency_ms=latency_ms,
        )

    except Exception as e:
        logger.error("failed_to_record_ai_usage", error=str(e))
        # Don't raise - cost tracking failure shouldn't break AI response


def record_ai_error(operation: str, model: str, error_type: str) -> None:
    """Record AI error to Prometheus metrics."""
    model_short = model.split("/")[-1] if "/" in model else model
    AI_REQUESTS_TOTAL.labels(
        operation=operation,
        model=model_short,
        status="error"
    ).inc()
