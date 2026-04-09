#!/bin/bash
# Simple startup script for Render - TCP Tunnel Server

echo "=== Starting Simple TCP Tunnel Server ==="
echo ""

# Ensure we're in the correct directory
cd /storage/self/primary/ScriptsExecutor

# Verify Python is available
if ! command -v python3 &> /dev/null
then
    echo "Error: python3 not found"
    exit 1
fi

# Show environment info
echo "Environment:"
echo "  Python: $(python3 --version 2>/dev/null || echo 'Not found')"
echo "  Working dir: $(pwd)"
echo "  Render PORT: ${PORT:-not set (will use 4444)}"
echo ""

# Start the tunnel server
echo "Launching tunnel server..."
echo "----------------------------------------"
python3 tunnel_server.py