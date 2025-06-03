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
    download_pic_notify: str = "🤖Loading picture🤖"
    model_1: str = "gemini-2.5-flash-preview-04-17"
    model_2: str = "gemini-2.5-pro-preview-05-06"
    model_3: str = "gemini-2.0-flash-preview-image-generation"
    streaming_update_interval: float = 0.5


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
    )
]

generation_config = types.GenerateContentConfig(
    response_modalities=['Text', 'Image'],
    safety_settings=safety_settings,
)
