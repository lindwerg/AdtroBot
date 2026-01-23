"""add_tarot_spreads_table

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-01-23 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tarot_spreads table for spread history."""
    op.create_table(
        "tarot_spreads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("spread_type", sa.String(length=20), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("cards", sa.JSON(), nullable=False),
        sa.Column("interpretation", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_tarot_spreads_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tarot_spreads")),
    )
    op.create_index(
        op.f("ix_tarot_spreads_user_id"),
        "tarot_spreads",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop tarot_spreads table."""
    op.drop_index(op.f("ix_tarot_spreads_user_id"), table_name="tarot_spreads")
    op.drop_table("tarot_spreads")
