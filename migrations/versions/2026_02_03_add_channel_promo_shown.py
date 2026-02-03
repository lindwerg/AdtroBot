"""add_channel_promo_shown

Revision ID: c9d0e1f2g3h4
Revises: bb3aea586917
Create Date: 2026-02-03 14:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9d0e1f2g3h4"
down_revision: Union[str, Sequence[str], None] = "bb3aea586917"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add channel_promo_shown field to users table
    op.add_column(
        "users",
        sa.Column(
            "channel_promo_shown",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove channel_promo_shown field from users table
    op.drop_column("users", "channel_promo_shown")
