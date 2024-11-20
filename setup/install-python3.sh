#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail

# Install Python3
apt-get update
apt-get install -y python3 python3-pip

# Verify installation
python3 --version
pip3 --version
