"""add global_discounts table

Revision ID: g1d2s3c4o5u6
Revises: p9r2e3m4i5u6
Create Date: 2026-02-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "g1d2s3c4o5u6"
down_revision: str | None = "p9r2e3m4i5u6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create global_discounts table."""
    op.create_table(
        "global_discounts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("target_plan", sa.String(20), nullable=False),
        sa.Column("discount_percent", sa.SmallInteger, nullable=False),
        sa.Column(
            "active_from",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("active_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Drop global_discounts table."""
    op.drop_table("global_discounts")
