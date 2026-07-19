#!/bin/bash
# Setup script for DSC Monitor server

set -e

echo "=== DSC Monitor Server Setup ==="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Please install Docker first:"
    echo "  curl -fsSL https://get.docker.com | sh"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Create directories
mkdir -p dsc_messages logs

# Build and start
echo "Building and starting DSC Monitor..."
docker-compose -f docker-compose.server.yml up -d --build

echo ""
echo "=== DSC Monitor Started ==="
echo "UDP Port: 6000 (for RTL-Airband audio)"
echo "Web UI: http://$(hostname -I | awk '{print $1}'):8000"
echo "Messages saved to: ./dsc_messages/"
echo ""
echo "View logs: docker-compose -f docker-compose.server.yml logs -f"
echo "Stop: docker-compose -f docker-compose.server.yml down"
