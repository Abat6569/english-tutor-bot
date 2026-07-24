from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.entities.evaluation import MistakeItem
from src.infrastructure.db.models.mistake import Mistake


class MistakeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_many(self, user_id: int, mistakes: list[MistakeItem]) -> None:
        if not mistakes:
            return
        self._session.add_all(
            Mistake(
                user_id=user_id,
                category=item.category,
                original_text=item.original,
                corrected_text=item.corrected,
                explanation=item.explanation,
            )
            for item in mistakes
        )
        await self._session.commit()

    async def recent(self, user_id: int, limit: int = 20) -> list[Mistake]:
        stmt = (
            select(Mistake)
            .where(Mistake.user_id == user_id)
            .order_by(Mistake.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def category_counts(self, user_id: int, limit: int = 200) -> dict[str, int]:
        """Counts categories over the most recent `limit` mistakes (not the whole table)."""
        subq = (
            select(Mistake.category, Mistake.created_at)
            .where(Mistake.user_id == user_id)
            .order_by(Mistake.created_at.desc())
            .limit(limit)
            .subquery()
        )
        stmt = select(subq.c.category, func.count()).group_by(subq.c.category)
        result = await self._session.execute(stmt)
        return dict(result.tuples().all())

    async def count_since(self, user_id: int, since: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(Mistake)
            .where(Mistake.user_id == user_id, Mistake.created_at >= since)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
