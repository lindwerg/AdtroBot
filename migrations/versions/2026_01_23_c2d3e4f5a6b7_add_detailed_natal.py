"""add_detailed_natal

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-01-23 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add detailed natal one-time purchase tracking.

    - User.detailed_natal_purchased_at: tracks when user bought detailed natal
    - detailed_natals table: caches AI-generated interpretations
    """
    # Add detailed_natal_purchased_at to users table
    op.add_column(
        "users",
        sa.Column(
            "detailed_natal_purchased_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Create detailed_natals table for caching interpretations
    op.create_table(
        "detailed_natals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("interpretation", sa.Text(), nullable=False),
        sa.Column("telegraph_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_detailed_natals_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_detailed_natals")),
    )
    op.create_index(
        op.f("ix_detailed_natals_user_id"),
        "detailed_natals",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove detailed natal tracking."""
    op.drop_index(op.f("ix_detailed_natals_user_id"), table_name="detailed_natals")
    op.drop_table("detailed_natals")
    op.drop_column("users", "detailed_natal_purchased_at")
