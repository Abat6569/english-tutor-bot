from src.core.interfaces.lesson_generator import LessonGenerator
from src.infrastructure.db.repositories.mistake_repository import MistakeRepository


class GenerateDailyLesson:
    def __init__(self, mistakes: MistakeRepository, generator: LessonGenerator) -> None:
        self._mistakes = mistakes
        self._generator = generator

    async def execute(self, user_id: int) -> str:
        recent = await self._mistakes.recent(user_id, limit=15)

        if not recent:
            summary = ""
        else:
            lines = [
                f'- ({m.category}) "{m.original_text}" -> "{m.corrected_text}": {m.explanation}'
                for m in recent
            ]
            summary = "Recent mistakes:\n" + "\n".join(lines)

        return await self._generator.generate(summary)
