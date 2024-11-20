#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail

# Install Ansible Semaphore
docker pull semaphoreui/semaphore:latest

# Create necessary directories
mkdir -p /opt/docker/semaphore/config
mkdir -p /opt/docker/semaphore/inventory
mkdir -p /opt/docker/semaphore/authorized-keys

# Run Semaphore container
docker run -d --name semaphore \
  -p 3000:3000 \
  -v /opt/docker/semaphore/config:/etc/semaphore \
  -v /opt/docker/semaphore/inventory:/inventory \
  -v /opt/docker/semaphore/authorized-keys:/authorized-keys \
  semaphoreui/semaphore:latest

# Verify installation
docker ps | grep semaphore
