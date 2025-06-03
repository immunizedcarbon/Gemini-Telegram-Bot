"""Entry point for the Gemini Telegram bot."""

import argparse
import asyncio
import os
import telebot
from telebot.async_telebot import AsyncTeleBot
import handlers
from config import BotConfig, conf

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


async def main() -> None:
    """Start the bot and register command handlers."""
    # Init bot
    if not options.tg_token or not options.GOOGLE_GEMINI_KEY:
        raise SystemExit("API keys must be provided via arguments or environment variables")

    bot = AsyncTeleBot(options.tg_token)
    await bot.delete_my_commands(scope=None, language_code=None)
    await bot.set_my_commands(
    commands=[
        telebot.types.BotCommand("start", "Start"),
        telebot.types.BotCommand("gemini", f"using {conf.model_1}"),
        telebot.types.BotCommand("gemini_pro", f"using {conf.model_2}"),
        telebot.types.BotCommand("draw", "draw picture"),
        telebot.types.BotCommand("edit", "edit photo"),
        telebot.types.BotCommand("clear", "Clear all history"),
        telebot.types.BotCommand("switch","switch default model")
    ],
)
    # Init commands
    bot.register_message_handler(handlers.start,                         commands=['start'],         pass_bot=True)
    bot.register_message_handler(handlers.gemini_stream_handler,         commands=['gemini'],        pass_bot=True)
    bot.register_message_handler(handlers.gemini_pro_stream_handler,     commands=['gemini_pro'],    pass_bot=True)
    bot.register_message_handler(handlers.draw_handler,                  commands=['draw'],          pass_bot=True)
    bot.register_message_handler(handlers.gemini_edit_handler,           commands=['edit'],          pass_bot=True)
    bot.register_message_handler(handlers.clear,                         commands=['clear'],         pass_bot=True)
    bot.register_message_handler(handlers.switch,                        commands=['switch'],        pass_bot=True)
    bot.register_message_handler(handlers.gemini_photo_handler,          content_types=["photo"],    pass_bot=True)
    bot.register_message_handler(
        handlers.gemini_private_handler,
        func=lambda message: message.chat.type == "private",
        content_types=['text'],
        pass_bot=True)

    # Start bot
    print("Starting Gemini_Telegram_Bot.")
    await bot.polling(none_stop=True)

if __name__ == '__main__':
    asyncio.run(main())
