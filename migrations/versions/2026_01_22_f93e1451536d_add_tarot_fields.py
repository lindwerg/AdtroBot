"""Add tarot fields.

Revision ID: f93e1451536d
Revises: 5d5aadbabd72
Create Date: 2026-01-22
"""

from alembic import op
import sqlalchemy as sa


revision = "f93e1451536d"
down_revision = "5d5aadbabd72"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Card of the day cache
    op.add_column(
        "users",
        sa.Column("card_of_day_id", sa.String(20), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("card_of_day_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("card_of_day_reversed", sa.Boolean(), nullable=True),
    )
    # Daily spread limits
    op.add_column(
        "users",
        sa.Column("tarot_spread_count", sa.SmallInteger(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("spread_reset_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "spread_reset_date")
    op.drop_column("users", "tarot_spread_count")
    op.drop_column("users", "card_of_day_reversed")
    op.drop_column("users", "card_of_day_date")
    op.drop_column("users", "card_of_day_id")
