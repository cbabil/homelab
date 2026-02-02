#!/bin/bash
#
# Tomo - Installation Script
#
# This script installs Tomo on bare-metal Linux servers.
# Supports: Ubuntu/Debian, RHEL/CentOS/Fedora/Rocky Linux, Arch Linux
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/cbabil/tomo/main/install.sh | bash
#   or
#   ./install.sh [--uninstall] [--upgrade] [--version X.Y.Z]
#

set -e

# Configuration
INSTALL_DIR="/opt/tomo"
DATA_DIR="/var/lib/tomo"
LOG_DIR="/var/log/tomo"
CONFIG_DIR="/etc/tomo"
STATIC_DIR="/var/www/tomo"
SERVICE_USER="tomo"
SERVICE_GROUP="tomo"
REPO_URL="https://github.com/cbabil/tomo"
VERSION="${VERSION:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root (sudo)"
        exit 1
    fi
}

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
        OS_FAMILY=$ID_LIKE
    elif [ -f /etc/redhat-release ]; then
        OS="rhel"
    elif [ -f /etc/debian_version ]; then
        OS="debian"
    else
        log_error "Unsupported operating system"
        exit 1
    fi
    log_info "Detected OS: $OS ($OS_VERSION)"
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."

    case $OS in
        ubuntu|debian)
            apt-get update -qq
            apt-get install -y -qq \
                python3 python3-pip python3-venv \
                nodejs npm \
                nginx \
                git curl wget \
                sqlite3
            # Install yarn
            npm install -g yarn
            ;;
        fedora|rhel|centos|rocky|almalinux)
            if command -v dnf &> /dev/null; then
                PKG_MGR="dnf"
            else
                PKG_MGR="yum"
            fi
            $PKG_MGR install -y -q \
                python3 python3-pip python3-virtualenv \
                nodejs npm \
                nginx \
                git curl wget \
                sqlite
            npm install -g yarn
            ;;
        arch|manjaro)
            pacman -Syu --noconfirm \
                python python-pip python-virtualenv \
                nodejs npm yarn \
                nginx \
                git curl wget \
                sqlite
            ;;
        *)
            log_error "Unsupported OS: $OS"
            log_info "Please install manually: python3, nodejs, npm, yarn, nginx, git, sqlite"
            exit 1
            ;;
    esac

    log_success "System dependencies installed"
}

# Create service user
create_user() {
    log_info "Creating service user..."

    if ! getent group $SERVICE_GROUP >/dev/null 2>&1; then
        groupadd -r $SERVICE_GROUP
    fi

    if ! getent passwd $SERVICE_USER >/dev/null 2>&1; then
        useradd -r -g $SERVICE_GROUP \
            -d $DATA_DIR \
            -s /sbin/nologin \
            -c "Tomo" $SERVICE_USER
    fi

    log_success "Service user created"
}

# Create directories
create_directories() {
    log_info "Creating directories..."

    mkdir -p $INSTALL_DIR
    mkdir -p $DATA_DIR/catalog
    mkdir -p $DATA_DIR/backups
    mkdir -p $LOG_DIR
    mkdir -p $CONFIG_DIR
    mkdir -p $STATIC_DIR

    chown -R $SERVICE_USER:$SERVICE_GROUP $DATA_DIR
    chown -R $SERVICE_USER:$SERVICE_GROUP $LOG_DIR
    chmod 750 $DATA_DIR
    chmod 750 $LOG_DIR

    log_success "Directories created"
}

# Download and install application
install_application() {
    log_info "Downloading Tomo..."

    TEMP_DIR=$(mktemp -d)
    cd $TEMP_DIR

    if [ "$VERSION" = "latest" ]; then
        # Get latest release
        DOWNLOAD_URL=$(curl -s https://api.github.com/repos/cbabil/tomo/releases/latest | \
            grep "tarball_url" | cut -d '"' -f 4)
        if [ -z "$DOWNLOAD_URL" ]; then
            # Fall back to main branch
            DOWNLOAD_URL="$REPO_URL/archive/refs/heads/main.tar.gz"
        fi
    else
        DOWNLOAD_URL="$REPO_URL/archive/refs/tags/v$VERSION.tar.gz"
    fi

    log_info "Downloading from: $DOWNLOAD_URL"
    curl -fsSL "$DOWNLOAD_URL" -o tomo.tar.gz
    tar -xzf tomo.tar.gz --strip-components=1

    # Install backend
    log_info "Installing backend..."
    cp -r backend/src $INSTALL_DIR/backend
    cp backend/requirements.txt $INSTALL_DIR/

    # Create and activate virtual environment
    python3 -m venv $INSTALL_DIR/venv
    $INSTALL_DIR/venv/bin/pip install --upgrade pip -q
    $INSTALL_DIR/venv/bin/pip install -r $INSTALL_DIR/requirements.txt -q

    # Build and install frontend
    log_info "Building frontend..."
    cd frontend
    yarn install --frozen-lockfile --silent
    yarn build
    cp -r dist/* $STATIC_DIR/
    cd ..

    # Cleanup
    cd /
    rm -rf $TEMP_DIR

    log_success "Application installed"
}

# Configure nginx
configure_nginx() {
    log_info "Configuring nginx..."

    cat > /etc/nginx/conf.d/tomo.conf << 'NGINX_CONF'
upstream tomo_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Frontend static files
    root /var/www/tomo;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # MCP endpoint - proxy to backend
    location /mcp {
        proxy_pass http://tomo_backend/mcp;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE support
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        chunked_transfer_encoding off;
    }

    # Health check
    location /health {
        proxy_pass http://tomo_backend/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_CONF

    # Remove default nginx site if exists
    rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
    rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true

    # Test nginx config
    nginx -t

    log_success "Nginx configured"
}

# Create systemd service
create_service() {
    log_info "Creating systemd service..."

    cat > /etc/systemd/system/tomo.service << SERVICE
[Unit]
Description=Tomo Backend
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR
Environment="PYTHONPATH=$INSTALL_DIR/backend"
Environment="DATA_DIRECTORY=$DATA_DIR"
Environment="LOG_DIRECTORY=$LOG_DIR"
EnvironmentFile=-$CONFIG_DIR/environment
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/backend/main.py
Restart=always
RestartSec=5

# Security hardening
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$DATA_DIR $LOG_DIR

[Install]
WantedBy=multi-user.target
SERVICE

    systemctl daemon-reload

    log_success "Systemd service created"
}

# Create configuration file
create_config() {
    log_info "Creating configuration..."

    if [ ! -f $CONFIG_DIR/environment ]; then
        # Generate random secrets
        MASTER_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
        SALT=$(openssl rand -base64 16 | tr -d '/+=' | head -c 16)
        JWT_SECRET=$(openssl rand -base64 48 | tr -d '/+=' | head -c 48)

        cat > $CONFIG_DIR/environment << CONFIG
# Tomo Configuration
# Generated on $(date)

# SECURITY: These are auto-generated secrets. Keep them safe!
TOMO_MASTER_PASSWORD=$MASTER_PASSWORD
TOMO_SALT=$SALT
JWT_SECRET_KEY=$JWT_SECRET

# Optional: Comma-separated list of allowed CORS origins
# ALLOWED_ORIGINS=http://localhost:3000
CONFIG

        chmod 600 $CONFIG_DIR/environment
        chown $SERVICE_USER:$SERVICE_GROUP $CONFIG_DIR/environment
    fi

    log_success "Configuration created"
}

# Start services
start_services() {
    log_info "Starting services..."

    systemctl enable nginx
    systemctl restart nginx

    systemctl enable tomo
    systemctl start tomo

    log_success "Services started"
}

# Print completion message
print_completion() {
    echo ""
    echo "=============================================="
    echo -e "${GREEN}Tomo installed successfully!${NC}"
    echo "=============================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "  1. Create an admin account:"
    echo "     sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/python \\"
    echo "       $INSTALL_DIR/backend/cli.py admin create -u admin -p YourPassword"
    echo ""
    echo "  2. Access the web interface:"
    echo "     http://$(hostname -I | awk '{print $1}')"
    echo ""
    echo "  3. Check service status:"
    echo "     systemctl status tomo"
    echo ""
    echo "  4. View logs:"
    echo "     journalctl -u tomo -f"
    echo ""
    echo "Configuration file: $CONFIG_DIR/environment"
    echo "Data directory:     $DATA_DIR"
    echo "Log directory:      $LOG_DIR"
    echo ""
}

# Uninstall function
uninstall() {
    log_info "Uninstalling Tomo..."

    # Stop services
    systemctl stop tomo 2>/dev/null || true
    systemctl disable tomo 2>/dev/null || true

    # Remove files
    rm -f /etc/systemd/system/tomo.service
    rm -f /etc/nginx/conf.d/tomo.conf
    rm -rf $INSTALL_DIR
    rm -rf $STATIC_DIR

    systemctl daemon-reload
    systemctl restart nginx 2>/dev/null || true

    log_warn "Data and configuration preserved at:"
    log_warn "  $DATA_DIR"
    log_warn "  $CONFIG_DIR"
    log_warn "Remove manually if no longer needed."

    log_success "Uninstallation complete"
}

# Main installation
main() {
    echo ""
    echo "=============================================="
    echo "  Tomo Installer"
    echo "=============================================="
    echo ""

    # Parse arguments
    for arg in "$@"; do
        case $arg in
            --uninstall)
                check_root
                uninstall
                exit 0
                ;;
            --upgrade)
                UPGRADE=true
                ;;
            --version=*)
                VERSION="${arg#*=}"
                ;;
        esac
    done

    check_root
    detect_os

    if [ "$UPGRADE" = true ] && [ -d "$INSTALL_DIR" ]; then
        log_info "Upgrading existing installation..."
        systemctl stop tomo 2>/dev/null || true
    fi

    install_dependencies
    create_user
    create_directories
    install_application
    configure_nginx
    create_service
    create_config
    start_services
    print_completion
}

# Run main function
main "$@"
