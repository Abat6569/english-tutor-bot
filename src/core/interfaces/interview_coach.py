from typing import Protocol

from src.core.entities.interview import InterviewFeedback


class InterviewCoach(Protocol):
    async def evaluate_answer(
        self, question: str, answer: str, interview_type: str
    ) -> InterviewFeedback: ...
