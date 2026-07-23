from html import escape

import structlog
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from src.core.entities.translation import TranslationResult
from src.infrastructure.db.models.user import User
from src.infrastructure.db.repositories.translation_repository import TranslationRepository
from src.infrastructure.db.repositories.user_repository import UserRepository
from src.infrastructure.db.session import get_session
from src.infrastructure.external.audio_convert import mp3_to_ogg_opus
from src.infrastructure.stt.groq_stt import GroqSTT
from src.infrastructure.tts.edge_tts_adapter import EdgeTTS
from src.services.translator.claude_translator import ClaudeTranslator

router = Router(name="translator")
log = structlog.get_logger()

_stt = GroqSTT()
_tts = EdgeTTS()
_translator = ClaudeTranslator()


@router.message(Command("translator"))
async def cmd_translator(message: Message) -> None:
    assert message.from_user is not None

    async with get_session() as session:
        await UserRepository(session).update_settings(message.from_user.id, mode="translator")

    await message.answer(
        "Translator mode on — Russian/English/Chinese/Uzbek. Send me text, a voice "
        "message, or a photo with text and I'll translate it. Send /speaking to go back "
        "to conversation practice."
    )


def _format_result(result: TranslationResult) -> str:
    lines = [
        f"<b>{result.source_language.upper()} → {result.target_language.upper()}</b>",
        "",
        escape(result.natural_translation),
    ]
    if result.literal_translation.strip().lower() != result.natural_translation.strip().lower():
        lines += ["", f"<i>Literal: {escape(result.literal_translation)}</i>"]
    if result.word_notes:
        lines.append("")
        for note in result.word_notes:
            lines.append(f"<b>{escape(note.word)}</b> — {escape(note.explanation)}")
    return "\n".join(lines)


async def _persist_and_reply(message: Message, source_text: str, result: TranslationResult) -> None:
    assert message.from_user is not None

    async with get_session() as session:
        await TranslationRepository(session).add(
            message.from_user.id,
            result.source_language,
            result.target_language,
            source_text,
            result.natural_translation,
        )

    await message.answer(_format_result(result))

    if result.target_language == "en":
        audio = await _tts.synthesize(result.natural_translation)
        ogg_bytes = await mp3_to_ogg_opus(audio)
        await message.answer_voice(BufferedInputFile(ogg_bytes, filename="pronunciation.ogg"))


@router.message(F.text)
async def handle_text_translation(message: Message) -> None:
    assert message.text is not None
    assert message.from_user is not None

    if message.text.startswith("/"):
        return

    try:
        result = await _translator.translate_text(message.text)
    except Exception:
        log.exception("translation_failed", user_id=message.from_user.id)
        await message.answer("Couldn't translate that — try again?")
        return

    await _persist_and_reply(message, message.text, result)


@router.message(F.photo)
async def handle_photo_translation(message: Message) -> None:
    assert message.bot is not None
    assert message.from_user is not None
    assert message.photo is not None

    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    assert file.file_path is not None
    buffer = await message.bot.download_file(file.file_path)
    assert buffer is not None
    image_bytes = buffer.read()

    try:
        result = await _translator.translate_image(image_bytes, media_type="image/jpeg")
    except Exception:
        log.exception("image_translation_failed", user_id=message.from_user.id)
        await message.answer("Couldn't read or translate that image — try again?")
        return

    await _persist_and_reply(message, "[image]", result)


async def handle_translator_voice(message: Message, user: User, audio_bytes: bytes) -> None:
    assert message.bot is not None
    assert message.from_user is not None

    await message.bot.send_chat_action(message.chat.id, "typing")

    transcribed = await _stt.transcribe(audio_bytes, "voice.ogg")

    try:
        result = await _translator.translate_text(transcribed)
    except Exception:
        log.exception("voice_translation_failed", user_id=message.from_user.id)
        await message.answer("Couldn't translate that — try again?")
        return

    await message.answer(f"Heard: <i>{escape(transcribed)}</i>")
    await _persist_and_reply(message, transcribed, result)
