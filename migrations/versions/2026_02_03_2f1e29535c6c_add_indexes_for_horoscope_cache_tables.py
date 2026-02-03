"""add_indexes_for_horoscope_cache_tables

Revision ID: 2f1e29535c6c
Revises: p9r2e3m4i5u6
Create Date: 2026-02-03 21:52:25.378410

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2f1e29535c6c"
down_revision: Union[str, Sequence[str], None] = "p9r2e3m4i5u6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes for horoscope cache tables to improve query performance."""
    # Index for HoroscopeCache queries (zodiac_sign + horoscope_date)
    op.create_index(
        "idx_horoscope_cache_sign_date",
        "horoscope_cache",
        ["zodiac_sign", "horoscope_date"],
        unique=True,
    )

    # Index for PremiumHoroscopeCache queries (user_id + horoscope_date)
    op.create_index(
        "idx_premium_cache_user_date",
        "premium_horoscope_cache",
        ["user_id", "horoscope_date"],
        unique=True,
    )


def downgrade() -> None:
    """Remove indexes for horoscope cache tables."""
    op.drop_index("idx_premium_cache_user_date", "premium_horoscope_cache")
    op.drop_index("idx_horoscope_cache_sign_date", "horoscope_cache")
