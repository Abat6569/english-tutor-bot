"""add gamification: xp/streak on users, achievements table

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("xp", sa.Integer(), nullable=False, server_default="0"))
    op.add_column(
        "users", sa.Column("streak_days", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column("users", sa.Column("last_activity_date", sa.Date(), nullable=True))

    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id", sa.BigInteger(), sa.ForeignKey("users.telegram_id"), nullable=False
        ),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column(
            "unlocked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_unique_constraint("uq_achievements_user_code", "achievements", ["user_id", "code"])


def downgrade() -> None:
    op.drop_constraint("uq_achievements_user_code", "achievements", type_="unique")
    op.drop_table("achievements")
    op.drop_column("users", "last_activity_date")
    op.drop_column("users", "streak_days")
    op.drop_column("users", "xp")
