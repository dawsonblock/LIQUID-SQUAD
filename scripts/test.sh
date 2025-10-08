#!/bin/bash
# Test automation script
# Runs all tests with coverage

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== LIQUID HIVE 25 - Test Suite ===${NC}"
echo ""

# Configuration
EXIT_CODE=0

# Backend tests
echo -e "${YELLOW}Running backend tests...${NC}"
cd full_build_upgraded/full_build

if pytest tests/ -v --tb=short --cov=full_build --cov-report=term --cov-report=html; then
    echo -e "${GREEN}✓ Backend tests passed${NC}"
else
    echo -e "${RED}✗ Backend tests failed${NC}"
    EXIT_CODE=1
fi

echo ""
echo -e "${BLUE}Coverage report: full_build_upgraded/full_build/htmlcov/index.html${NC}"
cd - > /dev/null

# Frontend tests
echo ""
echo -e "${YELLOW}Running frontend tests...${NC}"
cd full_build_upgraded/gui

if npm test -- --watchAll=false --coverage; then
    echo -e "${GREEN}✓ Frontend tests passed${NC}"
else
    echo -e "${RED}✗ Frontend tests failed${NC}"
    EXIT_CODE=1
fi

echo ""
echo -e "${BLUE}Coverage report: full_build_upgraded/gui/coverage/index.html${NC}"
cd - > /dev/null

# Summary
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}=== All tests passed ===${NC}"
else
    echo -e "${RED}=== Some tests failed ===${NC}"
fi

exit $EXIT_CODE
