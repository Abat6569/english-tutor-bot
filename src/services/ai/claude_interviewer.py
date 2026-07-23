from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import ToolParam

from src.config.settings import settings
from src.core.entities.interview import InterviewFeedback

INTERVIEWER_SYSTEM_PROMPT_TEMPLATE = """You are an experienced interviewer conducting a \
mock {interview_type} interview with a QA/QC engineer from Uzbekistan (native Russian, \
A2 heading toward B2/C1) preparing for international job interviews.

You will be given the question you asked and the candidate's transcribed spoken answer. \
Judge whether it is a genuinely good, natural, complete spoken answer for someone at \
their level — not perfect native English, but clear, relevant, and it covers the \
question. A short but complete and relevant answer with minor grammar slips can still \
pass.

If it passes: give brief, genuine spoken praise (1-2 sentences), optionally note one \
thing worth polishing next time, without dwelling on it.

If it does not pass: kindly explain what's missing or wrong (too short, off-topic, \
unclear, or major grammar errors that obscure meaning), then MODEL a better answer \
example (short, realistic, at their level) they could adapt, and ask them to try \
answering the same question again.

Never use markdown, bullet points, or emoji — this is spoken aloud. Always call the \
submit_interview_feedback tool, never reply in plain text."""

INTERVIEW_FEEDBACK_TOOL: ToolParam = {
    "name": "submit_interview_feedback",
    "description": "Submit feedback on the candidate's interview answer.",
    "input_schema": {
        "type": "object",
        "properties": {
            "passes": {"type": "boolean"},
            "score": {"type": "integer", "minimum": 1, "maximum": 5},
            "spoken_response": {"type": "string"},
        },
        "required": ["passes", "score", "spoken_response"],
    },
}


class ClaudeInterviewCoach:
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def evaluate_answer(
        self, question: str, answer: str, interview_type: str
    ) -> InterviewFeedback:
        system_prompt = INTERVIEWER_SYSTEM_PROMPT_TEMPLATE.format(interview_type=interview_type)
        user_content = f'Question: "{question}"\nCandidate\'s answer: "{answer}"'

        response = await self._client.messages.create(
            model=settings.anthropic_evaluation_model,
            max_tokens=800,
            system=system_prompt,
            tools=[INTERVIEW_FEEDBACK_TOOL],
            tool_choice={"type": "tool", "name": "submit_interview_feedback"},
            messages=[{"role": "user", "content": user_content}],
        )

        tool_input: dict[str, Any] = next(
            block.input for block in response.content if block.type == "tool_use"
        )

        return InterviewFeedback(
            passes=tool_input.get("passes", False),
            score=tool_input.get("score", 3),
            spoken_response=tool_input.get("spoken_response", "Sorry, could you say that again?"),
        )
