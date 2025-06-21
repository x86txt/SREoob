#!/bin/bash

# Cross-platform build script for SREoob Agent
# Builds for all supported platforms like GitHub Actions

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}SREoob Agent Cross-Platform Build${NC}"
echo -e "${YELLOW}==================================${NC}"

# Get version info
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

# Define platforms to build for (matching GitHub Actions)
declare -a PLATFORMS=(
    "linux/amd64"
    "linux/arm64" 
    "linux/arm/7"
    "linux/riscv64"
    "darwin/arm64"
    "windows/amd64"
)

# Create build directory
BUILD_DIR="builds"
mkdir -p "$BUILD_DIR"

echo -e "${BLUE}Building for ${#PLATFORMS[@]} platforms...${NC}"
echo ""

SUCCESSFUL_BUILDS=0
FAILED_BUILDS=0

# Build for each platform
for platform in "${PLATFORMS[@]}"; do
    IFS='/' read -ra PLATFORM_PARTS <<< "$platform"
    GOOS=${PLATFORM_PARTS[0]}
    GOARCH=${PLATFORM_PARTS[1]}
    GOARM=${PLATFORM_PARTS[2]:-""}
    
    # Determine binary name
    BINARY_NAME="sreoob-agent-${GOOS}-${GOARCH}"
    if [[ -n "$GOARM" ]]; then
        BINARY_NAME="sreoob-agent-${GOOS}-arm"
    fi
    if [[ "$GOOS" == "windows" ]]; then
        BINARY_NAME="${BINARY_NAME}.exe"
    fi
    
    echo -e "${YELLOW}Building $platform → $BINARY_NAME${NC}"
    
    # Set environment and build
    export GOOS GOARCH GOARM CGO_ENABLED=0
    
    if go build -ldflags="$LDFLAGS" -o "$BUILD_DIR/$BINARY_NAME" .; then
        echo -e "${GREEN}✓ Success${NC}"
        SUCCESSFUL_BUILDS=$((SUCCESSFUL_BUILDS + 1))
        
        # Show file size
        if command -v stat >/dev/null 2>&1; then
            SIZE=$(stat -f%z "$BUILD_DIR/$BINARY_NAME" 2>/dev/null || stat -c%s "$BUILD_DIR/$BINARY_NAME" 2>/dev/null || echo "unknown")
            echo -e "  Size: $(numfmt --to=iec --suffix=B $SIZE 2>/dev/null || echo "${SIZE} bytes")"
        fi
    else
        echo -e "${RED}✗ Failed${NC}"
        FAILED_BUILDS=$((FAILED_BUILDS + 1))
    fi
    echo ""
done

# Summary
echo -e "${BLUE}Build Summary:${NC}"
echo -e "${GREEN}✓ Successful: $SUCCESSFUL_BUILDS${NC}"
if [[ $FAILED_BUILDS -gt 0 ]]; then
    echo -e "${RED}✗ Failed: $FAILED_BUILDS${NC}"
fi
echo ""

if [[ $SUCCESSFUL_BUILDS -gt 0 ]]; then
    echo -e "${BLUE}Built binaries:${NC}"
    ls -la "$BUILD_DIR"/
    echo ""
    
    # Create checksums
    echo -e "${BLUE}Creating checksums...${NC}"
    cd "$BUILD_DIR"
    sha256sum * > SHA256SUMS
    echo -e "${GREEN}✓ SHA256SUMS created${NC}"
    cd ..
    
    echo ""
    echo -e "${GREEN}Cross-platform build completed!${NC}"
    echo -e "${YELLOW}Binaries location:${NC} $(pwd)/$BUILD_DIR/"
else
    echo -e "${RED}No successful builds!${NC}"
    exit 1
fi 