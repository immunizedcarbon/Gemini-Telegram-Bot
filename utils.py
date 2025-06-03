"""Utility helpers for Telegram bot operations."""

from __future__ import annotations

import logging
from telebot import TeleBot
from telebot.types import Message
from md2tgmd import escape

logger = logging.getLogger(__name__)


async def safe_edit(
    bot: TeleBot, message: Message, text: str, *, parse_markdown: bool = True
) -> None:
    """Edit ``message`` with ``text`` handling markdown errors."""
    try:
        await bot.edit_message_text(
            escape(text) if parse_markdown else text,
            chat_id=message.chat.id,
            message_id=message.message_id,
            parse_mode="MarkdownV2" if parse_markdown else None,
        )
    except Exception as exc:  # Telegram API may reject Markdown
        if "parse markdown" in str(exc).lower() and parse_markdown:
            await safe_edit(bot, message, text, parse_markdown=False)
        elif "message is not modified" not in str(exc).lower():
            logger.error("Error updating message: %s", exc)
