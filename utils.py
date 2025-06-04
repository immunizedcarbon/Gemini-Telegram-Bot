"""Utility helpers for Telegram bot operations."""

from __future__ import annotations

import logging
from telebot import TeleBot
from telebot.types import Message
from md2tgmd import escape

MAX_MESSAGE_LENGTH = 4096


def split_text(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Split ``text`` into chunks no longer than ``max_length``.

    Tries to split on newline boundaries when possible.
    """
    chunks: list[str] = []
    while len(text) > max_length:
        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length
        chunks.append(text[:split_at])
        text = text[split_at:]
    chunks.append(text)
    return chunks

logger = logging.getLogger(__name__)


async def safe_edit(
    bot: TeleBot,
    message: Message,
    text: str,
    *,
    markdown: bool = True,
    escape_text: bool = True,
) -> None:
    """Edit ``message`` with ``text`` handling markdown errors."""
    try:
        await bot.edit_message_text(
            escape(text) if markdown and escape_text else text,
            chat_id=message.chat.id,
            message_id=message.message_id,
            parse_mode="MarkdownV2" if markdown else None,
        )
    except Exception as exc:  # Telegram API may reject Markdown
        if "parse markdown" in str(exc).lower() and markdown:
            await safe_edit(bot, message, text, markdown=False, escape_text=False)
        elif "message is not modified" not in str(exc).lower():
            logger.error("Error updating message: %s", exc)
