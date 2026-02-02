# Tomo Development Container
# Includes Python 3.11, Node.js 20, and development tools

FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g yarn

# Install additional system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    openssh-client \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python development tools globally
RUN pip install --no-cache-dir \
    black \
    flake8 \
    mypy \
    pytest \
    pytest-asyncio \
    pytest-cov \
    ruff

# Create workspace directory
WORKDIR /workspaces/tomo

# Set up non-root user (vscode user is created by base image)
USER vscode

# Set Python path for the backend
ENV PYTHONPATH=/workspaces/tomo/backend/src
ENV PATH="/home/vscode/.local/bin:${PATH}"
