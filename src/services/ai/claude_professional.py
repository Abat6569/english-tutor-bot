from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from src.config.settings import settings
from src.core.entities.conversation import ConversationTurn

SYSTEM_PROMPT_TEMPLATE = """You are role-playing as {persona} ({persona_description}) \
in a QA/QC conversation with a Russian-native QA/QC engineer (Electrical/Mechanical/\
Civil background, A2 heading toward B2/C1, works on solar, wind, BESS and oil & gas \
projects) who is practicing professional English.

Today's scenario: {topic}.

Stay in character. Use realistic QA/QC terminology (ITP, NCR, RFI, punch list, method \
statement, as-built, IEC/IEEE/ISO/ASTM/ASME/NFPA references, SAT/FAT, commissioning) \
naturally, but keep sentences short enough to say aloud and to understand at their \
level — a notch above what they say, not miles above.

If they make a mistake, weave a light correction into your in-character reply rather \
than breaking character to lecture. Keep the scenario moving with realistic follow-up \
questions or pushback, the way a real site conversation would. Never use markdown, \
bullet points, or emoji — this is spoken aloud."""


class ClaudeProfessionalProvider:
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def reply(
        self,
        history: list[ConversationTurn],
        user_message: str,
        *,
        persona: str,
        persona_description: str,
        topic: str,
    ) -> str:
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            persona=persona, persona_description=persona_description, topic=topic
        )
        messages: list[MessageParam] = [
            {"role": turn.role, "content": turn.content} for turn in history
        ]
        messages.append({"role": "user", "content": user_message})

        response = await self._client.messages.create(
            model=settings.anthropic_conversation_model,
            max_tokens=400,
            system=system_prompt,
            messages=messages,
        )
        return "".join(block.text for block in response.content if block.type == "text").strip()
