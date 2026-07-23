from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import ToolParam

from src.config.settings import settings
from src.core.entities.evaluation import MistakeItem, TurnEvaluation

EVALUATOR_SYSTEM_PROMPT = """You are an experienced English teacher assessing one \
spoken utterance from a student. The student is a QA/QC engineer from Uzbekistan, \
native Russian speaker, currently A2, aiming for B2/C1.

Score grammar, vocabulary, fluency and naturalness from 1 (many basic errors) to 5 \
(native-like). Judge fluency and naturalness from how the sentence reads as \
transcribed speech, not from punctuation.

Only report mistakes that are real and worth the student's attention — do not invent \
nitpicks in an already-correct short sentence. If the utterance has no meaningful \
mistakes, return an empty mistakes list and set corrected_sentence equal to (or a \
slightly more natural phrasing of) the original.

Always call the submit_evaluation tool with your assessment. Never reply in plain text."""

EVALUATION_TOOL: ToolParam = {
    "name": "submit_evaluation",
    "description": "Submit a structured evaluation of the student's spoken utterance.",
    "input_schema": {
        "type": "object",
        "properties": {
            "grammar_score": {"type": "integer", "minimum": 1, "maximum": 5},
            "vocabulary_score": {"type": "integer", "minimum": 1, "maximum": 5},
            "fluency_score": {"type": "integer", "minimum": 1, "maximum": 5},
            "naturalness_score": {"type": "integer", "minimum": 1, "maximum": 5},
            "corrected_sentence": {"type": "string"},
            "mistakes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["grammar", "vocabulary", "fluency", "naturalness"],
                        },
                        "original": {"type": "string"},
                        "corrected": {"type": "string"},
                        "explanation": {"type": "string"},
                    },
                    "required": ["category", "original", "corrected", "explanation"],
                },
            },
        },
        "required": [
            "grammar_score",
            "vocabulary_score",
            "fluency_score",
            "naturalness_score",
            "corrected_sentence",
            "mistakes",
        ],
    },
}


class ClaudeTurnEvaluator:
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def evaluate(self, user_utterance: str) -> TurnEvaluation:
        response = await self._client.messages.create(
            model=settings.anthropic_evaluation_model,
            max_tokens=500,
            system=EVALUATOR_SYSTEM_PROMPT,
            tools=[EVALUATION_TOOL],
            tool_choice={"type": "tool", "name": "submit_evaluation"},
            messages=[{"role": "user", "content": user_utterance}],
        )

        tool_input: dict[str, Any] = next(
            block.input for block in response.content if block.type == "tool_use"
        )

        return TurnEvaluation(
            grammar_score=tool_input["grammar_score"],
            vocabulary_score=tool_input["vocabulary_score"],
            fluency_score=tool_input["fluency_score"],
            naturalness_score=tool_input["naturalness_score"],
            corrected_sentence=tool_input["corrected_sentence"],
            mistakes=[MistakeItem(**item) for item in tool_input["mistakes"]],
        )
