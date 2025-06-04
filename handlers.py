from __future__ import annotations

from telebot import TeleBot
import asyncio
from telebot.types import Message
from md2tgmd import escape
from google.genai import types

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


async def _extract_image_parts(message: Message, bot: TeleBot) -> list[types.Part]:
    """Return a list of Gemini Parts built from images in the message."""
    parts: list[types.Part] = []

    if message.photo:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        img_bytes = await bot.download_file(file_info.file_path)
        parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))

    if message.document and (message.document.mime_type or "").startswith("image/"):
        file_info = await bot.get_file(message.document.file_id)
        img_bytes = await bot.download_file(file_info.file_path)
        parts.append(
            types.Part.from_bytes(
                data=img_bytes,
                mime_type=message.document.mime_type or "image/jpeg",
            )
        )

    return parts





async def gemini_stream_handler(message: Message, bot: TeleBot) -> None:
    """Handle /gemini command using the flash model."""
    if not await _check_authorized(message, bot):
        return
    content = (message.text or message.caption or "").strip()
    try:
        m = content.split(maxsplit=1)[1].strip()
    except IndexError:
        await bot.reply_to(
            message,
            escape("Please add what you want to say after /gemini."),
            parse_mode="MarkdownV2",
        )
        return
    images = await _extract_image_parts(message, bot)
    await gemini.gemini_stream(bot, message, m, model_1, images=images)


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
    text = (message.text or message.caption or "").strip()
    images = await _extract_image_parts(message, bot)
    if not text and images:
        text = "Describe this image."
    await gemini.gemini_stream(bot, message, text, model_1, images=images)
