import structlog
from aiogram import F, Router
from aiogram.types import BufferedInputFile, Message

from src.core.use_cases.run_speaking_turn import RunSpeakingTurn
from src.infrastructure.db.repositories.message_repository import MessageRepository
from src.infrastructure.db.repositories.user_repository import UserRepository
from src.infrastructure.db.session import get_session
from src.infrastructure.external.audio_convert import mp3_to_ogg_opus
from src.infrastructure.stt.groq_stt import GroqSTT
from src.infrastructure.tts.edge_tts_adapter import EdgeTTS
from src.services.ai.claude_client import ClaudeConversationProvider

router = Router(name="voice")
log = structlog.get_logger()

_stt = GroqSTT()
_tts = EdgeTTS()
_llm = ClaudeConversationProvider()


@router.message(F.voice)
async def handle_voice(message: Message) -> None:
    assert message.from_user is not None
    assert message.voice is not None
    assert message.bot is not None

    await message.bot.send_chat_action(message.chat.id, "record_voice")

    file = await message.bot.get_file(message.voice.file_id)
    assert file.file_path is not None
    buffer = await message.bot.download_file(file.file_path)
    assert buffer is not None
    audio_bytes = buffer.read()

    async with get_session() as session:
        await UserRepository(session).get_or_create(
            message.from_user.id, message.from_user.username
        )
        use_case = RunSpeakingTurn(
            stt=_stt,
            llm=_llm,
            tts=_tts,
            messages=MessageRepository(session),
        )
        try:
            result = await use_case.execute(message.from_user.id, audio_bytes, "voice.ogg")
        except Exception:
            log.exception("speaking_turn_failed", user_id=message.from_user.id)
            await message.answer("Sorry, something went wrong on my end. Try again?")
            return

    log.info(
        "speaking_turn_ok",
        user_id=message.from_user.id,
        heard=result.transcribed_text,
        replied=result.reply_text,
    )

    ogg_bytes = await mp3_to_ogg_opus(result.reply_audio)
    await message.answer_voice(BufferedInputFile(ogg_bytes, filename="reply.ogg"))
