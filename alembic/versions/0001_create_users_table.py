"""create users table

Revision ID: 0001
Revises:
Create Date: 2026-07-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("telegram_id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("native_language", sa.String(length=16), nullable=False, server_default="ru"),
        sa.Column("current_level", sa.String(length=8), nullable=False, server_default="A2"),
        sa.Column("target_level", sa.String(length=8), nullable=False, server_default="B2"),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Asia/Tashkent"),
        sa.Column("settings_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("users")
