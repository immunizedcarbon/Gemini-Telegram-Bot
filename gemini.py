import google.generai as genai
from config import settings
from typing import List, Tuple, Any


def init_client(api_key: str) -> None:
    genai.configure(api_key=api_key)


async def generate_response(prompt: Any, history: List[dict]) -> Tuple[str, List[dict]]:
    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        safety_settings=settings.gemini_safety_settings,
        system_instruction=settings.system_instruction,
    )
    chat = model.start_chat(history=history)

    tools = [genai.protos.Tool(google_search=genai.protos.GoogleSearch())] if settings.enable_tools else None
    config = genai.types.GenerationConfig(tools=tools) if tools else None

    response = await chat.send_message_async(prompt, generation_config=config, stream=True)

    full_response = ""
    async for chunk in response:
        if chunk.text:
            full_response += chunk.text

    new_history = chat.history
    return full_response, new_history


def _parts_from_file(data: bytes, mime_type: str, prompt: str) -> list:
    return [prompt, {"mime_type": mime_type, "data": data}]


async def generate_from_pdf(pdf_bytes: bytes, prompt: str, history: List[dict]) -> Tuple[str, List[dict]]:
    parts = _parts_from_file(pdf_bytes, "application/pdf", prompt)
    return await generate_response(parts, history)


async def generate_from_image(image_bytes: bytes, mime_type: str, prompt: str, history: List[dict]) -> Tuple[str, List[dict]]:
    parts = _parts_from_file(image_bytes, mime_type, prompt)
    return await generate_response(parts, history)


async def generate_from_audio(audio_bytes: bytes, mime_type: str, prompt: str, history: List[dict]) -> Tuple[str, List[dict]]:
    parts = [prompt, {"mime_type": mime_type, "data": audio_bytes}]
    return await generate_response(parts, history)


async def generate_from_youtube(video_url: str, prompt: str, history: List[dict]) -> Tuple[str, List[dict]]:
    part = {"file_uri": video_url}
    parts = [part, prompt]
    return await generate_response(parts, history)
