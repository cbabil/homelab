#!/bin/bash
# Post-create script for Tomo development container
# Installs all dependencies and sets up the development environment

set -e

echo "========================================"
echo "Setting up Tomo development environment..."
echo "========================================"

# Install backend dependencies
echo ""
echo "Installing backend Python dependencies..."
cd /workspaces/tomo/backend
pip install -e ".[dev]" 2>/dev/null || pip install -r requirements.txt

# Create data directory if it doesn't exist
mkdir -p /workspaces/tomo/backend/data

# Install frontend dependencies
echo ""
echo "Installing frontend Node.js dependencies..."
cd /workspaces/tomo/frontend
yarn install

# Install CLI dependencies (if exists)
if [ -d "/workspaces/tomo/cli" ]; then
    echo ""
    echo "Installing CLI dependencies..."
    cd /workspaces/tomo/cli
    yarn install 2>/dev/null || true
fi

# Create .env file from template if it doesn't exist
if [ ! -f "/workspaces/tomo/.env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cat > /workspaces/tomo/.env << 'EOF'
# Tomo Environment Variables
# SECURITY: Change these values before using in any non-development environment!

# Master password for encrypting sensitive data (server credentials, etc.)
TOMO_MASTER_PASSWORD=dev_master_password_change_me

# Salt for additional encryption security
TOMO_SALT=dev_salt_change_me_in_production

# JWT secret key for session tokens
JWT_SECRET_KEY=dev_jwt_secret_change_me_in_production

# Optional: Allowed CORS origins (comma-separated)
# ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
EOF
    echo "WARNING: Default development credentials created in .env"
    echo "         Change these values before deploying to production!"
fi

echo ""
echo "========================================"
echo "Development environment setup complete!"
echo "========================================"
echo ""
echo "Quick start commands:"
echo "  Backend:  cd backend && python src/main.py"
echo "  Frontend: cd frontend && yarn dev"
echo "  Tests:    cd backend && pytest"
echo "            cd frontend && yarn test"
echo ""
echo "Access the application at: http://localhost:3001"
echo ""
