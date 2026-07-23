from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.entities.evaluation import VocabularyNote
from src.infrastructure.db.models.vocabulary import VocabularyItem


class VocabularyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_many(self, user_id: int, notes: list[VocabularyNote]) -> None:
        for note in notes:
            stmt = select(VocabularyItem).where(
                VocabularyItem.user_id == user_id,
                func.lower(VocabularyItem.word_or_phrase) == note.word_or_phrase.lower(),
            )
            existing = (await self._session.execute(stmt)).scalar_one_or_none()
            if existing is not None:
                existing.times_seen += 1
            else:
                self._session.add(
                    VocabularyItem(
                        user_id=user_id,
                        word_or_phrase=note.word_or_phrase,
                        translation_ru=note.translation_ru,
                        example_sentence=note.example_sentence,
                    )
                )
        if notes:
            await self._session.commit()

    async def recent(self, user_id: int, limit: int = 20) -> list[VocabularyItem]:
        stmt = (
            select(VocabularyItem)
            .where(VocabularyItem.user_id == user_id)
            .order_by(VocabularyItem.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
