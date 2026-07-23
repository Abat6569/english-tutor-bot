import asyncio
from html import escape

import structlog
from aiogram import Bot, F, Router
from aiogram.types import BufferedInputFile, Message

from src.bot.handlers.interview import handle_interview_voice
from src.bot.handlers.translator import handle_translator_voice
from src.core.entities.conversation import ConversationTurn
from src.core.entities.evaluation import TurnEvaluation
from src.core.use_cases.evaluate_speaking_turn import EvaluateSpeakingTurn
from src.core.use_cases.run_speaking_turn import RunSpeakingTurn
from src.infrastructure.db.models.user import User
from src.infrastructure.db.repositories.achievement_repository import AchievementRepository
from src.infrastructure.db.repositories.message_repository import MessageRepository
from src.infrastructure.db.repositories.mistake_repository import MistakeRepository
from src.infrastructure.db.repositories.user_repository import UserRepository
from src.infrastructure.db.repositories.vocabulary_repository import VocabularyRepository
from src.infrastructure.db.session import get_session
from src.infrastructure.external.audio_convert import mp3_to_ogg_opus
from src.infrastructure.stt.groq_stt import GroqSTT
from src.infrastructure.tts.edge_tts_adapter import EdgeTTS
from src.services.ai.claude_client import ClaudeConversationProvider
from src.services.ai.claude_evaluator import ClaudeTurnEvaluator
from src.services.ai.claude_professional import ClaudeProfessionalProvider
from src.services.gamification.xp_service import GamificationService

router = Router(name="voice")
log = structlog.get_logger()

_stt = GroqSTT()
_tts = EdgeTTS()
_llm = ClaudeConversationProvider()
_professional_llm = ClaudeProfessionalProvider()
_evaluator = ClaudeTurnEvaluator()

MAX_MISTAKES_SHOWN = 3

# Fire-and-forget evaluation tasks must be kept referenced or asyncio may
# garbage-collect them mid-flight.
_background_tasks: set[asyncio.Task[None]] = set()


class _ProfessionalModeAdapter:
    """Adapts ClaudeProfessionalProvider's persona/topic call signature to the
    plain (history, message) shape RunSpeakingTurn expects."""

    def __init__(self, provider: ClaudeProfessionalProvider, user: User) -> None:
        self._provider = provider
        self._persona = str(user.settings_json["professional_persona"])
        self._persona_description = str(user.settings_json["professional_persona_description"])
        self._topic = str(user.settings_json["professional_topic"])

    async def reply(self, history: list[ConversationTurn], user_message: str) -> str:
        return await self._provider.reply(
            history,
            user_message,
            persona=self._persona,
            persona_description=self._persona_description,
            topic=self._topic,
        )


def _pick_conversation_provider(
    user: User,
) -> ClaudeConversationProvider | _ProfessionalModeAdapter:
    is_professional = (
        user.settings_json.get("mode") == "professional"
        and "professional_topic" in user.settings_json
    )
    if is_professional:
        return _ProfessionalModeAdapter(_professional_llm, user)
    return _llm


def _format_feedback(evaluation: TurnEvaluation) -> str | None:
    if not evaluation.mistakes and not evaluation.vocabulary_notes:
        return None

    lines = []
    if evaluation.mistakes:
        lines.append("📝 <b>Quick correction</b>")
        for item in evaluation.mistakes[:MAX_MISTAKES_SHOWN]:
            lines.append(
                f'"{escape(item.original)}" → "{escape(item.corrected)}"\n'
                f"{escape(item.explanation)}"
            )
    if evaluation.vocabulary_notes:
        lines.append("📚 <b>Word to remember</b>")
        for note in evaluation.vocabulary_notes[:2]:
            lines.append(
                f"<b>{escape(note.word_or_phrase)}</b> — {escape(note.translation_ru)}\n"
                f"<i>{escape(note.example_sentence)}</i>"
            )
    return "\n\n".join(lines)


async def _evaluate_and_notify(bot: Bot, chat_id: int, user_id: int, user_utterance: str) -> None:
    try:
        async with get_session() as session:
            use_case = EvaluateSpeakingTurn(
                evaluator=_evaluator,
                mistakes=MistakeRepository(session),
                vocabulary=VocabularyRepository(session),
            )
            evaluation = await use_case.execute(user_id, user_utterance)
    except Exception:
        log.exception("evaluation_failed", user_id=user_id)
        return

    log.info(
        "evaluation_ok",
        user_id=user_id,
        grammar=evaluation.grammar_score,
        vocabulary=evaluation.vocabulary_score,
        fluency=evaluation.fluency_score,
        naturalness=evaluation.naturalness_score,
        mistake_count=len(evaluation.mistakes),
    )

    xp_gained = 10 + (
        evaluation.grammar_score
        + evaluation.vocabulary_score
        + evaluation.fluency_score
        + evaluation.naturalness_score
    )
    try:
        async with get_session() as session:
            gamification = GamificationService(
                users=UserRepository(session), achievements=AchievementRepository(session)
            )
            update = await gamification.record_activity(user_id, xp_gained)
    except Exception:
        log.exception("gamification_update_failed", user_id=user_id)
        update = None

    lines = []
    feedback_text = _format_feedback(evaluation)
    if feedback_text is not None:
        lines.append(feedback_text)
    if update is not None and update.newly_unlocked:
        lines.append("\n".join(f"🎉 {label}" for label in update.newly_unlocked))

    if lines:
        await bot.send_message(chat_id, "\n\n".join(lines))


@router.message(F.voice)
async def handle_voice(message: Message) -> None:
    assert message.from_user is not None
    assert message.voice is not None
    assert message.bot is not None

    async with get_session() as session:
        user = await UserRepository(session).get_or_create(
            message.from_user.id, message.from_user.username
        )

    file = await message.bot.get_file(message.voice.file_id)
    assert file.file_path is not None
    buffer = await message.bot.download_file(file.file_path)
    assert buffer is not None
    audio_bytes = buffer.read()

    mode = user.settings_json.get("mode")
    if mode == "interview":
        await handle_interview_voice(message, user, audio_bytes)
        return
    if mode == "translator":
        await handle_translator_voice(message, user, audio_bytes)
        return

    await message.bot.send_chat_action(message.chat.id, "record_voice")

    async with get_session() as session:
        use_case = RunSpeakingTurn(
            stt=_stt,
            llm=_pick_conversation_provider(user),
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

    task = asyncio.create_task(
        _evaluate_and_notify(
            message.bot, message.chat.id, message.from_user.id, result.transcribed_text
        )
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
