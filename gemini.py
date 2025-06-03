"""Gemini API helpers for streaming chat responses."""

import logging
import time
from typing import Dict, Optional
from telebot.types import Message
from md2tgmd import escape
from telebot import TeleBot
from config import conf
from google import genai
from google.genai import chats

gemini_chat_dict: Dict[str, chats.AsyncChat] = {}

model_1 = conf.model_1
error_info = conf.error_info
before_generate_info = conf.before_generate_info

search_tool = {'google_search': {}}

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

async def gemini_stream(bot: TeleBot, message: Message, m: str, model_type: str) -> None:
    """Stream a chat response from Gemini and edit the message as chunks arrive."""

    sent_message = None
    try:
        sent_message = await bot.reply_to(message, "🤖 Generating answers...")

        chat = None
        chat_dict = gemini_chat_dict

        if str(message.from_user.id) not in chat_dict:
            client = _ensure_client()
            chat = client.aio.chats.create(model=model_type, config={'tools': [search_tool]})
            chat_dict[str(message.from_user.id)] = chat
        else:
            chat = chat_dict[str(message.from_user.id)]

        response = await chat.send_message_stream(m)

        full_response = ""
        last_update = time.time()
        update_interval = conf.streaming_update_interval

        async for chunk in response:
            if hasattr(chunk, 'text') and chunk.text:
                full_response += chunk.text
                current_time = time.time()

                if current_time - last_update >= update_interval:

                    try:
                        await bot.edit_message_text(
                            escape(full_response),
                            chat_id=sent_message.chat.id,
                            message_id=sent_message.message_id,
                            parse_mode="MarkdownV2"
                            )
                    except Exception as e:
                        if "parse markdown" in str(e).lower():
                            await bot.edit_message_text(
                                full_response,
                                chat_id=sent_message.chat.id,
                                message_id=sent_message.message_id
                                )
                        else:
                            if "message is not modified" not in str(e).lower():
                                logger.error("Error updating message: %s", e)
                    last_update = current_time

        try:
            await bot.edit_message_text(
                escape(full_response),
                chat_id=sent_message.chat.id,
                message_id=sent_message.message_id,
                parse_mode="MarkdownV2"
            )
        except Exception as e:
            try:
                if "parse markdown" in str(e).lower():
                    await bot.edit_message_text(
                        full_response,
                        chat_id=sent_message.chat.id,
                        message_id=sent_message.message_id
                    )
            except Exception:
                logger.exception("Failed to send final message")


    except Exception as e:
        logger.exception("Gemini stream failed")
        if sent_message:
            await bot.edit_message_text(
                f"{error_info}\nError details: {str(e)}",
                chat_id=sent_message.chat.id,
                message_id=sent_message.message_id,
            )
        else:
            await bot.reply_to(message, f"{error_info}\nError details: {str(e)}")

