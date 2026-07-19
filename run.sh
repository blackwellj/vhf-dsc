#!/bin/bash
# Run DSC Monitor without Docker

set -e

echo "=== DSC Monitor ==="

# Install dependencies if needed
if ! python -c "import vhf_dsc" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -e .
fi

# Create directories
mkdir -p dsc_messages logs

# Start monitor
echo "Starting DSC Monitor on UDP port 6000..."
echo "Saving messages to ./dsc_messages/"
echo "Press Ctrl+C to stop"
echo ""

python -m cli.monitor_server --port 6000 --sample-rate 16000 --save-dir ./dsc_messages
