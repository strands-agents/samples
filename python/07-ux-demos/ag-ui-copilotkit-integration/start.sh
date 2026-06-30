#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Start AG-UI Strands Sample - Local Development
#
# This script starts both the agent and frontend for local development.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ports - change these if needed
AGENT_PORT=8001
FRONTEND_PORT=3001

echo "=========================================="
echo "AG-UI Strands Sample - Local Development"
echo "=========================================="
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $AGENT_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start Agent
echo "Starting agent..."
cd "$SCRIPT_DIR/agent"

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    uv venv
fi

source .venv/bin/activate
uv pip install -e . --quiet

echo "Agent starting on http://localhost:$AGENT_PORT"
AGENT_PORT=$AGENT_PORT python main.py &
AGENT_PID=$!

# Wait for agent to be ready
sleep 3

# Start Frontend
echo ""
echo "Starting frontend..."
cd "$SCRIPT_DIR/frontend"

# Always run npm install to ensure dependencies are up to date
echo "Installing npm dependencies (this may take a moment on first run)..."
npm install

echo "Frontend starting on http://localhost:$FRONTEND_PORT"
AGENT_URL="http://localhost:$AGENT_PORT" npm run dev -- -p $FRONTEND_PORT &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "✓ Both services starting!"
echo ""
echo "  Agent:    http://localhost:$AGENT_PORT"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo ""
echo "Press Ctrl+C to stop both services"
echo "=========================================="

# Wait for both processes
wait
