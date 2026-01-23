"""Messaging service for admin panel."""

import asyncio
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.models import ScheduledMessage
from src.admin.schemas import (
    MessageHistoryItem,
    MessageHistoryResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from src.bot.bot import get_bot
from src.db.models.user import User

logger = structlog.get_logger()


async def send_message_to_user(telegram_id: int, text: str) -> bool:
    """Send message to single user via Telegram bot.

    IMPORTANT: get_bot() requires the bot to be initialized.
    In FastAPI context, this is handled by the lifespan manager in src/main.py
    which calls init_bot() on startup. If running outside FastAPI (e.g., tests),
    ensure init_bot() is called first.
    """
    try:
        bot = get_bot()
        await bot.send_message(chat_id=telegram_id, text=text)
        return True
    except RuntimeError as e:
        # Bot not initialized
        await logger.aerror(
            "Bot not initialized. Ensure FastAPI lifespan has started.",
            telegram_id=telegram_id,
            error=str(e),
        )
        return False
    except Exception as e:
        await logger.awarning(
            "Failed to send message to user",
            telegram_id=telegram_id,
            error=str(e),
        )
        return False


def build_user_query(filters: dict[str, Any]):
    """Build SQLAlchemy query from filters dict."""
    query = select(User.telegram_id)

    if filters.get("is_premium") is not None:
        query = query.where(User.is_premium == filters["is_premium"])

    if filters.get("zodiac_sign"):
        query = query.where(User.zodiac_sign == filters["zodiac_sign"])

    if filters.get("has_detailed_natal") is not None:
        if filters["has_detailed_natal"]:
            query = query.where(User.detailed_natal_purchased_at.isnot(None))
        else:
            query = query.where(User.detailed_natal_purchased_at.is_(None))

    if filters.get("notifications_enabled") is not None:
        query = query.where(User.notifications_enabled == filters["notifications_enabled"])

    return query


async def broadcast_message(
    session: AsyncSession,
    text: str,
    filters: dict[str, Any],
) -> tuple[int, int, int]:
    """Send message to all users matching filters.

    Returns: (total, delivered, failed)
    """
    query = build_user_query(filters)
    result = await session.execute(query)
    telegram_ids = [row[0] for row in result.fetchall()]

    total = len(telegram_ids)
    delivered = 0
    failed = 0

    # Telegram rate limit: ~30 msg/sec for bots
    # Send in batches with delay
    batch_size = 25
    delay_between_batches = 1.0  # seconds

    for i in range(0, total, batch_size):
        batch = telegram_ids[i : i + batch_size]
        tasks = [send_message_to_user(tid, text) for tid in batch]
        results = await asyncio.gather(*tasks)

        delivered += sum(1 for r in results if r)
        failed += sum(1 for r in results if not r)

        if i + batch_size < total:
            await asyncio.sleep(delay_between_batches)

    return total, delivered, failed


async def send_or_schedule_message(
    session: AsyncSession,
    request: SendMessageRequest,
    admin_id: int,
) -> SendMessageResponse:
    """Send message immediately or schedule for later."""

    # Create message record
    message = ScheduledMessage(
        text=request.text,
        filters=request.filters or {},
        target_user_id=request.target_user_id,
        scheduled_at=request.scheduled_at,
        status="pending",
        created_by=admin_id,
    )
    session.add(message)
    await session.flush()

    # If scheduled for later, just save and return
    if request.scheduled_at and request.scheduled_at > datetime.now(timezone.utc):
        await session.commit()
        return SendMessageResponse(
            message_id=message.id,
            status="scheduled",
            recipients_count=0,
        )

    # Send immediately
    message.status = "sending"
    await session.commit()

    if request.target_user_id:
        # Single user
        user = await session.scalar(
            select(User).where(User.id == request.target_user_id)
        )
        if user:
            success = await send_message_to_user(user.telegram_id, request.text)
            message.total_recipients = 1
            message.delivered_count = 1 if success else 0
            message.failed_count = 0 if success else 1
        else:
            message.total_recipients = 0
            message.delivered_count = 0
            message.failed_count = 0
    else:
        # Broadcast
        total, delivered, failed = await broadcast_message(
            session, request.text, request.filters or {}
        )
        message.total_recipients = total
        message.delivered_count = delivered
        message.failed_count = failed

    message.status = "sent"
    message.sent_at = datetime.now(timezone.utc)
    await session.commit()

    return SendMessageResponse(
        message_id=message.id,
        status="sent",
        recipients_count=message.delivered_count,
    )


async def get_message_history(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> MessageHistoryResponse:
    """Get message history with pagination."""
    query = select(ScheduledMessage).order_by(ScheduledMessage.created_at.desc())

    # Count total
    count_query = select(func.count()).select_from(ScheduledMessage)
    total = await session.scalar(count_query) or 0

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    messages = result.scalars().all()

    items = [MessageHistoryItem.model_validate(m) for m in messages]

    return MessageHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def cancel_scheduled_message(
    session: AsyncSession,
    message_id: int,
) -> bool:
    """Cancel a scheduled message (if not yet sent)."""
    message = await session.get(ScheduledMessage, message_id)
    if not message or message.status != "pending":
        return False

    message.status = "canceled"
    await session.commit()
    return True
