# Gemini Telegram Bot

A Telegram bot that uses Google's Gemini API to chat, generate images and edit pictures. The bot supports multi-turn conversations and streaming responses.

## Features

- **Two chat models**: `gemini-2.5-flash-preview-04-17` and `gemini-2.5-pro-preview-05-06`.
- **Image generation and editing** using `gemini-2.0-flash-preview-image-generation`.
- **Streaming replies** so users see partial answers as they arrive.
- **Multi-turn conversations** tracked per user.
- Works in **private chats** or **groups**.

## Requirements

- Python 3.12+
- Telegram bot token ([BotFather](https://t.me/BotFather))
- Google Gemini API key ([Google AI Studio](https://makersuite.google.com/app/apikey))

Required Python packages are listed in [`requirements.txt`](requirements.txt).

## Running locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the bot, passing your tokens:
   ```bash
   python main.py <TELEGRAM_BOT_API_KEY> <GEMINI_API_KEY>
   ```

## Docker

A `Dockerfile` is included.

Build and run your own image:
```bash
docker build -t gemini-bot .
docker run -d --restart=always \
  -e TELEGRAM_BOT_API_KEY=<your telegram token> \
  -e GEMINI_API_KEYS=<your gemini key> \
  gemini-bot
```

## Commands

- `/start` – greeting message.
- `/gemini <text>` – ask using the flash model.
- `/gemini_pro <text>` – ask using the pro model.
- `/draw <prompt>` – generate an image.
- `/edit <instructions>` (with a photo) – edit the attached image.
- `/clear` – clear conversation history.
- `/switch` – switch default model in private chat.

In private chats you can also send text directly without a command. Use `/switch` to toggle between the two chat models.

## License

This project is licensed under the [Apache 2.0 License](LICENSE).
