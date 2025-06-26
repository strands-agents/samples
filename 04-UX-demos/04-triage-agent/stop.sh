#!/bin/bash

echo "🛑 Stopping AI Triage Agent..."

# Kill processes by PID files
if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo "✅ Backend stopped"
    fi
    rm -f backend.pid
fi

if [ -f "frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo "✅ Frontend stopped"
    fi
    rm -f frontend.pid
fi

# Kill any remaining processes on ports 8000 and 3000
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "npm.*start" 2>/dev/null || true
pkill -f "react-scripts/scripts/start.js"

echo "🏁 All services stopped"
