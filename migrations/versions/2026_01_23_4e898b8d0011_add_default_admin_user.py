"""add default admin user

Revision ID: 4e898b8d0011
Revises: g7b8c9d0e1f2
Create Date: 2026-01-23 11:58:29.322697

"""
from typing import Sequence, Union

from alembic import op
import bcrypt


# revision identifiers, used by Alembic.
revision: str = "4e898b8d0011"
down_revision: Union[str, Sequence[str], None] = "g7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create default admin user."""
    # Hash password: admin123
    hashed = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Insert admin user
    op.execute(
        f"""
        INSERT INTO admins (username, hashed_password, is_active, created_at)
        VALUES ('admin', '{hashed}', true, NOW())
        ON CONFLICT (username) DO NOTHING
        """
    )


def downgrade() -> None:
    """Remove default admin user."""
    op.execute("DELETE FROM admins WHERE username = 'admin'")
