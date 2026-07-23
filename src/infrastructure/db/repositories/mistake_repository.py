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
