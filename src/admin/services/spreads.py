"""Tarot spreads viewing service for admin panel."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.schemas import (
    CardPosition,
    TarotSpreadDetail,
    TarotSpreadListItem,
    TarotSpreadListResponse,
)
from src.bot.utils.tarot_cards import get_card_by_id
from src.bot.utils.tarot_formatting import CELTIC_CROSS_POSITIONS, SPREAD_POSITIONS
from src.db.models.tarot_spread import TarotSpread
from src.db.models.user import User


async def get_spreads(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    user_id: int | None = None,
    search: str | None = None,
    spread_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> TarotSpreadListResponse:
    """Get tarot spreads with filters and pagination."""
    # Base query with user join
    query = (
        select(TarotSpread, User.telegram_id, User.username)
        .join(User, TarotSpread.user_id == User.id)
        .order_by(TarotSpread.created_at.desc())
    )

    # Apply filters
    if user_id:
        query = query.where(TarotSpread.user_id == user_id)

    if spread_type:
        query = query.where(TarotSpread.spread_type == spread_type)

    if search:
        # Search in question text
        query = query.where(TarotSpread.question.ilike(f"%{search}%"))

    if date_from:
        query = query.where(TarotSpread.created_at >= date_from)

    if date_to:
        query = query.where(TarotSpread.created_at <= date_to)

    # Build count query with same filters
    count_query = select(func.count(TarotSpread.id)).join(
        User, TarotSpread.user_id == User.id
    )

    if user_id:
        count_query = count_query.where(TarotSpread.user_id == user_id)
    if spread_type:
        count_query = count_query.where(TarotSpread.spread_type == spread_type)
    if search:
        count_query = count_query.where(TarotSpread.question.ilike(f"%{search}%"))
    if date_from:
        count_query = count_query.where(TarotSpread.created_at >= date_from)
    if date_to:
        count_query = count_query.where(TarotSpread.created_at <= date_to)

    total = await session.scalar(count_query) or 0

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    rows = result.all()

    items = [
        TarotSpreadListItem(
            id=spread.id,
            user_id=spread.user_id,
            telegram_id=telegram_id,
            username=username,
            spread_type=spread.spread_type,
            question=spread.question,
            created_at=spread.created_at,
        )
        for spread, telegram_id, username in rows
    ]

    return TarotSpreadListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_spread_detail(
    session: AsyncSession,
    spread_id: int,
) -> TarotSpreadDetail | None:
    """Get detailed spread info including cards and interpretation."""
    # Get spread
    query = select(TarotSpread).where(TarotSpread.id == spread_id)
    result = await session.execute(query)
    spread = result.scalar_one_or_none()

    if not spread:
        return None

    # Get user info
    user = await session.get(User, spread.user_id)

    # Determine position names based on spread type
    if spread.spread_type == "celtic_cross":
        position_names = CELTIC_CROSS_POSITIONS
    else:
        position_names = SPREAD_POSITIONS

    # Map cards JSON to CardPosition objects
    cards: list[CardPosition] = []
    for i, card_info in enumerate(spread.cards):
        card_id = card_info.get("card_id")
        is_reversed = card_info.get("reversed", False)
        position_idx = card_info.get("position", i + 1)

        # Get card name from deck
        card = get_card_by_id(card_id)
        card_name = card["name"] if card else f"Unknown ({card_id})"

        # Get position name
        pos_idx = position_idx - 1 if position_idx > 0 else i
        position_name = (
            position_names[pos_idx]
            if pos_idx < len(position_names)
            else f"Position {position_idx}"
        )

        cards.append(
            CardPosition(
                position=position_idx,
                position_name=position_name,
                card_name=card_name,
                is_reversed=is_reversed,
            )
        )

    # Sort by position
    cards.sort(key=lambda c: c.position)

    return TarotSpreadDetail(
        id=spread.id,
        user_id=spread.user_id,
        telegram_id=user.telegram_id if user else None,
        username=user.username if user else None,
        spread_type=spread.spread_type,
        question=spread.question,
        cards=cards,
        interpretation=spread.interpretation,
        created_at=spread.created_at,
    )
