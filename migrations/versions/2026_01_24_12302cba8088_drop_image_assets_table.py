"""drop_image_assets_table

Revision ID: 12302cba8088
Revises: bb3aea586917
Create Date: 2026-01-24 07:16:57.241456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "12302cba8088"
down_revision: Union[str, Sequence[str], None] = "bb3aea586917"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop image_assets table (no longer used)."""
    op.drop_table("image_assets")


def downgrade() -> None:
    """Recreate image_assets table for rollback."""
    op.create_table(
        "image_assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_key", sa.String(length=255), nullable=False),
        sa.Column("file_id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_key"),
    )
    op.create_index("ix_image_assets_asset_key", "image_assets", ["asset_key"])
