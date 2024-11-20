#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail

# Function to install MOTD
install_motd() {
    echo "Installing HomeLab MOTD..."
    # Add your MOTD installation logic here
    # For example, you might want to copy a custom MOTD script to /etc/motd.sh
    cp /path/to/custom/motd.sh /etc/motd.sh
    chmod +x /etc/motd.sh

    # Ensure the MOTD script is executed on login
    if ! grep -q '/etc/motd.sh' /etc/profile; then
        echo '/etc/motd.sh' >> /etc/profile
    fi

    echo "HomeLab MOTD installed successfully."
}

install_motd 