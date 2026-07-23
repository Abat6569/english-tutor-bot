import base64
from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import ToolParam

from src.config.settings import settings
from src.core.entities.translation import TranslationResult, WordNote

TRANSLATOR_SYSTEM_PROMPT = """You are a professional translator working between \
Russian, English, Chinese (Mandarin), and Uzbek for a QA/QC engineer whose native \
language is Russian and who is learning English (A2 heading to B2/C1).

Detect the language of the given text among Russian, English, Chinese, or Uzbek. \
Translation direction: if the input is English, translate it to Russian (so the \
student can understand it). If the input is Russian, Chinese, or Uzbek, translate it \
to English (since the student is usually trying to communicate in English).

Give a natural, idiomatic translation. If a more literal, word-for-word translation \
would help the student understand the sentence structure and it differs meaningfully \
from the natural one, include it too — otherwise repeat the natural translation there. \
Note up to 2 words or idioms genuinely worth explaining (skip this for simple text).

Always call the submit_translation tool. Never reply in plain text."""

TRANSLATION_TOOL: ToolParam = {
    "name": "submit_translation",
    "description": "Submit a structured translation.",
    "input_schema": {
        "type": "object",
        "properties": {
            "source_language": {"type": "string", "enum": ["ru", "en", "zh", "uz", "other"]},
            "target_language": {"type": "string", "enum": ["ru", "en", "zh", "uz"]},
            "natural_translation": {"type": "string"},
            "literal_translation": {"type": "string"},
            "word_notes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "word": {"type": "string"},
                        "explanation": {"type": "string"},
                    },
                    "required": ["word", "explanation"],
                },
            },
        },
        "required": [
            "source_language",
            "target_language",
            "natural_translation",
            "literal_translation",
            "word_notes",
        ],
    },
}


class ClaudeTranslator:
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def translate_text(self, text: str) -> TranslationResult:
        return await self._call(content=[{"type": "text", "text": text}])

    async def translate_image(self, image_bytes: bytes, media_type: str) -> TranslationResult:
        encoded = base64.b64encode(image_bytes).decode("ascii")
        return await self._call(
            content=[
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": encoded},
                },
                {"type": "text", "text": "Translate the text visible in this image."},
            ]
        )

    async def _call(self, content: list[dict[str, Any]]) -> TranslationResult:
        response = await self._client.messages.create(  # type: ignore[call-overload]
            model=settings.anthropic_conversation_model,
            max_tokens=500,
            system=TRANSLATOR_SYSTEM_PROMPT,
            tools=[TRANSLATION_TOOL],
            tool_choice={"type": "tool", "name": "submit_translation"},
            messages=[{"role": "user", "content": content}],
        )

        tool_input: dict[str, Any] = next(
            block.input for block in response.content if block.type == "tool_use"
        )

        return TranslationResult(
            source_language=tool_input["source_language"],
            target_language=tool_input["target_language"],
            natural_translation=tool_input["natural_translation"],
            literal_translation=tool_input["literal_translation"],
            word_notes=[WordNote(**item) for item in tool_input["word_notes"]],
        )
