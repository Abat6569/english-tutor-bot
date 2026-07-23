from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.models.base import Base


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    native_language: Mapped[str] = mapped_column(String(16), default="ru")
    current_level: Mapped[str] = mapped_column(String(8), default="A2")
    target_level: Mapped[str] = mapped_column(String(8), default="B2")
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Tashkent")
    settings_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
