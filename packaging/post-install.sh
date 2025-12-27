#!/bin/bash
# Homelab Assistant - Post Installation Script
# This script is called after RPM installation
# It can also be run manually for setup/repair

set -e

echo "Setting up Homelab Assistant..."

# Create homelab user and group if not exists
if ! getent group homelab >/dev/null; then
    groupadd -r homelab
    echo "  Created homelab group"
fi

if ! getent passwd homelab >/dev/null; then
    useradd -r -g homelab \
        -d /var/lib/homelab-assistant \
        -s /sbin/nologin \
        -c "Homelab Assistant" homelab
    echo "  Created homelab user"
fi

# Create directories
mkdir -p /var/lib/homelab-assistant/catalog
mkdir -p /var/lib/homelab-assistant/backups
mkdir -p /var/log/homelab-assistant

# Set ownership
chown -R homelab:homelab /var/lib/homelab-assistant
chown -R homelab:homelab /var/log/homelab-assistant

# Set permissions
chmod 750 /var/lib/homelab-assistant
chmod 750 /var/log/homelab-assistant

# Set config file permissions
if [ -f /etc/homelab-assistant/config.yaml ]; then
    chown homelab:homelab /etc/homelab-assistant/config.yaml
    chmod 640 /etc/homelab-assistant/config.yaml
fi

# Create virtual environment if not exists
if [ ! -d /opt/homelab-assistant/venv ]; then
    echo "  Creating Python virtual environment..."
    python3 -m venv /opt/homelab-assistant/venv
fi

# Install/upgrade Python dependencies
echo "  Installing Python dependencies..."
/opt/homelab-assistant/venv/bin/pip install --upgrade pip -q
/opt/homelab-assistant/venv/bin/pip install -r /opt/homelab-assistant/requirements.txt -q

# Initialize database if not exists
if [ ! -f /var/lib/homelab-assistant/homelab.db ]; then
    echo "  Initializing database..."
    sudo -u homelab DATA_DIRECTORY=/var/lib/homelab-assistant \
        /opt/homelab-assistant/venv/bin/python \
        /opt/homelab-assistant/cli.py init-db 2>/dev/null || true
fi

# Reload systemd
systemctl daemon-reload

# Reload nginx if running
if systemctl is-active --quiet nginx; then
    systemctl reload nginx
fi

echo ""
echo "Homelab Assistant setup complete!"
echo ""
echo "Next steps:"
echo "  1. Create admin user:  homelab-assistant create-admin"
echo "  2. Start service:      systemctl start homelab-assistant"
echo "  3. Enable on boot:     systemctl enable homelab-assistant"
echo "  4. Check status:       systemctl status homelab-assistant"
echo "  5. View logs:          journalctl -u homelab-assistant -f"
echo ""
echo "Access the web interface at: http://localhost"
echo ""
