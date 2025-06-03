"""Entry point for the Gemini Telegram bot."""

import argparse
import asyncio
import logging
import os

from dotenv import load_dotenv
import telebot
from telebot.async_telebot import AsyncTeleBot

import handlers
from config import conf
import gemini

# Init args
parser = argparse.ArgumentParser()
parser.add_argument(
    "tg_token",
    nargs="?",
    default=os.getenv("TELEGRAM_BOT_API_KEY"),
    help="Telegram token",
)
parser.add_argument(
    "GOOGLE_GEMINI_KEY",
    nargs="?",
    default=os.getenv("GOOGLE_GEMINI_KEY") or os.getenv("GEMINI_API_KEYS"),
    help="Google Gemini API key",
)
options = parser.parse_args()

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Start the bot and register command handlers."""
    # Init bot
    if not options.tg_token or not options.GOOGLE_GEMINI_KEY:
        raise SystemExit("API keys must be provided via arguments or environment variables")

    gemini.init_client(options.GOOGLE_GEMINI_KEY)

    bot = AsyncTeleBot(options.tg_token)
    await bot.delete_my_commands(scope=None, language_code=None)
    await bot.set_my_commands(
    commands=[
        telebot.types.BotCommand("start", "Start"),
        telebot.types.BotCommand("gemini", f"using {conf.model_1}"),
        telebot.types.BotCommand("clear", "Clear all history")
    ],
)
    # Init commands
    bot.register_message_handler(handlers.start,                         commands=['start'],         pass_bot=True)
    bot.register_message_handler(handlers.gemini_stream_handler,         commands=['gemini'],        pass_bot=True)
    bot.register_message_handler(handlers.clear,                         commands=['clear'],         pass_bot=True)
    bot.register_message_handler(
        handlers.gemini_private_handler,
        func=lambda message: message.chat.type == "private",
        content_types=['text'],
        pass_bot=True)

    # Start bot
    logger.info("Starting Gemini_Telegram_Bot.")
    await bot.polling(none_stop=True)

if __name__ == '__main__':
    asyncio.run(main())
