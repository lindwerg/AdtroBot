"""add_premium_horoscope_cache

Revision ID: p9r2e3m4i5u6
Revises: 195478ad60d2
Create Date: 2026-02-03

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "p9r2e3m4i5u6"
down_revision: str | None = "195478ad60d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create premium_horoscope_cache table."""
    # Create premium_horoscope_cache table (IF NOT EXISTS для безопасности)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS premium_horoscope_cache (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            horoscope_date DATE NOT NULL,
            content TEXT NOT NULL,
            generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_premium_horoscope_cache_user_date UNIQUE (user_id, horoscope_date)
        )
    """
    )

    # Create indexes (IF NOT EXISTS для идемпотентности)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_premium_horoscope_cache_user_id
        ON premium_horoscope_cache (user_id)
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_premium_horoscope_cache_horoscope_date
        ON premium_horoscope_cache (horoscope_date)
    """
    )


def downgrade() -> None:
    """Drop premium_horoscope_cache table."""
    # Drop table (CASCADE для удаления связанных индексов)
    op.execute("DROP TABLE IF EXISTS premium_horoscope_cache CASCADE")
