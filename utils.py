"""Utility helpers for Telegram bot operations."""

from __future__ import annotations

import logging
from telebot import TeleBot
from telebot.types import Message
from md2tgmd import escape

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
