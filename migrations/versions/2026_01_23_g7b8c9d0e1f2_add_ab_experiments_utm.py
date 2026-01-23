"""add ab_experiments and utm tracking

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-01-23

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "g7b8c9d0e1f2"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create ab_experiments table
    op.create_table(
        "ab_experiments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metric", sa.String(length=50), nullable=False),
        sa.Column("variant_b_percent", sa.SmallInteger(), nullable=False, server_default="50"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ab_experiments")),
    )

    # Create ab_assignments table
    op.create_table(
        "ab_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("experiment_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("variant", sa.String(length=1), nullable=False),
        sa.Column("converted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["experiment_id"],
            ["ab_experiments.id"],
            name=op.f("fk_ab_assignments_experiment_id_ab_experiments"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_ab_assignments_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ab_assignments")),
        sa.UniqueConstraint(
            "experiment_id", "user_id", name="uq_ab_assignment_user_experiment"
        ),
    )
    op.create_index(
        op.f("ix_ab_assignments_experiment_id"),
        "ab_assignments",
        ["experiment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ab_assignments_user_id"),
        "ab_assignments",
        ["user_id"],
        unique=False,
    )

    # Add UTM fields to users table
    op.add_column(
        "users",
        sa.Column("utm_source", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("utm_medium", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("utm_campaign", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    # Remove UTM fields from users
    op.drop_column("users", "utm_campaign")
    op.drop_column("users", "utm_medium")
    op.drop_column("users", "utm_source")

    # Drop ab_assignments table
    op.drop_index(op.f("ix_ab_assignments_user_id"), table_name="ab_assignments")
    op.drop_index(op.f("ix_ab_assignments_experiment_id"), table_name="ab_assignments")
    op.drop_table("ab_assignments")

    # Drop ab_experiments table
    op.drop_table("ab_experiments")
