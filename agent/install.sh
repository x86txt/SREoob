#!/bin/bash

# SREoob Agent Quick Start Installer
# This script downloads and sets up the SREoob monitoring agent

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
GITHUB_REPO="x86txt/SREoob"  # Update this to your actual repo
BINARY_NAME="sreoob-agent"
INSTALL_DIR="/usr/local/bin"
SERVICE_DIR="/etc/systemd/system"
CONFIG_DIR="/etc/sreoob"

# Banner
echo -e "${PURPLE}"
echo "  ███████╗██████╗ ███████╗ ██████╗  ██████╗ ██████╗ "
echo "  ██╔════╝██╔══██╗██╔════╝██╔═══██╗██╔═══██╗██╔══██╗"
echo "  ███████╗██████╔╝█████╗  ██║   ██║██║   ██║██████╔╝"
echo "  ╚════██║██╔══██╗██╔══╝  ██║   ██║██║   ██║██╔══██╗"
echo "  ███████║██║  ██║███████╗╚██████╔╝╚██████╔╝██████╔╝"
echo "  ╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ "
echo -e "${NC}"
echo -e "${CYAN}SREoob Monitoring Agent - Quick Start Installer${NC}"
echo -e "${YELLOW}==========================================${NC}"
echo ""

# Check if running as root for system installation
if [[ $EUID -eq 0 ]]; then
    INSTALL_TYPE="system"
    echo -e "${GREEN}✓${NC} Running as root - will install system-wide"
else
    INSTALL_TYPE="user"
    INSTALL_DIR="$HOME/.local/bin"
    CONFIG_DIR="$HOME/.config/sreoob"
    echo -e "${YELLOW}!${NC} Running as user - will install to user directory"
    echo -e "  Install location: ${INSTALL_DIR}"
fi

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case $ARCH in
    x86_64) ARCH="amd64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    armv7l) ARCH="arm" ;;
    i386|i686) ARCH="386" ;;
    *) 
        echo -e "${RED}✗${NC} Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

case $OS in
    linux) OS="linux" ;;
    darwin) OS="darwin" ;;
    mingw*|msys*|cygwin*) OS="windows"; BINARY_NAME="${BINARY_NAME}.exe" ;;
    *)
        echo -e "${RED}✗${NC} Unsupported operating system: $OS"
        exit 1
        ;;
esac

BINARY_FILE="${BINARY_NAME}-${OS}-${ARCH}"
if [[ $OS == "windows" ]]; then
    BINARY_FILE="${BINARY_FILE}.exe"
fi

echo -e "${BLUE}Detected platform:${NC} ${OS}/${ARCH}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
echo -e "${BLUE}Checking prerequisites...${NC}"
for cmd in curl; do
    if ! command_exists $cmd; then
        echo -e "${RED}✗${NC} Required command not found: $cmd"
        echo "Please install $cmd and try again."
        exit 1
    fi
done
echo -e "${GREEN}✓${NC} All prerequisites satisfied"
echo ""

# Get master server URL
echo -e "${BLUE}Configuration Setup${NC}"
echo -e "${YELLOW}==================${NC}"
echo ""
while true; do
    echo -e "${CYAN}Enter your SREoob master server URL:${NC}"
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  • https://sreoob.example.com"
    echo -e "  • https://monitoring.company.com"
    echo -e "  • http://192.168.1.100:8000"
    echo ""
    read -p "Master URL: " MASTER_URL < /dev/tty
    
    if [[ -z "$MASTER_URL" ]]; then
        echo -e "${RED}✗${NC} Master URL cannot be empty"
        continue
    fi
    
    # Add https:// if no protocol specified
    if [[ ! "$MASTER_URL" =~ ^https?:// ]]; then
        MASTER_URL="https://$MASTER_URL"
        echo -e "${YELLOW}!${NC} Added https:// prefix: $MASTER_URL"
    fi
    
    break
done
echo ""

# Get agent name
while true; do
    echo -e "${CYAN}Enter a name for this agent:${NC}"
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  • Production Monitor"
    echo -e "  • EU West Agent"
    echo -e "  • Office Network Monitor"
    echo ""
    read -p "Agent Name: " AGENT_NAME < /dev/tty
    
    if [[ -z "$AGENT_NAME" ]]; then
        echo -e "${RED}✗${NC} Agent name cannot be empty"
        continue
    fi
    
    break
done
echo ""

# Optional description
echo -e "${CYAN}Enter a description for this agent (optional):${NC}"
read -p "Description: " AGENT_DESCRIPTION < /dev/tty
echo ""

# Create directories
echo -e "${BLUE}Setting up directories...${NC}"
mkdir -p "$(dirname "$INSTALL_DIR")"
mkdir -p "$CONFIG_DIR"
if [[ $INSTALL_TYPE == "system" && $OS == "linux" ]]; then
    mkdir -p "$SERVICE_DIR"
fi
echo -e "${GREEN}✓${NC} Directories created"

# Download binary
echo -e "${BLUE}Downloading SREoob agent...${NC}"
DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/releases/latest/download/${BINARY_FILE}"
echo -e "Downloading from: ${DOWNLOAD_URL}"

if curl -fsSL "$DOWNLOAD_URL" -o "${INSTALL_DIR}/${BINARY_NAME}"; then
    chmod +x "${INSTALL_DIR}/${BINARY_NAME}"
    echo -e "${GREEN}✓${NC} Agent binary downloaded and installed"
else
    echo -e "${RED}✗${NC} Failed to download agent binary"
    echo -e "${YELLOW}Note:${NC} Make sure the GitHub release exists with pre-compiled binaries"
    echo -e "Expected file: ${BINARY_FILE}"
    exit 1
fi
echo ""

# Generate API key
echo -e "${BLUE}Generating API key...${NC}"
API_KEY_OUTPUT=$("${INSTALL_DIR}/${BINARY_NAME}" -genkey 2>&1)
API_KEY=$(echo "$API_KEY_OUTPUT" | grep "AGENT_API_KEY=" | cut -d= -f2)

if [[ -z "$API_KEY" ]]; then
    echo -e "${RED}✗${NC} Failed to generate API key"
    echo "Output: $API_KEY_OUTPUT"
    exit 1
fi

echo -e "${GREEN}✓${NC} API key generated: ${API_KEY:0:16}..."
echo ""

# Create configuration file
CONFIG_FILE="${CONFIG_DIR}/agent.env"
echo -e "${BLUE}Creating configuration file...${NC}"
cat > "$CONFIG_FILE" << EOF
# SREoob Agent Configuration
MASTER_FQDN=$MASTER_URL
API_KEY=$API_KEY
AGENT_PORT=8081
USE_WEBSOCKET=true
LOG_LEVEL=info

# Agent Information
AGENT_NAME=$AGENT_NAME
AGENT_DESCRIPTION=$AGENT_DESCRIPTION
EOF

# Set secure permissions (readable only by owner)
chmod 600 "$CONFIG_FILE"
echo -e "${GREEN}✓${NC} Configuration saved to: $CONFIG_FILE"
echo -e "${GREEN}✓${NC} Secure permissions set (600 - owner read/write only)"
echo ""

# Create systemd service (Linux only)
if [[ $INSTALL_TYPE == "system" && $OS == "linux" ]]; then
    echo -e "${BLUE}Creating systemd service...${NC}"
    cat > "${SERVICE_DIR}/sreoob-agent.service" << EOF
[Unit]
Description=SREoob Monitoring Agent
Documentation=https://github.com/${GITHUB_REPO}
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=sreoob
Group=sreoob
EnvironmentFile=${CONFIG_FILE}
ExecStart=${INSTALL_DIR}/${BINARY_NAME}
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${CONFIG_DIR}
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

    # Create user if it doesn't exist
    if ! id "sreoob" &>/dev/null; then
        useradd --system --no-create-home --shell /bin/false sreoob
        echo -e "${GREEN}✓${NC} Created sreoob system user"
    fi
    
    # Set ownership and ensure secure permissions are maintained
    chown -R sreoob:sreoob "$CONFIG_DIR"
    chmod 600 "$CONFIG_FILE"  # Re-apply secure permissions after ownership change
    echo -e "${GREEN}✓${NC} Ownership set to sreoob user with secure permissions"
    
    echo -e "${GREEN}✓${NC} Systemd service created"
    echo ""
fi

# Instructions for agent registration
echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                        NEXT STEPS                                 ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}1. Register the agent in your SREoob dashboard:${NC}"
echo -e "   • Open: ${MASTER_URL}/agents"
echo -e "   • Click: ${CYAN}'Add Agent'${NC}"
echo -e "   • Agent Name: ${CYAN}${AGENT_NAME}${NC}"
echo -e "   • API Key: ${CYAN}${API_KEY}${NC}"
if [[ -n "$AGENT_DESCRIPTION" ]]; then
    echo -e "   • Description: ${CYAN}${AGENT_DESCRIPTION}${NC}"
fi
echo ""

echo -e "${YELLOW}2. Start the agent:${NC}"
if [[ $INSTALL_TYPE == "system" && $OS == "linux" ]]; then
    echo -e "   ${CYAN}sudo systemctl enable sreoob-agent${NC}"
    echo -e "   ${CYAN}sudo systemctl start sreoob-agent${NC}"
    echo ""
    echo -e "${YELLOW}3. Check agent status:${NC}"
    echo -e "   ${CYAN}sudo systemctl status sreoob-agent${NC}"
    echo -e "   ${CYAN}sudo journalctl -u sreoob-agent -f${NC}"
else
    echo -e "   ${CYAN}source ${CONFIG_FILE}${NC}"
    echo -e "   ${CYAN}${INSTALL_DIR}/${BINARY_NAME}${NC}"
fi
echo ""

# Show configuration summary
echo -e "${BLUE}Configuration Summary:${NC}"
echo -e "${YELLOW}=====================${NC}"
echo -e "Agent Binary: ${CYAN}${INSTALL_DIR}/${BINARY_NAME}${NC}"
echo -e "Config File:  ${CYAN}${CONFIG_FILE}${NC}"
echo -e "Master URL:   ${CYAN}${MASTER_URL}${NC}"
echo -e "Agent Name:   ${CYAN}${AGENT_NAME}${NC}"
if [[ $INSTALL_TYPE == "system" && $OS == "linux" ]]; then
    echo -e "Service File: ${CYAN}${SERVICE_DIR}/sreoob-agent.service${NC}"
fi
echo ""

# Final success message
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 SREoob Agent installation completed successfully! 🎉          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Don't forget to register the agent in your dashboard before starting it!${NC}"
echo "" 