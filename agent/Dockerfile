FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev deps, frozen from lock file)
RUN uv sync --frozen --no-dev --no-install-project

# Copy agent code
COPY src/ ./src/

# Data volume for token persistence
VOLUME /data

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["uv", "run", "--no-dev", "python", "-m", "src.main"]
