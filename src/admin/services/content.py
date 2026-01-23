"""Content management service for admin panel."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.models import HoroscopeContent
from src.admin.schemas import (
    HoroscopeContentItem,
    HoroscopeContentListResponse,
    UpdateHoroscopeContentRequest,
)


ZODIAC_SIGNS = [
    "aries",
    "taurus",
    "gemini",
    "cancer",
    "leo",
    "virgo",
    "libra",
    "scorpio",
    "sagittarius",
    "capricorn",
    "aquarius",
    "pisces",
]

ZODIAC_LABELS = {
    "aries": "Овен",
    "taurus": "Телец",
    "gemini": "Близнецы",
    "cancer": "Рак",
    "leo": "Лев",
    "virgo": "Дева",
    "libra": "Весы",
    "scorpio": "Скорпион",
    "sagittarius": "Стрелец",
    "capricorn": "Козерог",
    "aquarius": "Водолей",
    "pisces": "Рыбы",
}


async def get_all_horoscope_content(
    session: AsyncSession,
) -> HoroscopeContentListResponse:
    """Get horoscope content for all zodiac signs."""
    query = select(HoroscopeContent).order_by(HoroscopeContent.id)
    result = await session.execute(query)
    contents = result.scalars().all()

    # Ensure all signs exist (create missing ones)
    existing_signs = {c.zodiac_sign for c in contents}
    for sign in ZODIAC_SIGNS:
        if sign not in existing_signs:
            new_content = HoroscopeContent(zodiac_sign=sign, base_text="")
            session.add(new_content)

    if len(existing_signs) < 12:
        await session.commit()
        # Re-fetch
        result = await session.execute(query)
        contents = result.scalars().all()

    items = [HoroscopeContentItem.model_validate(c) for c in contents]
    return HoroscopeContentListResponse(items=items)


async def get_horoscope_content(
    session: AsyncSession,
    zodiac_sign: str,
) -> HoroscopeContent | None:
    """Get horoscope content for specific zodiac sign."""
    query = select(HoroscopeContent).where(
        HoroscopeContent.zodiac_sign == zodiac_sign
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def update_horoscope_content(
    session: AsyncSession,
    zodiac_sign: str,
    request: UpdateHoroscopeContentRequest,
    admin_id: int,
) -> HoroscopeContent | None:
    """Update horoscope content for specific zodiac sign."""
    content = await get_horoscope_content(session, zodiac_sign)
    if not content:
        # Create if doesn't exist
        content = HoroscopeContent(zodiac_sign=zodiac_sign)
        session.add(content)

    content.base_text = request.base_text
    content.notes = request.notes
    content.updated_by = admin_id

    await session.commit()
    await session.refresh(content)
    return content
