#!/bin/bash

# Local build script for SREoob Agent
# This demonstrates the same build process used in GitHub Actions

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}SREoob Agent Local Build Script${NC}"
echo -e "${YELLOW}================================${NC}"

# Get version info (simulate GitHub Actions)
VERSION=${1:-"dev-$(date +%Y%m%d%H%M%S)"}
BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo -e "${BLUE}Build Information:${NC}"
echo "Version: $VERSION"
echo "Build Time: $BUILD_TIME"
echo "Git Commit: $GIT_COMMIT"
echo ""

# Build flags for version info
LDFLAGS="-s -w -X main.Version=$VERSION -X main.BuildTime=$BUILD_TIME -X main.GitCommit=$GIT_COMMIT"

# Platform to build for (default to current platform)
GOOS=${GOOS:-$(go env GOOS)}
GOARCH=${GOARCH:-$(go env GOARCH)}

echo -e "${BLUE}Building for platform:${NC} $GOOS/$GOARCH"

# Determine binary name
BINARY_NAME="sreoob-agent-${GOOS}-${GOARCH}"
if [[ "$GOOS" == "windows" ]]; then
    BINARY_NAME="${BINARY_NAME}.exe"
fi

echo -e "${BLUE}Output binary:${NC} $BINARY_NAME"
echo ""

# Build the binary
echo -e "${YELLOW}Building binary...${NC}"
CGO_ENABLED=0 go build -ldflags="$LDFLAGS" -o "$BINARY_NAME" .

# Verify the binary was created
if [[ -f "$BINARY_NAME" ]]; then
    echo -e "${GREEN}✓ Build successful!${NC}"
    echo ""
    
    # Show binary info
    echo -e "${BLUE}Binary information:${NC}"
    ls -la "$BINARY_NAME"
    echo ""
    
    # Test version output (if building for current platform)
    if [[ "$GOOS" == "$(go env GOOS)" && "$GOARCH" == "$(go env GOARCH)" ]]; then
        echo -e "${BLUE}Testing binary:${NC}"
        ./"$BINARY_NAME" -version
        echo ""
    fi
    
    echo -e "${GREEN}Build completed successfully!${NC}"
    echo -e "${YELLOW}Binary location:${NC} $(pwd)/$BINARY_NAME"
else
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi 