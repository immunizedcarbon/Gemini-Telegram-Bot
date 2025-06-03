"""Gemini API helpers for streaming chat responses."""

from __future__ import annotations

import logging
import time
from typing import Dict, Optional

from telebot import TeleBot
from telebot.types import Message
from google import genai
from google.genai import chats

from config import conf
from utils import safe_edit

gemini_chat_dict: Dict[str, chats.AsyncChat] = {}

model_1 = conf.model_1
error_info = conf.error_info
before_generate_info = conf.before_generate_info

search_tool = {"google_search": {}}

logger = logging.getLogger(__name__)

client: Optional[genai.Client] = None


def init_client(api_key: str) -> None:
    """Configure the global Gemini client."""
    global client
    client = genai.Client(api_key=api_key)


def _ensure_client() -> genai.Client:
    if client is None:
        raise RuntimeError("Gemini client not initialized")
    return client


async def gemini_stream(
    bot: TeleBot, message: Message, query: str, model_type: str
) -> None:
    """Stream a chat response from Gemini and edit the message as chunks arrive."""

    sent_message: Message | None = None
    try:
        sent_message = await bot.reply_to(message, before_generate_info)

        chat = gemini_chat_dict.get(str(message.from_user.id))
        if chat is None:
            client = _ensure_client()
            chat = client.aio.chats.create(
                model=model_type,
                config={"tools": [search_tool]},
            )
            gemini_chat_dict[str(message.from_user.id)] = chat

        response = await chat.send_message_stream(query)

        full_response = ""
        last_update = time.monotonic()
        update_interval = conf.streaming_update_interval

        async for chunk in response:
            if getattr(chunk, "text", ""):
                full_response += chunk.text
                if time.monotonic() - last_update >= update_interval:
                    await safe_edit(bot, sent_message, full_response)
                    last_update = time.monotonic()

        await safe_edit(bot, sent_message, full_response)

    except Exception as exc:  # pragma: no cover - network issues
        logger.exception("Gemini stream failed")
        if sent_message:
            await safe_edit(
                bot,
                sent_message,
                f"{error_info}\nError details: {exc}",
                parse_markdown=False,
            )
        else:
            await bot.reply_to(message, f"{error_info}\nError details: {exc}")
