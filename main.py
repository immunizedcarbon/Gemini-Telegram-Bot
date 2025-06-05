import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    PicklePersistence,
    ContextTypes,
    filters,
)

import handlers
import gemini
from config import settings

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    gemini.init_client(settings.gemini_api_key.get_secret_value())
    await application.bot.set_my_commands([
        ("start", "Show help and bot info"),
        ("clear", "Clear conversation history"),
    ])

def main() -> None:
    persistence = PicklePersistence(filepath=settings.persistence_file)

    application = (
        Application.builder()
        .token(settings.telegram_bot_api_key.get_secret_value())
        .persistence(persistence)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", handlers.start_handler))
    application.add_handler(CommandHandler("clear", handlers.clear_handler))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.text_handler))
    application.add_handler(MessageHandler(filters.PHOTO, handlers.image_handler))
    application.add_handler(MessageHandler(filters.Document.IMAGE, handlers.image_handler))
    application.add_handler(MessageHandler(filters.Document.PDF, handlers.pdf_handler))
    application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, handlers.audio_handler))

    application.add_error_handler(handlers.error_handler)

    logger.info("Starting Gemini_Telegram_Bot with PTB.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
