"""create vocabulary table

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vocabulary",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id", sa.BigInteger(), sa.ForeignKey("users.telegram_id"), nullable=False
        ),
        sa.Column("word_or_phrase", sa.String(length=255), nullable=False),
        sa.Column("translation_ru", sa.String(length=255), nullable=False),
        sa.Column("example_sentence", sa.Text(), nullable=False),
        sa.Column("times_seen", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_vocabulary_user_id_created_at", "vocabulary", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_vocabulary_user_id_created_at", table_name="vocabulary")
    op.drop_table("vocabulary")
