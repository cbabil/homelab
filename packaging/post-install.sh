#!/bin/bash
# Tomo - Post Installation Script
# This script is called after RPM installation
# It can also be run manually for setup/repair

set -e

echo "Setting up Tomo..."

# Create tomo user and group if not exists
if ! getent group tomo >/dev/null; then
    groupadd -r tomo
    echo "  Created tomo group"
fi

if ! getent passwd tomo >/dev/null; then
    useradd -r -g tomo \
        -d /var/lib/tomo \
        -s /sbin/nologin \
        -c "Tomo" tomo
    echo "  Created tomo user"
fi

# Create directories
mkdir -p /var/lib/tomo/catalog
mkdir -p /var/lib/tomo/backups
mkdir -p /var/log/tomo

# Set ownership
chown -R tomo:tomo /var/lib/tomo
chown -R tomo:tomo /var/log/tomo

# Set permissions
chmod 750 /var/lib/tomo
chmod 750 /var/log/tomo

# Set config file permissions
if [ -f /etc/tomo/config.yaml ]; then
    chown tomo:tomo /etc/tomo/config.yaml
    chmod 640 /etc/tomo/config.yaml
fi

# Create virtual environment if not exists
if [ ! -d /opt/tomo/venv ]; then
    echo "  Creating Python virtual environment..."
    python3 -m venv /opt/tomo/venv
fi

# Install/upgrade Python dependencies
echo "  Installing Python dependencies..."
/opt/tomo/venv/bin/pip install --upgrade pip -q
/opt/tomo/venv/bin/pip install -r /opt/tomo/requirements.txt -q

# Initialize database if not exists
if [ ! -f /var/lib/tomo/tomo.db ]; then
    echo "  Initializing database..."
    sudo -u tomo DATA_DIRECTORY=/var/lib/tomo \
        /opt/tomo/venv/bin/python \
        /opt/tomo/cli.py init-db 2>/dev/null || true
fi

# Reload systemd
systemctl daemon-reload

# Reload nginx if running
if systemctl is-active --quiet nginx; then
    systemctl reload nginx
fi

echo ""
echo "Tomo setup complete!"
echo ""
echo "Next steps:"
echo "  1. Create admin user:  tomo create-admin"
echo "  2. Start service:      systemctl start tomo"
echo "  3. Enable on boot:     systemctl enable tomo"
echo "  4. Check status:       systemctl status tomo"
echo "  5. View logs:          journalctl -u tomo -f"
echo ""
echo "Access the web interface at: http://localhost"
echo ""
