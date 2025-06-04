"""Gemini API helpers for streaming chat responses."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from telebot import TeleBot
from telebot.types import Message
from google import genai
from google.genai import chats, types

from config import conf, safety_settings
from utils import safe_edit
from md2tgmd import escape


@dataclass
class ChatSession:
    chat: chats.AsyncChat
    last_used: float = field(default_factory=time.monotonic)


class ChatManager:
    def __init__(self, ttl: float) -> None:
        self.ttl = ttl
        self.sessions: Dict[str, ChatSession] = {}

    def get_chat(self, user_id: str, *, model: str) -> chats.AsyncChat:
        now = time.monotonic()
        session = self.sessions.get(user_id)
        if session is not None:
            session.last_used = now
            return session.chat

        client = _ensure_client()
        chat = client.aio.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                tools=[search_tool],
                system_instruction=conf.system_instruction,
                safety_settings=safety_settings,
            ),
        )
        self.sessions[user_id] = ChatSession(chat)
        return chat

    def cleanup(self) -> None:
        if self.ttl <= 0:
            return
        now = time.monotonic()
        to_remove = [uid for uid, sess in self.sessions.items() if now - sess.last_used > self.ttl]
        for uid in to_remove:
            del self.sessions[uid]


chat_manager = ChatManager(conf.session_ttl)

model_1 = conf.model_1
error_info = conf.error_info
before_generate_info = conf.before_generate_info

search_tool = {"google_search": {}}

logger = logging.getLogger(__name__)

client: Optional[genai.Client] = None


def _format_sources(candidate: types.Candidate | None) -> str | None:
    """Return Markdown formatted sources from ``candidate`` if available."""
    if not candidate or not candidate.grounding_metadata:
        return None
    chunks = candidate.grounding_metadata.grounding_chunks or []
    links: list[str] = []
    for chunk in chunks:
        web = chunk.web
        if not web or not web.uri:
            continue
        title = web.title or web.domain or "source"
        links.append(f"[{escape(title)}]({web.uri})")

    if not links:
        return None
    # Remove duplicates while preserving order
    deduped = []
    seen = set()
    for link in links:
        if link not in seen:
            seen.add(link)
            deduped.append(link)
    return "Sources: " + ", ".join(deduped)


def init_client(api_key: str) -> None:
    """Configure the global Gemini client."""
    global client
    client = genai.Client(api_key=api_key)


def _ensure_client() -> genai.Client:
    if client is None:
        raise RuntimeError("Gemini client not initialized")
    return client


async def gemini_stream(
    bot: TeleBot,
    message: Message,
    query: object,
    model_type: str,
) -> None:
    """Stream a chat response from Gemini.

    ``query`` may be a plain string or a list of ``types.Part`` objects mixed
    with strings for multimodal prompts.
    """

    sent_message: Message | None = None
    try:
        sent_message = await bot.reply_to(message, before_generate_info)

        chat = chat_manager.get_chat(str(message.from_user.id), model=model_type)
        chat_manager.cleanup()

        response = await chat.send_message_stream(query)

        full_response = ""
        last_update = time.monotonic()
        update_interval = conf.streaming_update_interval
        last_candidate: types.Candidate | None = None

        async for chunk in response:
            if getattr(chunk, "text", ""):
                full_response += chunk.text
                if time.monotonic() - last_update >= update_interval:
                    await safe_edit(bot, sent_message, full_response)
                    last_update = time.monotonic()
            if chunk.candidates:
                last_candidate = chunk.candidates[0]

        sources = _format_sources(last_candidate) if last_candidate else None
        final_text = escape(full_response)
        if sources:
            final_text += "\n\n" + sources

        await safe_edit(bot, sent_message, final_text, parse_markdown=False)

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


async def gemini_youtube_stream(
    bot: TeleBot,
    message: Message,
    youtube_url: str,
    prompt: str,
    model_type: str,
) -> None:
    """Stream a response based on the provided YouTube video and prompt."""

    video_part = types.Part(
        file_data=types.FileData(file_uri=youtube_url)
    )
    await gemini_stream(bot, message, [video_part, prompt], model_type)
