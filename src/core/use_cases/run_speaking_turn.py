from dataclasses import dataclass

from src.core.entities.conversation import ConversationTurn
from src.core.interfaces.llm import ConversationProvider
from src.core.interfaces.stt import STTProvider
from src.core.interfaces.tts import TTSProvider
from src.infrastructure.db.repositories.message_repository import MessageRepository


@dataclass
class SpeakingTurnResult:
    transcribed_text: str
    reply_text: str
    reply_audio: bytes


class RunSpeakingTurn:
    def __init__(
        self,
        stt: STTProvider,
        llm: ConversationProvider,
        tts: TTSProvider,
        messages: MessageRepository,
    ) -> None:
        self._stt = stt
        self._llm = llm
        self._tts = tts
        self._messages = messages

    async def execute(self, user_id: int, audio_bytes: bytes, filename: str) -> SpeakingTurnResult:
        transcribed_text = await self._stt.transcribe(audio_bytes, filename)

        history_rows = await self._messages.recent(user_id, limit=10)
        history = [
            ConversationTurn(role=row.role, content=row.content_text)  # type: ignore[arg-type]
            for row in history_rows
        ]

        reply_text = await self._llm.reply(history, transcribed_text)

        await self._messages.add(user_id, "user", transcribed_text)
        await self._messages.add(user_id, "assistant", reply_text)

        reply_audio = await self._tts.synthesize(reply_text)

        return SpeakingTurnResult(
            transcribed_text=transcribed_text,
            reply_text=reply_text,
            reply_audio=reply_audio,
        )
