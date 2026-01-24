"""add_horoscope_cache_tables

Revision ID: h8c9d0e1f2g3
Revises: 4e898b8d0011
Create Date: 2026-01-23

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "h8c9d0e1f2g3"
down_revision: str | None = "4e898b8d0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create horoscope_cache and horoscope_views tables."""
    # Create horoscope_cache table (IF NOT EXISTS через raw SQL для безопасности)
    op.execute("""
        CREATE TABLE IF NOT EXISTS horoscope_cache (
            id SERIAL PRIMARY KEY,
            zodiac_sign VARCHAR(20) NOT NULL,
            horoscope_date DATE NOT NULL,
            content TEXT NOT NULL,
            generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_horoscope_cache_sign_date UNIQUE (zodiac_sign, horoscope_date)
        )
    """)

    # Create indexes (IF NOT EXISTS для идемпотентности)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_horoscope_cache_date
        ON horoscope_cache (horoscope_date)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_horoscope_cache_zodiac_sign
        ON horoscope_cache (zodiac_sign)
    """)

    # Create horoscope_views table (IF NOT EXISTS)
    op.execute("""
        CREATE TABLE IF NOT EXISTS horoscope_views (
            id SERIAL PRIMARY KEY,
            zodiac_sign VARCHAR(20) NOT NULL,
            view_date DATE NOT NULL,
            view_count INTEGER NOT NULL DEFAULT 0,
            CONSTRAINT uq_horoscope_views_sign_date UNIQUE (zodiac_sign, view_date)
        )
    """)


def downgrade() -> None:
    """Drop horoscope_views and horoscope_cache tables."""
    # Drop tables (CASCADE для удаления связанных индексов)
    op.execute("DROP TABLE IF EXISTS horoscope_views CASCADE")
    op.execute("DROP TABLE IF EXISTS horoscope_cache CASCADE")
