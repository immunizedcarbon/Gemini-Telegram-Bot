from __future__ import annotations

from telebot import TeleBot
import asyncio
from telebot.types import Message
from md2tgmd import escape

import gemini
from config import conf

error_info = conf.error_info
before_generate_info = conf.before_generate_info
model_1 = conf.model_1
authorized_user_ids = conf.authorized_user_ids
access_denied_info = conf.access_denied_info


async def _check_authorized(message: Message, bot: TeleBot) -> bool:
    """Return True if user is allowed, else reply with denial."""
    if message.from_user.id in authorized_user_ids:
        return True
    await bot.reply_to(message, access_denied_info)
    return False





async def gemini_stream_handler(message: Message, bot: TeleBot) -> None:
    """Handle /gemini command using the flash model."""
    if not await _check_authorized(message, bot):
        return
    try:
        m = message.text.strip().split(maxsplit=1)[1].strip()
    except IndexError:
        await bot.reply_to(
            message,
            escape("Please add what you want to say after /gemini."),
            parse_mode="MarkdownV2",
        )
        return
    await gemini.gemini_stream(bot, message, m, model_1)


async def clear(message: Message, bot: TeleBot) -> None:
    """Clear conversation history for the user."""
    if not await _check_authorized(message, bot):
        return
    gemini.chat_manager.sessions.pop(str(message.from_user.id), None)
    await bot.reply_to(message, "Your history has been cleared")


async def gemini_private_handler(message: Message, bot: TeleBot) -> None:
    """Handle plain text messages in private chats."""
    if not await _check_authorized(message, bot):
        return
    m = message.text.strip()
    await gemini.gemini_stream(bot, message, m, model_1)
