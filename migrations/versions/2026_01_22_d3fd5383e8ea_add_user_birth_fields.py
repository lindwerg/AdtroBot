"""add user birth fields

Revision ID: d3fd5383e8ea
Revises: 3cd28dafcf62
Create Date: 2026-01-22 20:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d3fd5383e8ea"
down_revision: Union[str, Sequence[str], None] = "3cd28dafcf62"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add birth_date and zodiac_sign columns to users table."""
    op.add_column("users", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("zodiac_sign", sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Remove birth_date and zodiac_sign columns from users table."""
    op.drop_column("users", "zodiac_sign")
    op.drop_column("users", "birth_date")
