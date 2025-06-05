FROM python:3.12-slim

# Avoid writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies first for better caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user and transfer ownership
RUN useradd --create-home bot && chown -R bot:bot /app
USER bot

# Environment variables will be managed by pydantic-settings
# The CMD will be updated later when main.py is refactored
CMD ["python", "main.py"]
