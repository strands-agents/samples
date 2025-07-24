#!/bin/bash

# AI Triage Agent - Development Starter
# Intelligent medical triage system with Strands Agents

set -e

echo "🚀 Starting AI Triage Agent with Strands Agents..."

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
export REACT_APP_API_BASE="http://localhost:8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check port availability
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null; then
        echo -e "${YELLOW}Warning: Port $1 is already in use${NC}"
        return 1
    fi
    return 0
}

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}Error: Node.js/npm is not installed${NC}"
    exit 1
fi

if ! command_exists uvx; then
    echo -e "${YELLOW}Installing uvx for MCP servers...${NC}"
    pip install uvx
fi

# Install backend dependencies
echo -e "${BLUE}Setting up Python backend...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

echo -e "${YELLOW}Activating virtual environment and installing dependencies...${NC}"
source venv/bin/activate
pip install -r requirements.txt

# Install frontend dependencies
echo -e "${BLUE}Setting up React frontend...${NC}"
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
    npm install
fi

# Go back to root
cd ..

# Check ports
check_port 8000 || echo -e "${YELLOW}Backend may conflict on port 8000${NC}"
check_port 3000 || echo -e "${YELLOW}Frontend may conflict on port 3000${NC}"

# Start backend in background
echo -e "${GREEN}Starting AI Triage Agent backend on port 8000...${NC}"
cd backend
source venv/bin/activate

# Start backend with proper error handling
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Give backend time to start
sleep 3

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}Error: Backend failed to start${NC}"
    exit 1
fi

# Start frontend
echo -e "${GREEN}Starting AI Triage Agent frontend on port 3000...${NC}"
cd ../frontend

# Start frontend with proper error handling
npm start &
FRONTEND_PID=$!

# Store PIDs for cleanup
echo $BACKEND_PID > ../backend.pid
echo $FRONTEND_PID > ../frontend.pid

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    
    if [ -f "../backend.pid" ]; then
        BACKEND_PID=$(cat ../backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            echo -e "${GREEN}Backend stopped${NC}"
        fi
        rm -f ../backend.pid
    fi
    
    if [ -f "../frontend.pid" ]; then
        FRONTEND_PID=$(cat ../frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            echo -e "${GREEN}Frontend stopped${NC}"
        fi
        rm -f ../frontend.pid
    fi
    
    echo -e "${GREEN}Cleanup completed${NC}"
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Wait for services to start
sleep 5

echo -e "${GREEN}✅ AI Triage Agent started successfully!${NC}"
echo -e "${BLUE}🏥 Triage Interface: http://localhost:3000${NC}"
echo -e "${BLUE}🔧 API Docs: http://localhost:8000/docs${NC}"
echo -e "${BLUE}❤️  Health Check: http://localhost:8000/health${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Wait for processes
wait 