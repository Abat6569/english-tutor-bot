from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.models.achievement import Achievement


class AchievementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def unlock(self, user_id: int, code: str) -> bool:
        """Returns True if this achievement was newly unlocked, False if already had it."""
        stmt = select(Achievement).where(Achievement.user_id == user_id, Achievement.code == code)
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            return False

        self._session.add(Achievement(user_id=user_id, code=code))
        await self._session.commit()
        return True

    async def count(self, user_id: int) -> int:
        stmt = select(func.count()).select_from(Achievement).where(Achievement.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one()
