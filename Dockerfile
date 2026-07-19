FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Copy source code (will be overridden by volume mount in dev)
COPY . .

EXPOSE 8000

# Default command - can be overridden
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
