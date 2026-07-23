from src.core.entities.evaluation import TurnEvaluation
from src.core.interfaces.evaluator import TurnEvaluator
from src.infrastructure.db.repositories.mistake_repository import MistakeRepository
from src.infrastructure.db.repositories.vocabulary_repository import VocabularyRepository


class EvaluateSpeakingTurn:
    def __init__(
        self,
        evaluator: TurnEvaluator,
        mistakes: MistakeRepository,
        vocabulary: VocabularyRepository,
    ) -> None:
        self._evaluator = evaluator
        self._mistakes = mistakes
        self._vocabulary = vocabulary

    async def execute(self, user_id: int, user_utterance: str) -> TurnEvaluation:
        evaluation = await self._evaluator.evaluate(user_utterance)
        await self._mistakes.add_many(user_id, evaluation.mistakes)
        await self._vocabulary.add_many(user_id, evaluation.vocabulary_notes)
        return evaluation
