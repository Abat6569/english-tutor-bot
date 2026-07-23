from typing import Protocol


class LessonGenerator(Protocol):
    async def generate(self, mistake_summary: str) -> str: ...
