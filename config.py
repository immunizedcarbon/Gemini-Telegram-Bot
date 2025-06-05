from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, HttpUrl, SecretStr
from typing import Set, Optional
from google.generai import types

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # Telegram Configuration
    telegram_bot_api_key: SecretStr
    authorized_user_ids: Set[int]

    # Gemini API Configuration
    gemini_api_key: SecretStr
    gemini_model: str = 'gemini-1.5-flash-latest'
    gemini_rpm_limit: int = 10
    gemini_tpm_limit: int = 250000

    # Bot Behavior
    session_ttl: int = 0  # Lifetime of inactive sessions in seconds (0 = unlimited)
    enable_tools: bool = True
    system_instruction: Optional[str] = None
    streaming_update_interval: float = 0.7

    # Persistence
    persistence_file: str = 'bot_persistence.pickle'

    # Safety Settings (example: allow configuring one level)
    harm_block_threshold: str = Field("BLOCK_NONE", pattern=r'^(BLOCK_ONLY_HIGH|BLOCK_MEDIUM_AND_ABOVE|BLOCK_LOW_AND_ABOVE|BLOCK_NONE)$')

    @property
    def gemini_safety_settings(self) -> list[types.SafetySetting]:
        return [
            types.SafetySetting(category=cat, threshold=self.harm_block_threshold)
            for cat in [
                'HARM_CATEGORY_HARASSMENT',
                'HARM_CATEGORY_HATE_SPEECH',
                'HARM_CATEGORY_SEXUALLY_EXPLICIT',
                'HARM_CATEGORY_DANGEROUS_CONTENT',
            ]
        ]

# Global settings instance to be imported by other modules
settings = Settings()
