"""merge_heads

Revision ID: 195478ad60d2
Revises: c9d0e1f2g3h4, 12302cba8088
Create Date: 2026-02-03 14:31:26.861597

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "195478ad60d2"
down_revision: Union[str, Sequence[str], None] = ("c9d0e1f2g3h4", "12302cba8088")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
