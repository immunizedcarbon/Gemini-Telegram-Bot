"""Gemini API helpers for streaming chat responses."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
from collections import deque

from telebot import TeleBot
from telebot.types import Message
from google import genai
from google.genai import chats, types

from config import conf, safety_settings
from utils import safe_edit, split_text, MAX_MESSAGE_LENGTH
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
        to_remove = [
            uid
            for uid, sess in self.sessions.items()
            if now - sess.last_used > self.ttl
        ]
        for uid in to_remove:
            del self.sessions[uid]


class RateLimiter:
    """Simple token and request limiter for the Gemini API."""

    def __init__(self, rpm: int, tpm: int) -> None:
        self.rpm = rpm
        self.tpm = tpm
        self.req_times: deque[float] = deque()
        self.token_times: deque[Tuple[float, int]] = deque()

    def _cleanup(self, now: float) -> None:
        while self.req_times and now - self.req_times[0] > 60:
            self.req_times.popleft()
        while self.token_times and now - self.token_times[0][0] > 60:
            self.token_times.popleft()

    def can_make_request(self, tokens: int) -> bool:
        now = time.monotonic()
        self._cleanup(now)
        if len(self.req_times) >= self.rpm:
            return False
        if sum(t for _, t in self.token_times) + tokens > self.tpm:
            return False
        return True

    def record(self, tokens: int) -> None:
        now = time.monotonic()
        self.req_times.append(now)
        self.token_times.append((now, tokens))
        self._cleanup(now)


chat_manager = ChatManager(conf.session_ttl)

model_1 = conf.model_1
error_info = conf.error_info
before_generate_info = conf.before_generate_info

search_tool = {"google_search": {}}

logger = logging.getLogger(__name__)

rate_limiter = RateLimiter(conf.gemini_rpm_limit, conf.gemini_tpm_limit)

client: Optional[genai.Client] = None

# Cache model metadata to avoid repeated requests
_model_cache: Dict[str, types.Model] = {}


async def _get_model_info(model: str) -> types.Model:
    """Return model info using cached data when available."""
    info = _model_cache.get(model)
    if info is None:
        client = _ensure_client()
        info = await client.aio.models.get(model=model)
        _model_cache[model] = info
    return info


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
    last_action = time.monotonic()
    try:
        sent_message = await bot.reply_to(
            message,
            before_generate_info,
        )
        await bot.send_chat_action(message.chat.id, "typing")
        
        chat = chat_manager.get_chat(str(message.from_user.id), model=model_type)
        chat_manager.cleanup()

        model_info = await _get_model_info(model_type)
        history = chat.get_history()
        contents = history + (query if isinstance(query, list) else [query])
        tokens = await client.aio.models.count_tokens(
            model=model_type,
            contents=contents,
        )
        if (
            tokens.total_tokens
            and tokens.total_tokens > model_info.input_token_limit
        ):
            await safe_edit(
                bot,
                sent_message,
                "Prompt too long for model. Please shorten your message.",
            )
            return
        if not rate_limiter.can_make_request(tokens.total_tokens or 0):
            await safe_edit(
                bot,
                sent_message,
                "Rate limit reached. Please wait.",
            )
            return

        response = await chat.send_message_stream(query)

        full_response = ""
        last_update = time.monotonic()
        update_interval = conf.streaming_update_interval
        last_candidate: types.Candidate | None = None
        usage_tokens: int | None = None

        messages = [sent_message]
        buffers = [""]

        async for chunk in response:
            if getattr(chunk, "text", ""):
                full_response += chunk.text
                buffers[-1] += chunk.text
                while len(buffers[-1]) > MAX_MESSAGE_LENGTH:
                    part = buffers[-1][:MAX_MESSAGE_LENGTH]
                    leftover = buffers[-1][MAX_MESSAGE_LENGTH:]
                    await safe_edit(bot, messages[-1], part)
                    buffers[-1] = part
                    new_msg = await bot.send_message(
                        sent_message.chat.id,
                        escape(leftover) if leftover else "\u200b",
                        parse_mode="MarkdownV2",
                    )
                    messages.append(new_msg)
                    buffers.append(leftover)
                if time.monotonic() - last_update >= update_interval:
                    await safe_edit(bot, messages[-1], buffers[-1])
                    last_update = time.monotonic()
            if time.monotonic() - last_action >= 4:
                await bot.send_chat_action(message.chat.id, "typing")
                last_action = time.monotonic()
            if chunk.candidates:
                last_candidate = chunk.candidates[0]
            if chunk.usage_metadata and chunk.usage_metadata.total_token_count:
                usage_tokens = chunk.usage_metadata.total_token_count

        sources = _format_sources(last_candidate) if last_candidate else None
        final_text = escape(full_response)
        if sources:
            final_text += "\n\n" + sources

        chunks = split_text(final_text)
        for i, chunk in enumerate(chunks):
            if i < len(messages):
                await safe_edit(
                    bot,
                    messages[i],
                    chunk,
                    markdown=True,
                    escape_text=False,
                )
            else:
                msg = await bot.send_message(
                    sent_message.chat.id,
                    chunk,
                    parse_mode="MarkdownV2",
                )
                messages.append(msg)
        # remove any extra placeholder messages created during streaming
        for msg in messages[len(chunks):]:
            try:
                await bot.delete_message(msg.chat.id, msg.message_id)
            except Exception:
                pass

        if usage_tokens is not None:
            rate_limiter.record(usage_tokens)

    except genai.errors.APIError as exc:  # pragma: no cover - API issues
        logger.exception("Gemini API error")
        msg = f"{error_info}\nAPI error {exc.code}: {exc.message}"
        if sent_message:
            await safe_edit(bot, sent_message, msg, markdown=False)
        else:
            await bot.reply_to(message, msg)
    except Exception as exc:  # pragma: no cover - network issues
        logger.exception("Gemini stream failed")
        if sent_message:
            await safe_edit(
                bot,
                sent_message,
                f"{error_info}\nError details: {exc}",
                markdown=False,
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


async def gemini_pdf_stream(
    bot: TeleBot,
    message: Message,
    pdf_bytes: bytes,
    prompt: str,
    model_type: str,
) -> None:
    """Stream a response based on a PDF file and prompt."""

    pdf_part = types.Part.from_bytes(
        data=pdf_bytes,
        mime_type="application/pdf",
    )
    await gemini_stream(bot, message, [pdf_part, prompt], model_type)


async def gemini_audio_stream(
    bot: TeleBot,
    message: Message,
    audio_bytes: bytes,
    mime_type: str,
    prompt: str,
    model_type: str,
) -> None:
    """Stream a response based on an audio clip and prompt."""

    audio_part = types.Part.from_bytes(
        data=audio_bytes,
        mime_type=mime_type,
    )
    await gemini_stream(bot, message, [prompt, audio_part], model_type)
