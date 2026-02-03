# Tomo Development Container
# Includes Python 3.12, Node.js 20, uv, and bun

FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Install Node.js 20 and bun
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && curl -fsSL https://bun.sh/install | bash \
    && mv /root/.bun/bin/bun /usr/local/bin/

# Install uv for Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/

# Install additional system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    openssh-client \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create workspace directory
WORKDIR /workspaces/tomo

# Set up non-root user (vscode user is created by base image)
USER vscode

# Set Python path for the backend
ENV PYTHONPATH=/workspaces/tomo/backend/src
ENV PATH="/home/vscode/.local/bin:${PATH}"
