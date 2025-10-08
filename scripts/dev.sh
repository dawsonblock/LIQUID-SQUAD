#!/bin/bash
# Development environment startup script
# Starts backend and frontend in development mode

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== LIQUID HIVE 25 - Development Server ===${NC}"
echo ""

# Check dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed${NC}"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Dependencies OK${NC}"

# Set environment variables
export PYTHONUNBUFFERED=1
export LOG_LEVEL=DEBUG
export RETRIEVAL_MODE=disabled
export AUTH_TOKEN=dev-token-12345

# Trap to kill all background processes on exit
trap 'kill $(jobs -p) 2>/dev/null' EXIT

# Start backend
echo ""
echo -e "${YELLOW}Starting backend API (http://localhost:8000)...${NC}"
cd full_build_upgraded/full_build
python3 -m uvicorn full_build.service.api_enhanced:app --reload --port 8000 --log-level debug &
BACKEND_PID=$!
cd - > /dev/null

# Wait a bit for backend to start
sleep 3

# Start frontend
echo -e "${YELLOW}Starting frontend GUI (http://localhost:3000)...${NC}"
cd full_build_upgraded/gui
npm run dev &
FRONTEND_PID=$!
cd - > /dev/null

echo ""
echo -e "${GREEN}=== Development servers started ===${NC}"
echo -e "${BLUE}Backend API:${NC} http://localhost:8000"
echo -e "${BLUE}API Docs:${NC} http://localhost:8000/docs"
echo -e "${BLUE}Metrics:${NC} http://localhost:8000/metrics"
echo -e "${BLUE}Frontend GUI:${NC} http://localhost:3000"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Wait for user interrupt
wait
