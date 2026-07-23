from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.models.translation import Translation


class TranslationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        user_id: int,
        source_language: str,
        target_language: str,
        source_text: str,
        translated_text: str,
    ) -> None:
        self._session.add(
            Translation(
                user_id=user_id,
                source_language=source_language,
                target_language=target_language,
                source_text=source_text,
                translated_text=translated_text,
            )
        )
        await self._session.commit()
