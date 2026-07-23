from dataclasses import dataclass

from src.core.entities.interview import InterviewFeedback
from src.core.interfaces.interview_coach import InterviewCoach
from src.core.interfaces.stt import STTProvider
from src.core.interfaces.tts import TTSProvider
from src.infrastructure.db.repositories.message_repository import MessageRepository


@dataclass
class InterviewTurnResult:
    transcribed_text: str
    feedback: InterviewFeedback
    reply_audio: bytes


class RunInterviewTurn:
    def __init__(
        self,
        stt: STTProvider,
        coach: InterviewCoach,
        tts: TTSProvider,
        messages: MessageRepository,
    ) -> None:
        self._stt = stt
        self._coach = coach
        self._tts = tts
        self._messages = messages

    async def execute(
        self,
        user_id: int,
        audio_bytes: bytes,
        filename: str,
        question: str,
        interview_type: str,
    ) -> InterviewTurnResult:
        transcribed_text = await self._stt.transcribe(audio_bytes, filename)
        feedback = await self._coach.evaluate_answer(question, transcribed_text, interview_type)

        await self._messages.add(user_id, "user", transcribed_text)
        await self._messages.add(user_id, "assistant", feedback.spoken_response)

        reply_audio = await self._tts.synthesize(feedback.spoken_response)

        return InterviewTurnResult(
            transcribed_text=transcribed_text,
            feedback=feedback,
            reply_audio=reply_audio,
        )
