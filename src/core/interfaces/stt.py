from typing import Protocol


class STTProvider(Protocol):
    async def transcribe(self, audio_bytes: bytes, filename: str) -> str: ...
