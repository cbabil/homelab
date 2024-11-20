#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail

# Install Docker Compose
apt-get update
apt-get install -y docker-compose-plugin

# Verify installation
docker-compose --version
