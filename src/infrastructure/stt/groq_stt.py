from groq import AsyncGroq

from src.config.settings import settings


class GroqSTT:
    def __init__(self) -> None:
        self._client = AsyncGroq(api_key=settings.groq_api_key)

    async def transcribe(self, audio_bytes: bytes, filename: str) -> str:
        response = await self._client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model="whisper-large-v3-turbo",
        )
        return response.text.strip()
