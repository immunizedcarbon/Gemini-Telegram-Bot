"""Application configuration and Gemini safety settings."""

from dataclasses import dataclass, field
import os
from google.genai import types


@dataclass(frozen=True)
class BotConfig:
    """Immutable container for runtime configuration."""

    error_info: str = (
        "⚠️⚠️⚠️\nSomething went wrong !\nPlease try to change your prompt or "
        "contact the admin !"
    )
    before_generate_info: str = "🤖Generating🤖"
    model_1: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-05-20")

    _raw_system_instruction = os.getenv("SYSTEM_INSTRUCTION")
    system_instruction: str | None = (
        _raw_system_instruction.replace("\\n", "\n")
        if _raw_system_instruction
        else None
    )
    streaming_update_interval: float = 0.5
    # Lifetime of an inactive chat session in seconds. Set to 0 for unlimited
    # lifetime. Sessions exist only while the bot process runs.
    session_ttl: float = 0.0
    # Comma separated list of allowed Telegram user IDs
    authorized_user_ids: set[int] = field(default_factory=lambda: {
        int(uid)
        for uid in os.getenv("AUTHORIZED_USER_IDS", "").split(",")
        if uid.strip().isdigit()
    })
    access_denied_info: str = "❌ Access denied"
    gemini_rpm_limit: int = int(os.getenv("GEMINI_RPM_LIMIT", 10))
    gemini_tpm_limit: int = int(os.getenv("GEMINI_TPM_LIMIT", 250000))


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
