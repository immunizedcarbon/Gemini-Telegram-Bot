# Gemini Telegram Bot

A Telegram bot that uses Google's Gemini API to chat. The bot supports multi-turn conversations and streaming responses.

## Features

- **Chat model**: `gemini-2.5-flash-preview-05-20`.
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
2. Run the bot. Tokens can be provided either as command line arguments or via environment variables. A `.env` file can also be used:
   ```bash
   TELEGRAM_BOT_API_KEY=<telegram token> GEMINI_API_KEYS=<gemini key> python main.py
   ```
   Create a `.env` file if you prefer storing credentials there:
   ```env
   TELEGRAM_BOT_API_KEY=<your telegram token>
   GEMINI_API_KEYS=<your gemini key>
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
- `/clear` – clear conversation history.

In private chats you can also send text directly without a command.

## License

This project is licensed under the [Apache 2.0 License](LICENSE).
