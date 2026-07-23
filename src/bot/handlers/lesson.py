from html import escape

import structlog
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from src.core.use_cases.generate_daily_lesson import GenerateDailyLesson
from src.infrastructure.db.repositories.mistake_repository import MistakeRepository
from src.infrastructure.db.repositories.vocabulary_repository import VocabularyRepository
from src.infrastructure.db.session import get_session
from src.infrastructure.external.audio_convert import mp3_to_ogg_opus
from src.infrastructure.tts.edge_tts_adapter import EdgeTTS
from src.services.learning.lesson_generator import ClaudeLessonGenerator

router = Router(name="lesson")
log = structlog.get_logger()

_tts = EdgeTTS()
_lesson_generator = ClaudeLessonGenerator()

CATEGORY_LABELS = {
    "grammar": "Grammar",
    "vocabulary": "Vocabulary",
    "fluency": "Fluency",
    "naturalness": "Naturalness",
}


@router.message(Command("lesson"))
async def cmd_lesson(message: Message) -> None:
    assert message.from_user is not None
    assert message.bot is not None

    await message.bot.send_chat_action(message.chat.id, "record_voice")

    async with get_session() as session:
        use_case = GenerateDailyLesson(
            mistakes=MistakeRepository(session),
            generator=_lesson_generator,
        )
        try:
            opening_text = await use_case.execute(message.from_user.id)
        except Exception:
            log.exception("lesson_generation_failed", user_id=message.from_user.id)
            await message.answer("Couldn't put today's lesson together — try again in a bit.")
            return

    audio = await _tts.synthesize(opening_text)
    ogg_bytes = await mp3_to_ogg_opus(audio)
    await message.answer_voice(BufferedInputFile(ogg_bytes, filename="lesson.ogg"))


@router.message(Command("grammar"))
async def cmd_grammar(message: Message) -> None:
    assert message.from_user is not None

    async with get_session() as session:
        counts = await MistakeRepository(session).category_counts(message.from_user.id, limit=200)

    if not counts:
        await message.answer(
            "No mistakes logged yet — keep practicing and I'll start tracking patterns."
        )
        return

    lines = ["<b>Your recent mistake breakdown</b>"]
    for category, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        label = CATEGORY_LABELS.get(category, category.title())
        lines.append(f"{escape(label)}: {count}")
    await message.answer("\n".join(lines))


@router.message(Command("vocabulary"))
async def cmd_vocabulary(message: Message) -> None:
    assert message.from_user is not None

    async with get_session() as session:
        items = await VocabularyRepository(session).recent(message.from_user.id, limit=15)

    if not items:
        await message.answer("No vocabulary saved yet — it fills up as we talk.")
        return

    lines = ["<b>Words to remember</b>"]
    for item in items:
        lines.append(f"<b>{escape(item.word_or_phrase)}</b> — {escape(item.translation_ru)}")
    await message.answer("\n".join(lines))
