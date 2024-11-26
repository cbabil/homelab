#!/bin/bash

# Install prerequisites
apt-get update || error "Failed to update package list"
apt-get install -y curl || error "Failed to install prerequisites"

# Download and execute Docker's convenience script
curl -fsSL https://get.docker.com -o get-docker.sh || error "Failed to download Docker installation script"
sh get-docker.sh || error "Failed to execute Docker installation script"
rm get-docker.sh

# Add current user to docker group
usermod -aG docker $USER || error "Failed to add user to docker group"

# Verify installation
if command -v docker >/dev/null 2>&1; then
    success "Docker has been installed"
    docker --version
else
    error "Docker installation failed"
fi