#!/bin/bash
# Post-installation script for homelab-assistant

set -e

# Create homelab user and group
if ! getent group homelab >/dev/null; then
    groupadd -r homelab
    echo "Created homelab group"
fi

if ! getent passwd homelab >/dev/null; then
    useradd -r -g homelab -d /var/lib/homelab-assistant -s /sbin/nologin -c "Homelab Assistant" homelab
    echo "Created homelab user"
fi

# Create directories
mkdir -p /var/lib/homelab-assistant/catalog
mkdir -p /var/log/homelab-assistant

# Set ownership
chown -R homelab:homelab /var/lib/homelab-assistant
chown -R homelab:homelab /var/log/homelab-assistant

# Set permissions
chmod 750 /var/lib/homelab-assistant
chmod 750 /var/log/homelab-assistant

# Initialize database if not exists
if [ ! -f /var/lib/homelab-assistant/homelab.db ]; then
    echo "Initializing database..."
    sudo -u homelab python3 /opt/homelab-assistant/cli.py init-db
fi

# Reload systemd
systemctl daemon-reload

echo "Post-installation complete"
echo ""
echo "To start the service:"
echo "  systemctl start homelab-assistant"
echo ""
echo "To create an admin user:"
echo "  homelab-assistant create-admin"
