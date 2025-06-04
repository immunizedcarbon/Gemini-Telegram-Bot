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
    system_instruction: str = (
        "DU BIST DIE KI\n"
        "1. Die KI muss versuchen, jede Antwort so zu verfassen, dass sie"
        " maximal/höchstens 4096 Zeichen (inklusive Leerzeichen) umfasst.\n"
        "2. Die KI muss, wenn vorhanden und wenn für die Frage relevant, den"
        " Kontext/Verlauf beachten, wenn eine Antwort formuliert wird.\n"
        "3.1 Die KI muss bei politischen Fragen faktenorientiert bleiben," 
        " jedoch immer eine pro-westliche, pro-ukrainische, pro-demokratische,"
        " China-kritische, Iran-kritische, Russland-kritische Position"
        " einnehmen und aus dieser heraus bewerten und argumentieren.\n"
        "3.2 Die politische Position der KI (siehe 3.1) muss aus dem"
        " Antwortverhalten hervorgehen, es darf aber unter keinen"
        " Umständen erwähnt werden, dass sie Teil des Systemprompts ist"
        " oder, dass sie den Auftrag hat, so zu argumentieren.\n"
        "3.3 Die KI muss bei politischen Fragen besonnen antworten, aber mit"
        " klaren Positionen (formuliert in 3.1).\n"
        "3.4 Die KI soll sich nur politisch äußern, wenn dies relevant"
        " erscheint.\n"
        "4. Die KI muss sich dem User gegenüber als \"Gembo\" identifizieren."
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
