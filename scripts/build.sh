#!/bin/bash
# Build script for LIQUID HIVE 25
# Builds optimized production images

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="full_build_upgraded/full_build"
GUI_DIR="full_build_upgraded/gui"
BACKEND_IMAGE="liquid-hive-api"
GUI_IMAGE="liquid-hive-gui"
VERSION="${VERSION:-latest}"

echo -e "${BLUE}=== LIQUID HIVE 25 - Production Build ===${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_status "Docker is running"

# Build backend
echo ""
echo -e "${YELLOW}Building backend image...${NC}"
cd $BACKEND_DIR
docker build \
    -f Dockerfile.optimized \
    -t ${BACKEND_IMAGE}:${VERSION} \
    -t ${BACKEND_IMAGE}:$(git rev-parse --short HEAD) \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    --build-arg VCS_REF=$(git rev-parse --short HEAD) \
    --build-arg VERSION=${VERSION} \
    .

if [ $? -eq 0 ]; then
    print_status "Backend image built successfully"
else
    print_error "Backend build failed"
    exit 1
fi

cd - > /dev/null

# Build frontend
echo ""
echo -e "${YELLOW}Building frontend image...${NC}"
cd $GUI_DIR
docker build \
    -f Dockerfile.optimized \
    -t ${GUI_IMAGE}:${VERSION} \
    -t ${GUI_IMAGE}:$(git rev-parse --short HEAD) \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    --build-arg VCS_REF=$(git rev-parse --short HEAD) \
    --build-arg VERSION=${VERSION} \
    .

if [ $? -eq 0 ]; then
    print_status "Frontend image built successfully"
else
    print_error "Frontend build failed"
    exit 1
fi

cd - > /dev/null

# Display image sizes
echo ""
echo -e "${BLUE}=== Image Information ===${NC}"
docker images | grep -E "(REPOSITORY|${BACKEND_IMAGE}|${GUI_IMAGE})" | head -5

echo ""
print_status "Build complete!"
print_info "Backend: ${BACKEND_IMAGE}:${VERSION}"
print_info "Frontend: ${GUI_IMAGE}:${VERSION}"

# Optional: Run quick tests
if [ "${RUN_TESTS:-false}" = "true" ]; then
    echo ""
    echo -e "${YELLOW}Running tests...${NC}"
    ./scripts/test.sh
fi

# Optional: Push to registry
if [ "${PUSH_IMAGES:-false}" = "true" ]; then
    echo ""
    echo -e "${YELLOW}Pushing images to registry...${NC}"
    
    if [ -z "${REGISTRY:-}" ]; then
        print_error "REGISTRY environment variable not set"
        exit 1
    fi
    
    docker tag ${BACKEND_IMAGE}:${VERSION} ${REGISTRY}/${BACKEND_IMAGE}:${VERSION}
    docker tag ${GUI_IMAGE}:${VERSION} ${REGISTRY}/${GUI_IMAGE}:${VERSION}
    
    docker push ${REGISTRY}/${BACKEND_IMAGE}:${VERSION}
    docker push ${REGISTRY}/${GUI_IMAGE}:${VERSION}
    
    print_status "Images pushed to registry"
fi

echo ""
echo -e "${GREEN}=== Build Complete ===${NC}"
