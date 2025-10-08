#!/bin/bash
# Deployment script for LIQUID HIVE 25
# Handles production deployment with health checks

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-production}"
COMPOSE_FILE="${2:-docker-compose.prod.yml}"

echo -e "${BLUE}=== LIQUID HIVE 25 - Deployment ===${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    echo -e "${YELLOW}Please create .env file with required variables${NC}"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

echo -e "${GREEN}✓ Environment variables loaded${NC}"

# Validate required environment variables
REQUIRED_VARS=(
    "AUTH_TOKEN"
    "POSTGRES_PASSWORD"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}✗ Required variable $var is not set${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✓ Required variables validated${NC}"

# Pull latest images if using pre-built
if [ "${BUILD_IMAGES:-true}" = "false" ]; then
    echo ""
    echo -e "${YELLOW}Pulling latest images...${NC}"
    docker compose -f $COMPOSE_FILE pull
fi

# Stop existing containers
echo ""
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker compose -f $COMPOSE_FILE down --remove-orphans

# Start services
echo ""
echo -e "${YELLOW}Starting services...${NC}"
docker compose -f $COMPOSE_FILE up -d --build

# Wait for services to be healthy
echo ""
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"

MAX_WAIT=120
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    if docker compose -f $COMPOSE_FILE ps | grep -q "unhealthy"; then
        echo -e "${YELLOW}Waiting... (${ELAPSED}s)${NC}"
        sleep 5
        ELAPSED=$((ELAPSED + 5))
    else
        break
    fi
done

# Check service health
echo ""
echo -e "${BLUE}=== Service Health Check ===${NC}"

# API health
if curl -sf http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ API is healthy${NC}"
else
    echo -e "${RED}✗ API is not responding${NC}"
    docker compose -f $COMPOSE_FILE logs api
    exit 1
fi

# GUI health
if curl -sf http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✓ GUI is healthy${NC}"
else
    echo -e "${RED}✗ GUI is not responding${NC}"
    docker compose -f $COMPOSE_FILE logs gui
    exit 1
fi

# Display service status
echo ""
echo -e "${BLUE}=== Service Status ===${NC}"
docker compose -f $COMPOSE_FILE ps

# Display URLs
echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo -e "${BLUE}Services available at:${NC}"
echo "  API:        http://localhost:8000"
echo "  GUI:        http://localhost:3000"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana:    http://localhost:3001"
echo ""
echo -e "${YELLOW}View logs:${NC} docker compose -f $COMPOSE_FILE logs -f"
echo -e "${YELLOW}Stop services:${NC} docker compose -f $COMPOSE_FILE down"
