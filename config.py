"""Application configuration and Gemini safety settings."""

from dataclasses import dataclass
from google.genai import types


@dataclass(frozen=True)
class BotConfig:
    """Immutable container for runtime configuration."""

    error_info: str = (
        "⚠️⚠️⚠️\nSomething went wrong !\nPlease try to change your prompt or "
        "contact the admin !"
    )
    before_generate_info: str = "🤖Generating🤖"
    model_1: str = "gemini-2.5-flash-preview-05-20"
    streaming_update_interval: float = 0.5
    # Lifetime of an inactive chat session in seconds
    session_ttl: float = 3600.0


conf = BotConfig()

safety_settings = [
    types.SafetySetting(
        category="HARM_CATEGORY_HARASSMENT",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_HATE_SPEECH",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_DANGEROUS_CONTENT",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_CIVIC_INTEGRITY",
        threshold="BLOCK_NONE",
    ),
]
