from __future__ import annotations

from telebot import TeleBot
from telebot.types import Message
from md2tgmd import escape

import gemini
from config import conf

error_info = conf.error_info
before_generate_info = conf.before_generate_info
model_1 = conf.model_1



async def start(message: Message, bot: TeleBot) -> None:
    """Send a greeting to the user."""

    try:
        await bot.reply_to(
            message,
            escape(
                "Welcome, you can ask me questions now. \nFor example: `Who is john lennon?`"
            ),
            parse_mode="MarkdownV2",
        )
    except IndexError:
        await bot.reply_to(message, error_info)


async def gemini_stream_handler(message: Message, bot: TeleBot) -> None:
    """Handle /gemini command using the flash model."""
    try:
        m = message.text.strip().split(maxsplit=1)[1].strip()
    except IndexError:
        await bot.reply_to(
            message,
            escape(
                "Please add what you want to say after /gemini. \nFor example: `/gemini Who is john lennon?`"
            ),
            parse_mode="MarkdownV2",
        )
        return
    await gemini.gemini_stream(bot, message, m, model_1)


async def clear(message: Message, bot: TeleBot) -> None:
    """Clear conversation history for the user."""
    gemini.chat_manager.sessions.pop(str(message.from_user.id), None)
    await bot.reply_to(message, "Your history has been cleared")


async def gemini_private_handler(message: Message, bot: TeleBot) -> None:
    """Handle plain text messages in private chats."""
    m = message.text.strip()
    await gemini.gemini_stream(bot, message, m, model_1)
