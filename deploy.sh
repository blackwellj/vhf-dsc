#!/bin/bash
# Deploy DSC Monitor to server

set -e

echo "=== DSC Monitor Deployment ==="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

# Create directories
mkdir -p dsc_messages logs

# Build and start
echo "Building and starting DSC Monitor..."
docker compose -f docker-compose.server.yml up -d --build

echo ""
echo "=== DSC Monitor Started ==="
echo "UDP Port: 6000 (for RTL-Airband audio)"
echo "Web UI: http://$(hostname -I | awk '{print $1}'):8000"
echo "Messages saved to: ./dsc_messages/"
echo ""
echo "View logs: docker compose -f docker-compose.server.yml logs -f"
echo "Stop: docker compose -f docker-compose.server.yml down"
