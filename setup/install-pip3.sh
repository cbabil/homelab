#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail

# Install Pip3
apt-get update
apt-get install -y python3-pip

# Verify installation
pip3 --version
