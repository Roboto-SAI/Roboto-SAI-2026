#!/bin/bash
# Roboto SAI Development Environment Setup
# Start all services locally (without Docker)

set -e

if [ "$1" = "--stop" ]; then
    echo "🛑 Stopping Roboto SAI Development Environment"
    pkill -f "python main_modular.py" || true
    pkill -f "npm run dev" || true
    pkill -f "npm start" || true
    echo "✅ All services stopped"
    exit 0
fi

echo "🚀 Starting Roboto SAI Development Environment"
echo "============================================="

# Function to start process in background
start_service() {
    local name="$1"
    local command="$2"
    local cwd="$3"

    echo "Starting $name..."
    (
        cd "$cwd"
        eval "$command" &
        echo "$!" > "/tmp/roboto_$name.pid"
    )
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Start backend (Python)
start_service "Backend API Server" "python main_modular.py" "$REPO_ROOT/backend"

# Wait for backend to start
sleep 5

# Start OS Agent (Node.js)
start_service "OS Agent (MCP Host)" "npm run dev" "$REPO_ROOT/os-agent"

# Wait for OS Agent to start
sleep 3

# Build MCP servers
echo "Building MCP servers..."
cd "$REPO_ROOT/mcp-servers/fs-server" && npm run build

# Start MCP filesystem server
start_service "MCP Filesystem Server" "npm start" "$REPO_ROOT/mcp-servers/fs-server"

# Start frontend (Vite)
start_service "Frontend Dev Server" "npm run dev" "$REPO_ROOT"

echo ""
echo "✅ All services starting..."
echo ""
echo "🔗 Service URLs:"
echo "   Frontend:    http://localhost:8080"
echo "   Backend:     http://localhost:5000"
echo "   OS Agent:    http://localhost:5055"
echo "   MCP FS:      Running in background"
echo ""
echo "Run '$0 --stop' to stop all services"
echo ""
echo "Services will continue running. Press Ctrl+C to exit this script..."

# Wait for user interrupt
trap 'echo ""; echo "🛑 To stop all services, run: $0 --stop"' INT
while true; do
    sleep 1
done