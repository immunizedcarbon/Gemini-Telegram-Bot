from __future__ import annotations

import re
import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from md2tgmd import escape

import gemini
from config import settings

logger = logging.getLogger(__name__)

YOUTUBE_RE = re.compile(r"https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[^\s]+")
MAX_MESSAGE_LENGTH = 4096


def _split_text(text: str) -> list[str]:
    chunks: list[str] = []
    while len(text) > MAX_MESSAGE_LENGTH:
        split_at = text.rfind("\n", 0, MAX_MESSAGE_LENGTH)
        if split_at == -1:
            split_at = MAX_MESSAGE_LENGTH
        chunks.append(text[:split_at])
        text = text[split_at:]
    chunks.append(text)
    return chunks


def _extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s]+", text)


def _remove_urls(text: str) -> str:
    return re.sub(r"https?://[^\s]+", "", text).strip()


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in settings.authorized_user_ids:
        await update.message.reply_text('❌ Access denied')
        return
    text = (
        "Ich kann mit dir chatten, Bilder, PDFs und Audiodateien verstehen. "
        "Sende mir einfach etwas. Nutze /clear, um den Verlauf zu löschen."
    )
    await update.message.reply_text(escape(text), parse_mode=ParseMode.MARKDOWN_V2)


async def clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in settings.authorized_user_ids:
        await update.message.reply_text('❌ Access denied')
        return
    context.user_data.clear()
    await update.message.reply_text('History cleared.')


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in settings.authorized_user_ids:
        await update.message.reply_text('❌ Access denied')
        return

    message_text = update.message.text.strip()

    pending_url = context.user_data.pop('pending_youtube', None)
    youtube_match = YOUTUBE_RE.search(message_text)

    if pending_url and not youtube_match:
        url = pending_url
        prompt = _remove_urls(message_text)
        history = context.user_data.get('history', [])
        response, new_history = await gemini.generate_from_youtube(url, prompt or message_text, history)
        context.user_data['history'] = new_history
    elif youtube_match:
        url = youtube_match.group(0)
        caption = (message_text[:youtube_match.start()] + message_text[youtube_match.end():]).strip()
        if not caption:
            context.user_data['pending_youtube'] = url
            await update.message.reply_text('Was soll ich mit diesem Video tun?')
            return
        prompt = _remove_urls(caption)
        history = context.user_data.get('history', [])
        response, new_history = await gemini.generate_from_youtube(url, prompt, history)
        context.user_data['history'] = new_history
    else:
        prompt = _remove_urls(message_text)
        history = context.user_data.get('history', [])
        response, new_history = await gemini.generate_response(prompt or message_text, history)
        context.user_data['history'] = new_history

    for part in _split_text(escape(response)):
        await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN_V2)


async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in settings.authorized_user_ids:
        await update.message.reply_text('❌ Access denied')
        return

    file = None
    mime_type = 'image/jpeg'
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        mime_type = 'image/jpeg'
    elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith('image/'):
        file = await update.message.document.get_file()
        mime_type = update.message.document.mime_type
    if not file:
        return
    image_bytes = await file.download_as_bytearray()
    caption = update.message.caption.strip() if update.message.caption else 'Beschreibe dieses Bild.'
    history = context.user_data.get('history', [])
    response, new_history = await gemini.generate_from_image(bytes(image_bytes), mime_type, caption, history)
    context.user_data['history'] = new_history
    for part in _split_text(escape(response)):
        await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN_V2)


async def pdf_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in settings.authorized_user_ids:
        await update.message.reply_text('❌ Access denied')
        return
    if not update.message.document or update.message.document.mime_type != 'application/pdf':
        return
    file = await update.message.document.get_file()
    pdf_bytes = await file.download_as_bytearray()
    caption = update.message.caption.strip() if update.message.caption else 'Fasse dieses Dokument zusammen.'
    history = context.user_data.get('history', [])
    response, new_history = await gemini.generate_from_pdf(bytes(pdf_bytes), caption, history)
    context.user_data['history'] = new_history
    for part in _split_text(escape(response)):
        await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN_V2)


async def audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in settings.authorized_user_ids:
        await update.message.reply_text('❌ Access denied')
        return

    file = None
    mime_type = None
    if update.message.voice:
        file = await update.message.voice.get_file()
        mime_type = 'audio/ogg'
    elif update.message.audio:
        file = await update.message.audio.get_file()
        mime_type = update.message.audio.mime_type or 'audio/mpeg'
    elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith('audio/'):
        file = await update.message.document.get_file()
        mime_type = update.message.document.mime_type
    if not file or not mime_type:
        return
    audio_bytes = await file.download_as_bytearray()
    caption = update.message.caption.strip() if update.message.caption else 'Beschreibe dieses Audio.'
    history = context.user_data.get('history', [])
    response, new_history = await gemini.generate_from_audio(bytes(audio_bytes), mime_type, caption, history)
    context.user_data['history'] = new_history
    for part in _split_text(escape(response)):
        await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN_V2)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text('Ein Fehler ist aufgetreten.')
