#!/bin/bash

# Install Docker Compose
apt-get update || error "Failed to update package list"
apt-get install -y docker-compose-plugin || error "Failed to install Docker Compose"

# Verify installation
if command -v docker compose >/dev/null 2>&1; then
    success "Docker Compose has been installed"
    docker compose version
else
    error "Docker Compose installation failed"
fi
