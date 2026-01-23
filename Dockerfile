FROM python:3.11-slim

# Install system dependencies (including Cairo for SVG rendering)
RUN apt-get update && apt-get install -y \
    libsqlite3-0 \
    libcairo2 \
    libcairo2-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

# Run migrations and start app
CMD alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
