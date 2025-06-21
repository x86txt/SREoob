#!/bin/bash

# SREoob Agent Installation Demo
# This script demonstrates what the real installation process looks like

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${PURPLE}"
echo "  ███████╗██████╗ ███████╗ ██████╗  ██████╗ ██████╗ "
echo "  ██╔════╝██╔══██╗██╔════╝██╔═══██╗██╔═══██╗██╔══██╗"
echo "  ███████╗██████╔╝█████╗  ██║   ██║██║   ██║██████╔╝"
echo "  ╚════██║██╔══██╗██╔══╝  ██║   ██║██║   ██║██╔══██╗"
echo "  ███████║██║  ██║███████╗╚██████╔╝╚██████╔╝██████╔╝"
echo "  ╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ "
echo -e "${NC}"
echo -e "${CYAN}SREoob Monitoring Agent - Installation Demo${NC}"
echo -e "${YELLOW}===========================================${NC}"
echo ""

echo -e "${YELLOW}!${NC} Running as user - will install to user directory"
echo -e "  Install location: $HOME/.local/bin"
echo ""

echo -e "${BLUE}Detected platform:${NC} linux/amd64"
echo ""

echo -e "${BLUE}Checking prerequisites...${NC}"
echo -e "${GREEN}✓${NC} All prerequisites satisfied"
echo ""

echo -e "${BLUE}Configuration Setup${NC}"
echo -e "${YELLOW}==================${NC}"
echo ""
echo -e "${CYAN}Enter your SREoob master server URL:${NC}"
echo -e "${YELLOW}Examples:${NC}"
echo -e "  • https://sreoob.example.com"
echo -e "  • https://monitoring.company.com"
echo -e "  • http://192.168.1.100:8000"
echo ""
echo -e "Master URL: ${CYAN}https://demo.sreoob.com${NC}"
echo ""

echo -e "${CYAN}Enter a name for this agent:${NC}"
echo -e "${YELLOW}Examples:${NC}"
echo -e "  • Production Monitor"
echo -e "  • EU West Agent"
echo -e "  • Office Network Monitor"
echo ""
echo -e "Agent Name: ${CYAN}Demo Production Agent${NC}"
echo ""

echo -e "${CYAN}Enter a description for this agent (optional):${NC}"
echo -e "Description: ${CYAN}Monitoring production services in the US East region${NC}"
echo ""

echo -e "${BLUE}Setting up directories...${NC}"
echo -e "${GREEN}✓${NC} Directories created"

echo -e "${BLUE}Downloading SREoob agent...${NC}"
echo -e "Downloading from: https://github.com/yourusername/sreoob/releases/latest/download/sreoob-agent-linux-amd64"
sleep 1
echo -e "${GREEN}✓${NC} Agent binary downloaded and installed"
echo ""

echo -e "${BLUE}Generating API key...${NC}"
sleep 1
echo -e "${GREEN}✓${NC} API key generated: abc123def456789a..."
echo ""

echo -e "${BLUE}Creating configuration file...${NC}"
echo -e "${GREEN}✓${NC} Configuration saved to: $HOME/.config/sreoob/agent.env"
echo ""

echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                        NEXT STEPS                                 ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}1. Register the agent in your SREoob dashboard:${NC}"
echo -e "   • Open: ${CYAN}https://demo.sreoob.com/agents${NC}"
echo -e "   • Click: ${CYAN}'Add Agent'${NC}"
echo -e "   • Agent Name: ${CYAN}Demo Production Agent${NC}"
echo -e "   • API Key: ${CYAN}abc123def456789abcdef123456789abcdef123456789abcdef123456789abcdef12${NC}"
echo -e "   • Description: ${CYAN}Monitoring production services in the US East region${NC}"
echo ""

echo -e "${YELLOW}2. Start the agent:${NC}"
echo -e "   ${CYAN}source $HOME/.config/sreoob/agent.env${NC}"
echo -e "   ${CYAN}$HOME/.local/bin/sreoob-agent${NC}"
echo ""

echo -e "${BLUE}Configuration Summary:${NC}"
echo -e "${YELLOW}=====================${NC}"
echo -e "Agent Binary: ${CYAN}$HOME/.local/bin/sreoob-agent${NC}"
echo -e "Config File:  ${CYAN}$HOME/.config/sreoob/agent.env${NC}"
echo -e "Master URL:   ${CYAN}https://demo.sreoob.com${NC}"
echo -e "Agent Name:   ${CYAN}Demo Production Agent${NC}"
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 SREoob Agent installation completed successfully! 🎉          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Don't forget to register the agent in your dashboard before starting it!${NC}"
echo "" 