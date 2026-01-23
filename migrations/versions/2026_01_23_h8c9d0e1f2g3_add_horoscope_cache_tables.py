"""add_horoscope_cache_tables

Revision ID: h8c9d0e1f2g3
Revises: g7b8c9d0e1f2
Create Date: 2026-01-23

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "h8c9d0e1f2g3"
down_revision: str | None = "g7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create horoscope_cache and horoscope_views tables."""
    # Create horoscope_cache table
    op.create_table(
        "horoscope_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zodiac_sign", sa.String(length=20), nullable=False),
        sa.Column("horoscope_date", sa.Date(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_horoscope_cache")),
        sa.UniqueConstraint(
            "zodiac_sign", "horoscope_date", name="uq_horoscope_cache_sign_date"
        ),
    )
    op.create_index(
        "ix_horoscope_cache_date",
        "horoscope_cache",
        ["horoscope_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_zodiac_sign"),
        "horoscope_cache",
        ["zodiac_sign"],
        unique=False,
    )

    # Create horoscope_views table
    op.create_table(
        "horoscope_views",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zodiac_sign", sa.String(length=20), nullable=False),
        sa.Column("view_date", sa.Date(), nullable=False),
        sa.Column("view_count", sa.Integer(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_horoscope_views")),
        sa.UniqueConstraint(
            "zodiac_sign", "view_date", name="uq_horoscope_views_sign_date"
        ),
    )


def downgrade() -> None:
    """Drop horoscope_views and horoscope_cache tables."""
    op.drop_table("horoscope_views")
    op.drop_index(op.f("ix_zodiac_sign"), table_name="horoscope_cache")
    op.drop_index("ix_horoscope_cache_date", table_name="horoscope_cache")
    op.drop_table("horoscope_cache")
