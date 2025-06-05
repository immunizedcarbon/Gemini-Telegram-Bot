"""Entry point for the Gemini Telegram bot."""

import argparse
import asyncio
import logging
import os

from dotenv import load_dotenv
import telebot
from telebot.async_telebot import AsyncTeleBot

import handlers
import gemini

# Load environment from .env if present
load_dotenv()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "tg_token",
        nargs="?",
        default=os.getenv("TELEGRAM_BOT_API_KEY"),
        help="Telegram token",
    )
    parser.add_argument(
        "GEMINI_API_KEY",
        nargs="?",
        default=os.getenv("GEMINI_API_KEY"),
        help="Google Gemini API key",
    )
    return parser.parse_args()


options = parse_args()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Start the bot and register command handlers."""
    # Init bot
    if not options.tg_token or not options.GEMINI_API_KEY:
        raise SystemExit(
            "API keys must be provided via arguments or environment variables"
        )

    gemini.init_client(options.GEMINI_API_KEY)

    bot = AsyncTeleBot(options.tg_token)
    await bot.delete_my_commands(scope=None, language_code=None)
    await bot.set_my_commands(
        commands=[
            telebot.types.BotCommand("start", "Show help"),
            telebot.types.BotCommand("clear", "Clear all history"),
        ],
    )
    # Init commands
    bot.register_message_handler(
        handlers.start_handler, commands=["start"], pass_bot=True
    )
    bot.register_message_handler(
        handlers.gemini_stream_handler, commands=["gemini"], pass_bot=True
    )
    bot.register_message_handler(
        handlers.youtube_command_handler, commands=["youtube", "yt"], pass_bot=True
    )
    bot.register_message_handler(handlers.clear, commands=["clear"], pass_bot=True)
    bot.register_message_handler(
        handlers.gemini_pdf_handler,
        content_types=["document"],
        func=lambda m: m.document is not None and m.document.mime_type == "application/pdf",
        pass_bot=True,
    )
    bot.register_message_handler(
        handlers.gemini_audio_handler,
        content_types=["audio", "voice", "document"],
        func=lambda m: (
            (m.content_type in {"audio", "voice"})
            or (
                m.content_type == "document"
                and m.document is not None
                and m.document.mime_type
                and m.document.mime_type.startswith("audio/")
            )
        ),
        pass_bot=True,
    )
    bot.register_message_handler(
        handlers.gemini_private_handler,
        func=lambda message: message.chat.type == "private",
        content_types=["text"],
        pass_bot=True,
    )
    bot.register_message_handler(
        handlers.gemini_image_handler,
        content_types=["photo", "document"],
        pass_bot=True,
    )

    # Start bot
    logger.info("Starting Gemini_Telegram_Bot.")
    await bot.polling(none_stop=True)


if __name__ == "__main__":
    asyncio.run(main())
