import edge_tts

from src.config.settings import settings


class EdgeTTS:
    def __init__(self, voice: str | None = None) -> None:
        self._voice = voice or settings.edge_tts_voice_en

    async def synthesize(self, text: str) -> bytes:
        communicate = edge_tts.Communicate(text, self._voice)
        audio = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
        return bytes(audio)
