"""add_birth_location_fields

Revision ID: a1b2c3d4e5f6
Revises: c6bc722b76ba
Create Date: 2026-01-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "c6bc722b76ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add birth location fields for natal chart (premium feature)
    op.add_column("users", sa.Column("birth_time", sa.Time(), nullable=True))
    op.add_column("users", sa.Column("birth_city", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("birth_lat", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("birth_lon", sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "birth_lon")
    op.drop_column("users", "birth_lat")
    op.drop_column("users", "birth_city")
    op.drop_column("users", "birth_time")
