from anthropic import AsyncAnthropic

from src.config.settings import settings

LESSON_SYSTEM_PROMPT = """You are an English teacher preparing the opening of today's \
spoken practice session for a QA/QC engineer from Uzbekistan (native Russian, A2 \
heading to B2/C1).

You will be given a short summary of mistakes they made recently. Write a short, warm, \
spoken opening (3-5 sentences) for today's session: briefly and kindly mention 1-2 \
patterns you noticed (without listing every mistake), then ask an engaging opening \
question to start conversation practice — ideally one that will naturally invite the \
grammar or vocabulary they need to practice.

Never use markdown or bullet points — this is spoken aloud by a text-to-speech engine. \
If there is no mistake history, just give a friendly, varied opening question about \
their life or work instead."""


class ClaudeLessonGenerator:
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate(self, mistake_summary: str) -> str:
        response = await self._client.messages.create(
            model=settings.anthropic_conversation_model,
            max_tokens=300,
            system=LESSON_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": mistake_summary or "No recent mistake history."}],
        )
        return "".join(block.text for block in response.content if block.type == "text").strip()
