"""Add user notification fields.

Revision ID: 5d5aadbabd72
Revises: d3fd5383e8ea
Create Date: 2026-01-22
"""

from alembic import op
import sqlalchemy as sa


revision = "5d5aadbabd72"
down_revision = "d3fd5383e8ea"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("timezone", sa.String(50), nullable=True, server_default="Europe/Moscow"),
    )
    op.add_column(
        "users",
        sa.Column("notification_hour", sa.SmallInteger(), nullable=True, server_default="9"),
    )
    op.add_column(
        "users",
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("users", "notifications_enabled")
    op.drop_column("users", "notification_hour")
    op.drop_column("users", "timezone")
