#!/bin/bash
# Validation script for LIQUID HIVE 25
# Validates environment and dependencies before deployment

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== LIQUID HIVE 25 - System Validation ===${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Function to check command exists
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        if [ ! -z "$2" ]; then
            VERSION=$($1 $2 2>&1 | head -1)
            echo -e "  ${BLUE}→${NC} $VERSION"
        fi
    else
        echo -e "${RED}✗${NC} $1 is not installed"
        ERRORS=$((ERRORS + 1))
    fi
}

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
    else
        echo -e "${RED}✗${NC} $1 not found"
        ERRORS=$((ERRORS + 1))
    fi
}

# Check required commands
echo -e "${YELLOW}Checking required tools...${NC}"
check_command "python3" "--version"
check_command "node" "--version"
check_command "npm" "--version"
check_command "docker" "--version"
check_command "git" "--version"

echo ""

# Check optional commands
echo -e "${YELLOW}Checking optional tools...${NC}"
check_command "make" "--version" || WARNINGS=$((WARNINGS + 1))
check_command "pre-commit" "--version" || WARNINGS=$((WARNINGS + 1))

echo ""

# Check critical files
echo -e "${YELLOW}Checking critical files...${NC}"
check_file "Makefile"
check_file ".env.example"
check_file "full_build_upgraded/full_build/requirements.txt"
check_file "full_build_upgraded/gui/package.json"
check_file "docker-compose.prod.yml"

echo ""

# Check environment variables
echo -e "${YELLOW}Checking environment configuration...${NC}"

if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
    
    # Source the .env file
    set -a
    source .env 2>/dev/null || true
    set +a
    
    # Check critical variables
    if [ -z "${AUTH_TOKEN}" ]; then
        echo -e "${YELLOW}⚠${NC} AUTH_TOKEN not set (API will allow unauthenticated access)"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}✓${NC} AUTH_TOKEN is set"
    fi
    
    if [ -z "${POSTGRES_PASSWORD}" ]; then
        echo -e "${YELLOW}⚠${NC} POSTGRES_PASSWORD not set"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}✓${NC} POSTGRES_PASSWORD is set"
    fi
else
    echo -e "${YELLOW}⚠${NC} .env file not found (using defaults)"
    echo -e "  ${BLUE}→${NC} Copy .env.example to .env and configure"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

# Check Docker
echo -e "${YELLOW}Checking Docker...${NC}"
if docker info &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker is running"
    DOCKER_VERSION=$(docker version --format '{{.Server.Version}}')
    echo -e "  ${BLUE}→${NC} Docker version: $DOCKER_VERSION"
else
    echo -e "${RED}✗${NC} Docker is not running"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# Check ports
echo -e "${YELLOW}Checking ports availability...${NC}"
PORTS=(3000 8000 6333 9200 9090 3001 5432 6379)
PORT_NAMES=("GUI" "API" "Qdrant" "Elasticsearch" "Prometheus" "Grafana" "PostgreSQL" "Redis")

for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    NAME=${PORT_NAMES[$i]}
    
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠${NC} Port $PORT ($NAME) is in use"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}✓${NC} Port $PORT ($NAME) is available"
    fi
done

echo ""

# Summary
echo -e "${BLUE}=== Validation Summary ===${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo -e "${GREEN}System is ready for deployment.${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Validation completed with $WARNINGS warnings${NC}"
    echo -e "${YELLOW}System should work but may need attention.${NC}"
    exit 0
else
    echo -e "${RED}✗ Validation failed with $ERRORS errors and $WARNINGS warnings${NC}"
    echo -e "${RED}Please fix errors before proceeding.${NC}"
    exit 1
fi
