from typing import Protocol

from src.core.entities.evaluation import TurnEvaluation


class TurnEvaluator(Protocol):
    async def evaluate(self, user_utterance: str) -> TurnEvaluation: ...
