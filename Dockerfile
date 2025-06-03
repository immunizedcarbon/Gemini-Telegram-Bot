FROM python:3.12-slim

# Avoid writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies first for better caching
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home bot
USER bot

# Environment variables for runtime configuration
ENV TELEGRAM_BOT_API_KEY="" \
    GEMINI_API_KEYS=""

CMD ["python", "main.py"]
