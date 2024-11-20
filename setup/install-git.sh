#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail

# Install Git
apt-get update
apt-get install -y git

# Verify installation
git --version
