"""add_image_assets_table

Revision ID: 4c005bb76409
Revises: h8c9d0e1f2g3
Create Date: 2026-01-24 03:02:27.976316

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4c005bb76409"
down_revision: Union[str, Sequence[str], None] = "h8c9d0e1f2g3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create image_assets table for Telegram file_id caching."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS image_assets (
            id SERIAL PRIMARY KEY,
            asset_key VARCHAR(255) NOT NULL UNIQUE,
            file_id VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_image_assets_asset_key
        ON image_assets (asset_key)
    """)


def downgrade() -> None:
    """Drop image_assets table."""
    op.execute("DROP TABLE IF EXISTS image_assets CASCADE")
