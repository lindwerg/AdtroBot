"""merge heads for global_discounts

Revision ID: ca7893bddd5e
Revises: 2f1e29535c6c, g1d2s3c4o5u6
Create Date: 2026-02-05 23:01:57.696845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ca7893bddd5e"
down_revision: Union[str, Sequence[str], None] = ("2f1e29535c6c", "g1d2s3c4o5u6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
