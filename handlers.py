from __future__ import annotations

from telebot import TeleBot
from telebot.types import Message
from google.genai import types
import re
from md2tgmd import escape

import gemini
from config import conf

error_info = conf.error_info
before_generate_info = conf.before_generate_info
model_1 = conf.model_1
authorized_user_ids = conf.authorized_user_ids
access_denied_info = conf.access_denied_info

# Map user ID to pending YouTube URL awaiting a prompt
pending_youtube: dict[int, str] = {}

# Simple regex to detect YouTube links
YOUTUBE_RE = re.compile(r"https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[^\s]+")


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


async def youtube_command_handler(message: Message, bot: TeleBot) -> None:
    """Handle /youtube command with a video URL and optional prompt."""
    if not await _check_authorized(message, bot):
        return
    parts = message.text.strip().split(maxsplit=2)
    if len(parts) < 2 or not YOUTUBE_RE.search(parts[1]):
        await bot.reply_to(
            message,
            escape("Please provide a valid YouTube URL after /youtube."),
            parse_mode="MarkdownV2",
        )
        return

    url = parts[1]
    if len(parts) == 2:
        pending_youtube[message.from_user.id] = url
        await bot.reply_to(message, "What would you like to do with this video?")
        return

    prompt = parts[2].strip()
    await gemini.gemini_youtube_stream(bot, message, url, prompt, model_1)


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

    # If user previously sent a YouTube link without a prompt
    if message.from_user.id in pending_youtube and not YOUTUBE_RE.search(m):
        url = pending_youtube.pop(message.from_user.id)
        await gemini.gemini_youtube_stream(bot, message, url, m, model_1)
        return

    # Message contains a YouTube link
    match = YOUTUBE_RE.search(m)
    if match:
        url = match.group(0)
        prompt = m[match.end():].strip()
        if not prompt:
            pending_youtube[message.from_user.id] = url
            await bot.reply_to(message, "What would you like to do with this video?")
            return
        await gemini.gemini_youtube_stream(bot, message, url, prompt, model_1)
        return

    # Regular text
    await gemini.gemini_stream(bot, message, m, model_1)


async def gemini_image_handler(message: Message, bot: TeleBot) -> None:
    """Handle image messages and caption prompts."""
    if not await _check_authorized(message, bot):
        return

    file_id: str | None = None
    mime_type = "image/jpeg"

    if message.content_type == "photo":
        file_id = message.photo[-1].file_id
        mime_type = "image/jpeg"
    elif message.content_type == "document" and message.document.mime_type and message.document.mime_type.startswith("image/"):
        file_id = message.document.file_id
        mime_type = message.document.mime_type

    if not file_id:
        return

    try:
        file = await bot.get_file(file_id)
        image_bytes = await bot.download_file(file.file_path)
    except Exception as exc:  # pragma: no cover - network issues
        await bot.reply_to(message, f"{error_info}\nError details: {exc}")
        return

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    prompt = message.caption.strip() if message.caption else "Describe this image."
    await gemini.gemini_stream(bot, message, [image_part, prompt], model_1)
