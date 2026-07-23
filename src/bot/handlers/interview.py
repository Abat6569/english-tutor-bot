import random

import structlog
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from src.core.use_cases.run_interview_turn import RunInterviewTurn
from src.infrastructure.db.models.user import User
from src.infrastructure.db.repositories.message_repository import MessageRepository
from src.infrastructure.db.repositories.user_repository import UserRepository
from src.infrastructure.db.session import get_session
from src.infrastructure.external.audio_convert import mp3_to_ogg_opus
from src.infrastructure.stt.groq_stt import GroqSTT
from src.infrastructure.tts.edge_tts_adapter import EdgeTTS
from src.services.ai.claude_interviewer import ClaudeInterviewCoach

router = Router(name="interview")
log = structlog.get_logger()

_stt = GroqSTT()
_tts = EdgeTTS()
_coach = ClaudeInterviewCoach()

INTERVIEW_QUESTIONS: dict[str, list[str]] = {
    "hr": [
        "Tell me about yourself.",
        "Why do you want to work for our company?",
        "What are your strengths and weaknesses?",
        "Where do you see yourself in five years?",
        "Why are you leaving your current job?",
    ],
    "behavioral": [
        "Describe a difficult situation you faced at work and how you handled it.",
        "Tell me about a time you disagreed with a colleague or supervisor.",
        "Give an example of when you had to meet a tight deadline.",
        "Describe a mistake you made and what you learned from it.",
        "Tell me about a time you had to explain a technical issue to a " "non-technical person.",
    ],
    "technical": [
        "Tell me about an NCR you raised and how it was resolved.",
        "Walk me through how you review an ITP before an inspection.",
        "What's the difference between a Method Statement and an ITP?",
        "How do you handle a disagreement with a contractor about a non-conformance?",
        "Describe your process for reviewing as-built documentation.",
    ],
    "engineering": [
        "Describe your QA/QC responsibilities on your current project.",
        "What standards do you commonly reference in your inspections, like IEC, " "IEEE, or ISO?",
        "Walk me through a SAT or FAT you were involved in.",
        "How do you ensure compliance during cable installation inspections?",
        "Tell me about your experience with BESS, solar, or wind projects.",
    ],
}


def _pick_next_question(interview_type: str, asked: list[str]) -> str | None:
    pool = [q for q in INTERVIEW_QUESTIONS.get(interview_type, []) if q not in asked]
    if not pool:
        return None
    return random.choice(pool)


@router.message(Command("interview"))
async def cmd_interview(message: Message) -> None:
    assert message.from_user is not None
    assert message.bot is not None

    interview_type = random.choice(list(INTERVIEW_QUESTIONS.keys()))
    question = random.choice(INTERVIEW_QUESTIONS[interview_type])

    async with get_session() as session:
        await UserRepository(session).update_settings(
            message.from_user.id,
            mode="interview",
            interview_type=interview_type,
            interview_question=question,
            interview_asked=[],
        )

    intro = f"Let's do a mock {interview_type} interview question. {question}"
    await message.bot.send_chat_action(message.chat.id, "record_voice")
    audio = await _tts.synthesize(intro)
    ogg_bytes = await mp3_to_ogg_opus(audio)
    await message.answer_voice(BufferedInputFile(ogg_bytes, filename="interview_intro.ogg"))


async def handle_interview_voice(message: Message, user: User, audio_bytes: bytes) -> None:
    assert message.bot is not None
    assert message.from_user is not None

    question = str(user.settings_json.get("interview_question", ""))
    interview_type = str(user.settings_json.get("interview_type", "hr"))

    await message.bot.send_chat_action(message.chat.id, "record_voice")

    async with get_session() as session:
        use_case = RunInterviewTurn(
            stt=_stt, coach=_coach, tts=_tts, messages=MessageRepository(session)
        )
        try:
            result = await use_case.execute(
                message.from_user.id, audio_bytes, "voice.ogg", question, interview_type
            )
        except Exception:
            log.exception("interview_turn_failed", user_id=message.from_user.id)
            await message.answer("Sorry, something went wrong. Try answering again?")
            return

    log.info(
        "interview_turn_ok",
        user_id=message.from_user.id,
        question=question,
        heard=result.transcribed_text,
        passes=result.feedback.passes,
        score=result.feedback.score,
    )

    ogg_bytes = await mp3_to_ogg_opus(result.reply_audio)
    await message.answer_voice(BufferedInputFile(ogg_bytes, filename="reply.ogg"))

    if not result.feedback.passes:
        return

    asked_raw = user.settings_json.get("interview_asked", [])
    asked = [*(asked_raw if isinstance(asked_raw, list) else []), question]
    next_question = _pick_next_question(interview_type, asked)

    async with get_session() as session:
        repo = UserRepository(session)
        if next_question is None:
            await repo.update_settings(message.from_user.id, mode="general")
            await message.answer(
                "Nice, you've worked through this set! Send /interview to start a new round."
            )
        else:
            await repo.update_settings(
                message.from_user.id,
                interview_question=next_question,
                interview_asked=asked,
            )
