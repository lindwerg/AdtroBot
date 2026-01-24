FROM python:3.11-slim

# Install system dependencies (including Cairo for SVG rendering and Node.js)
RUN apt-get update && apt-get install -y \
    libsqlite3-0 \
    libcairo2 \
    libcairo2-dev \
    pkg-config \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
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

# Build admin frontend
WORKDIR /app/admin-frontend
RUN npm ci && npm run build

# Return to app directory
WORKDIR /app

# Run migrations and start app
CMD alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
