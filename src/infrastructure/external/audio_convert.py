import asyncio


async def mp3_to_ogg_opus(mp3_bytes: bytes) -> bytes:
    """Convert MP3 audio (edge-tts output) to OGG/Opus so Telegram renders it
    as a proper voice-message bubble instead of a generic audio file."""
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-i",
        "pipe:0",
        "-c:a",
        "libopus",
        "-b:a",
        "32k",
        "-f",
        "ogg",
        "pipe:1",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate(input=mp3_bytes)
    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {stderr.decode(errors='ignore')}")
    return stdout
