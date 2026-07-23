import structlog
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from src.infrastructure.db.repositories.user_repository import UserRepository
from src.infrastructure.db.session import get_session
from src.infrastructure.external.audio_convert import mp3_to_ogg_opus
from src.infrastructure.tts.edge_tts_adapter import EdgeTTS
from src.services.learning.professional_topics import random_scenario

router = Router(name="modes")
log = structlog.get_logger()

_tts = EdgeTTS()


@router.message(Command("professional"))
async def cmd_professional(message: Message) -> None:
    assert message.from_user is not None
    assert message.bot is not None

    scenario = random_scenario()

    async with get_session() as session:
        await UserRepository(session).update_settings(
            message.from_user.id,
            mode="professional",
            professional_persona=scenario.persona,
            professional_persona_description=scenario.persona_description,
            professional_topic=scenario.topic,
        )

    intro_text = (
        f"Switching to professional practice. I'll play the role of {scenario.persona}. "
        f"Today's scenario: {scenario.topic}. Go ahead, start the conversation whenever "
        "you're ready."
    )

    await message.bot.send_chat_action(message.chat.id, "record_voice")
    audio = await _tts.synthesize(intro_text)
    ogg_bytes = await mp3_to_ogg_opus(audio)
    await message.answer_voice(BufferedInputFile(ogg_bytes, filename="intro.ogg"))


@router.message(Command("speaking"))
async def cmd_speaking(message: Message) -> None:
    assert message.from_user is not None

    async with get_session() as session:
        await UserRepository(session).update_settings(message.from_user.id, mode="general")

    await message.answer("Back to free conversation practice. Send me a voice message any time.")
