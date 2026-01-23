"""add horoscope_content table

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-01-23

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "horoscope_content",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zodiac_sign", sa.String(length=20), nullable=False),
        sa.Column("base_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_horoscope_content")),
        sa.UniqueConstraint("zodiac_sign", name=op.f("uq_horoscope_content_zodiac_sign")),
    )
    op.create_index(
        op.f("ix_zodiac_sign"), "horoscope_content", ["zodiac_sign"], unique=False
    )

    # Seed initial data for all 12 zodiac signs
    op.execute("""
        INSERT INTO horoscope_content (zodiac_sign, base_text, updated_at)
        VALUES
            ('aries', '', NOW()),
            ('taurus', '', NOW()),
            ('gemini', '', NOW()),
            ('cancer', '', NOW()),
            ('leo', '', NOW()),
            ('virgo', '', NOW()),
            ('libra', '', NOW()),
            ('scorpio', '', NOW()),
            ('sagittarius', '', NOW()),
            ('capricorn', '', NOW()),
            ('aquarius', '', NOW()),
            ('pisces', '', NOW())
        ON CONFLICT (zodiac_sign) DO NOTHING;
    """)


def downgrade() -> None:
    op.drop_index(op.f("ix_zodiac_sign"), table_name="horoscope_content")
    op.drop_table("horoscope_content")
