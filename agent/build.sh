#!/bin/bash

# SiteUp Agent Build Script

set -e

echo "Building SiteUp Monitoring Agent..."

# Clean previous builds
echo "Cleaning previous builds..."
rm -f siteup-agent siteup-agent-*

# Initialize go modules if needed
if [ ! -f "go.sum" ]; then
    echo "Initializing Go modules..."
    go mod tidy
fi

# Build for current platform
echo "Building for current platform..."
go build -ldflags "-s -w" -o siteup-agent .

echo "✅ Built siteup-agent for current platform"

# Build for multiple platforms if requested
if [ "$1" = "all" ]; then
    echo "Building for multiple platforms..."
    
    # Linux AMD64
    echo "Building for Linux AMD64..."
    GOOS=linux GOARCH=amd64 go build -ldflags "-s -w" -o siteup-agent-linux-amd64 .
    
    # Linux ARM64
    echo "Building for Linux ARM64..."
    GOOS=linux GOARCH=arm64 go build -ldflags "-s -w" -o siteup-agent-linux-arm64 .
    
    # Windows AMD64
    echo "Building for Windows AMD64..."
    GOOS=windows GOARCH=amd64 go build -ldflags "-s -w" -o siteup-agent-windows-amd64.exe .
    
    # macOS AMD64
    echo "Building for macOS AMD64..."
    GOOS=darwin GOARCH=amd64 go build -ldflags "-s -w" -o siteup-agent-darwin-amd64 .
    
    # macOS ARM64 (Apple Silicon)
    echo "Building for macOS ARM64..."
    GOOS=darwin GOARCH=arm64 go build -ldflags "-s -w" -o siteup-agent-darwin-arm64 .
    
    echo "✅ Built agents for all platforms:"
    ls -la siteup-agent-*
fi

echo "✅ Build complete!"
echo ""
echo "Usage:"
echo "  export MASTER_FQDN=https://your-siteup-master.com"
echo "  export API_KEY=\$(openssl rand -hex 32)  # Generate 64-char key"
echo "  ./siteup-agent" 