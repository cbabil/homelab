#!/bin/bash
set -e

echo "Setting up Homelab Assistant development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create data directory
mkdir -p data

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
if command -v yarn &> /dev/null; then
    yarn install
else
    npm install
fi
cd ..

# Install backend dependencies (if running locally)
echo "Installing backend dependencies..."
cd backend
if command -v python3 &> /dev/null; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi
cd ..

echo "Setup complete! You can now run:"
echo "  docker-compose -f docker-compose.dev.yml up"
echo "Or for local development:"
echo "  cd frontend && yarn dev"
echo "  cd backend && source venv/bin/activate && python -m uvicorn src.main:app --reload"