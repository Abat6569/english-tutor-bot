from src.core.entities.evaluation import TurnEvaluation
from src.core.interfaces.evaluator import TurnEvaluator
from src.infrastructure.db.repositories.mistake_repository import MistakeRepository


class EvaluateSpeakingTurn:
    def __init__(self, evaluator: TurnEvaluator, mistakes: MistakeRepository) -> None:
        self._evaluator = evaluator
        self._mistakes = mistakes

    async def execute(self, user_id: int, user_utterance: str) -> TurnEvaluation:
        evaluation = await self._evaluator.evaluate(user_utterance)
        await self._mistakes.add_many(user_id, evaluation.mistakes)
        return evaluation
