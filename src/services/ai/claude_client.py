from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from src.config.settings import settings
from src.core.entities.conversation import ConversationTurn

SYSTEM_PROMPT = """You are a warm, encouraging English speaking coach and conversation \
partner for a QA/QC engineer from Uzbekistan whose native language is Russian. Their \
current level is A2 and the goal is B2/C1.

Your job in this conversation mode:
- Talk naturally, like a real person on a voice call, not a lecture. Keep replies short \
(1-4 sentences) and easy to say out loud.
- Match your vocabulary and grammar slightly above the student's current level, so \
they are stretched but not lost.
- If the student makes a mistake, don't stop the conversation for a grammar lecture. \
Weave a light, natural correction into your reply (for example, restate the sentence \
correctly in passing), then keep the conversation moving with a genuine follow-up \
question.
- Ask about their life, work (QA/QC in solar, wind, BESS, oil & gas, electrical/\
mechanical/civil inspection, construction, commissioning), travel, or daily life. Keep \
topics varied — don't reuse the same questions.
- Never use markdown, bullet points, or emoji — this text is spoken aloud by a \
text-to-speech engine.
"""


class ClaudeConversationProvider:
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def reply(self, history: list[ConversationTurn], user_message: str) -> str:
        messages: list[MessageParam] = [
            {"role": turn.role, "content": turn.content} for turn in history
        ]
        messages.append({"role": "user", "content": user_message})

        response = await self._client.messages.create(
            model=settings.anthropic_conversation_model,
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        return "".join(block.text for block in response.content if block.type == "text").strip()
