from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str
    admin_telegram_id: int

    anthropic_api_key: str
    anthropic_conversation_model: str = "claude-sonnet-5"
    anthropic_evaluation_model: str = "claude-sonnet-5"

    stt_provider: str = "groq"
    groq_api_key: str = ""

    tts_provider: str = "edge"
    edge_tts_voice_en: str = "en-US-AriaNeural"
    edge_tts_voice_ru: str = "ru-RU-SvetlanaNeural"

    database_url: str
    redis_url: str

    log_level: str = "INFO"
    timezone: str = "Asia/Tashkent"


settings = Settings()  # type: ignore[call-arg]
