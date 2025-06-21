#!/bin/bash

# SREoob Server Quick Start Installer
# This script downloads and sets up the SREoob monitoring server

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
GITHUB_REPO="x86txt/SREoob"
COMPOSE_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/refs/heads/main/docker-compose.yml"
NGINX_CONFIG_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/refs/heads/main/nginx/nginx.conf"

# Banner
echo -e "${PURPLE}"
echo "  ███████╗██████╗ ███████╗ ██████╗  ██████╗ ██████╗ "
echo "  ██╔════╝██╔══██╗██╔════╝██╔═══██╗██╔═══██╗██╔══██╗"
echo "  ███████╗██████╔╝█████╗  ██║   ██║██║   ██║██████╔╝"
echo "  ╚════██║██╔══██╗██╔══╝  ██║   ██║██║   ██║██╔══██╗"
echo "  ███████║██║  ██║███████╗╚██████╔╝╚██████╔╝██████╔╝"
echo "  ╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ "
echo -e "${NC}"
echo -e "${CYAN}SREoob Server - Quick Start Installer${NC}"
echo -e "${YELLOW}=====================================${NC}"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    INSTALL_TYPE="system"
    INSTALL_DIR="/opt/sreoob"
    CONFIG_DIR="/etc/sreoob"
    echo -e "${GREEN}✓${NC} Running as root - will install system-wide"
else
    INSTALL_TYPE="user"
    INSTALL_DIR="$HOME/sreoob"
    CONFIG_DIR="$HOME/.config/sreoob"
    echo -e "${YELLOW}!${NC} Running as user - will install to user directory"
    echo -e "  Install location: ${INSTALL_DIR}"
fi

echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
echo -e "${BLUE}Checking prerequisites...${NC}"
MISSING_DEPS=()

if ! command_exists docker; then
    MISSING_DEPS+=("docker")
fi

if ! command_exists docker-compose; then
    if ! docker compose version >/dev/null 2>&1; then
        MISSING_DEPS+=("docker-compose")
    fi
fi

if ! command_exists curl; then
    MISSING_DEPS+=("curl")
fi

if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
    echo -e "${RED}✗${NC} Missing required dependencies: ${MISSING_DEPS[*]}"
    echo ""
    echo -e "${YELLOW}Please install the missing dependencies:${NC}"
    echo -e "  • Docker: https://docs.docker.com/get-docker/"
    echo -e "  • Docker Compose: https://docs.docker.com/compose/install/"
    echo -e "  • curl: Usually available in package managers"
    exit 1
fi

echo -e "${GREEN}✓${NC} All prerequisites satisfied"
echo ""

# Get deployment type
echo -e "${BLUE}Deployment Configuration${NC}"
echo -e "${YELLOW}========================${NC}"
echo ""
echo -e "${CYAN}Choose deployment type:${NC}"
echo -e "${YELLOW}1)${NC} Complete Stack (Backend + Frontend + Nginx) ${GREEN}[Recommended]${NC}"
echo -e "${YELLOW}2)${NC} Backend Only (API server)"
echo -e "${YELLOW}3)${NC} Frontend Only (Web interface)"
echo ""
while true; do
    read -p "Enter choice (1-3): " DEPLOY_TYPE < /dev/tty
    
    case $DEPLOY_TYPE in
        1)
            DEPLOY_MODE="full"
            echo -e "${GREEN}✓${NC} Selected: Complete Stack"
            break
            ;;
        2)
            DEPLOY_MODE="backend"
            echo -e "${GREEN}✓${NC} Selected: Backend Only"
            break
            ;;
        3)
            DEPLOY_MODE="frontend"
            echo -e "${GREEN}✓${NC} Selected: Frontend Only"
            break
            ;;
        *)
            echo -e "${RED}✗${NC} Invalid choice. Please enter 1, 2, or 3."
            ;;
    esac
done
echo ""

# Get domain/hostname
echo -e "${CYAN}Enter the domain or hostname for your SREoob server:${NC}"
echo -e "${YELLOW}Examples:${NC}"
echo -e "  • sreoob.example.com"
echo -e "  • monitoring.company.com"
echo -e "  • localhost (for local testing)"
echo ""
while true; do
    read -p "Domain/Hostname: " SERVER_DOMAIN < /dev/tty
    
    if [[ -z "$SERVER_DOMAIN" ]]; then
        echo -e "${RED}✗${NC} Domain cannot be empty"
        continue
    fi
    
    break
done
echo ""

# Get SSL configuration
if [[ "$SERVER_DOMAIN" != "localhost" && "$SERVER_DOMAIN" != "127.0.0.1" ]]; then
    echo -e "${CYAN}Do you want to enable SSL/HTTPS?${NC}"
    echo -e "${YELLOW}Note:${NC} You'll need to provide SSL certificates or use Let's Encrypt"
    echo ""
    while true; do
        read -p "Enable SSL? (y/n): " ENABLE_SSL < /dev/tty
        
        case $ENABLE_SSL in
            [Yy]* )
                USE_SSL="true"
                PROTOCOL="https"
                echo -e "${GREEN}✓${NC} SSL enabled"
                break
                ;;
            [Nn]* )
                USE_SSL="false"
                PROTOCOL="http"
                echo -e "${YELLOW}!${NC} SSL disabled (HTTP only)"
                break
                ;;
            * )
                echo -e "${RED}✗${NC} Please answer yes (y) or no (n)"
                ;;
        esac
    done
else
    USE_SSL="false"
    PROTOCOL="http"
    echo -e "${YELLOW}!${NC} Using HTTP for localhost"
fi
echo ""

# Get admin API key (optional)
echo -e "${CYAN}Set up admin authentication? (optional)${NC}"
echo -e "${YELLOW}This allows you to protect admin functions with an API key${NC}"
echo ""
while true; do
    read -p "Enable admin authentication? (y/n): " ENABLE_AUTH < /dev/tty
    
    case $ENABLE_AUTH in
        [Yy]* )
            echo ""
            echo -e "${CYAN}Enter admin API key (64 characters recommended):${NC}"
            echo -e "${YELLOW}Tip:${NC} Generate a secure key with: openssl rand -hex 32"
            read -p "Admin API Key: " ADMIN_API_KEY < /dev/tty
            
            if [[ ${#ADMIN_API_KEY} -lt 32 ]]; then
                echo -e "${YELLOW}!${NC} Warning: API key is shorter than recommended (32+ characters)"
            fi
            break
            ;;
        [Nn]* )
            ADMIN_API_KEY=""
            echo -e "${YELLOW}!${NC} Admin authentication disabled"
            break
            ;;
        * )
            echo -e "${RED}✗${NC} Please answer yes (y) or no (n)"
            ;;
    esac
done
echo ""

# Create directories
echo -e "${BLUE}Setting up directories...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
echo -e "${GREEN}✓${NC} Directories created"

# Download Docker Compose file
echo -e "${BLUE}Downloading deployment configuration...${NC}"
if curl -fsSL "$COMPOSE_URL" -o "$INSTALL_DIR/docker-compose.yml"; then
    echo -e "${GREEN}✓${NC} Docker Compose configuration downloaded"
else
    echo -e "${RED}✗${NC} Failed to download Docker Compose configuration"
    echo -e "${YELLOW}Note:${NC} Make sure the GitHub release exists"
    exit 1
fi

# Download nginx configuration if needed
if [[ "$DEPLOY_MODE" == "full" ]]; then
    mkdir -p "$INSTALL_DIR/nginx"
    if curl -fsSL "$NGINX_CONFIG_URL" -o "$INSTALL_DIR/nginx/nginx.conf"; then
        echo -e "${GREEN}✓${NC} Nginx configuration downloaded"
    else
        echo -e "${YELLOW}!${NC} Could not download nginx config, using default"
    fi
fi

# Create environment file
ENV_FILE="$INSTALL_DIR/.env"
echo -e "${BLUE}Creating environment configuration...${NC}"
cat > "$ENV_FILE" << EOF
# SREoob Server Configuration
COMPOSE_PROJECT_NAME=sreoob

# Server Configuration
SERVER_DOMAIN=$SERVER_DOMAIN
PROTOCOL=$PROTOCOL
USE_SSL=$USE_SSL

# Backend Configuration
DATABASE_PATH=/data/sreoob.db
SCAN_RANGE_MIN=30s
SCAN_RANGE_MAX=5m
LOG_LEVEL=info

# Agent Communication
AGENT_SERVER_PORT=5227

# Authentication
$(if [[ -n "$ADMIN_API_KEY" ]]; then
    # Generate Argon2 hash for the API key
    echo "ADMIN_API_KEY_HASH=\"\$(echo '$ADMIN_API_KEY' | python3 -c 'import sys, hashlib, secrets; key=sys.stdin.read().strip(); salt=secrets.token_bytes(32); print(f\"\$argon2id\$v=19\$m=65536,t=3,p=4\${salt.hex()}\${hashlib.pbkdf2_hmac(\"sha256\", key.encode(), salt, 100000).hex()}\")')\""
else
    echo "# ADMIN_API_KEY_HASH=your_argon2_hash_here"
fi)

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000
NGINX_PORT=80
NGINX_SSL_PORT=443

# Docker Configuration
RESTART_POLICY=unless-stopped
EOF

echo -e "${GREEN}✓${NC} Environment configuration created"
echo ""

# Modify docker-compose.yml based on deployment mode
if [[ "$DEPLOY_MODE" != "full" ]]; then
    echo -e "${BLUE}Customizing deployment for $DEPLOY_MODE mode...${NC}"
    
    # Create a custom compose file based on the mode
    cp "$INSTALL_DIR/docker-compose.yml" "$INSTALL_DIR/docker-compose.yml.backup"
    
    case $DEPLOY_MODE in
        "backend")
            # Remove frontend and nginx services
            python3 -c "
import yaml
with open('$INSTALL_DIR/docker-compose.yml', 'r') as f:
    config = yaml.safe_load(f)
config['services'] = {k: v for k, v in config['services'].items() if k == 'backend'}
if 'frontend' in config['services']:
    del config['services']['frontend']
if 'nginx' in config['services']:
    del config['services']['nginx']
with open('$INSTALL_DIR/docker-compose.yml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False)
" 2>/dev/null || echo "Note: Could not customize compose file, using full configuration"
            ;;
        "frontend")
            # Remove backend and nginx services, but this might not work without backend
            echo -e "${YELLOW}!${NC} Frontend-only mode requires a separate backend server"
            ;;
    esac
    
    echo -e "${GREEN}✓${NC} Deployment customized"
fi

# Pull Docker images
echo -e "${BLUE}Pulling Docker images...${NC}"
cd "$INSTALL_DIR"
if docker-compose pull; then
    echo -e "${GREEN}✓${NC} Docker images pulled successfully"
else
    echo -e "${YELLOW}!${NC} Some images may not be available, will build locally if needed"
fi

# Instructions
echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                        NEXT STEPS                                 ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}1. Start the SREoob server:${NC}"
echo -e "   ${CYAN}cd $INSTALL_DIR${NC}"
echo -e "   ${CYAN}docker-compose up -d${NC}"
echo ""

echo -e "${YELLOW}2. Access your SREoob dashboard:${NC}"
case $DEPLOY_MODE in
    "full")
        echo -e "   ${CYAN}${PROTOCOL}://${SERVER_DOMAIN}${NC}"
        ;;
    "backend")
        echo -e "   ${CYAN}${PROTOCOL}://${SERVER_DOMAIN}:8000${NC} (API only)"
        ;;
    "frontend")
        echo -e "   ${CYAN}${PROTOCOL}://${SERVER_DOMAIN}:3000${NC}"
        ;;
esac
echo ""

if [[ -n "$ADMIN_API_KEY" ]]; then
    echo -e "${YELLOW}3. Admin authentication:${NC}"
    echo -e "   ${CYAN}API Key: $ADMIN_API_KEY${NC}"
    echo ""
fi

echo -e "${YELLOW}$(if [[ -n "$ADMIN_API_KEY" ]]; then echo "4"; else echo "3"; fi). Deploy monitoring agents:${NC}"
echo -e "   ${CYAN}curl -fsSL https://raw.githubusercontent.com/${GITHUB_REPO}/refs/heads/main/agent/install.sh | bash${NC}"
echo ""

echo -e "${YELLOW}$(if [[ -n "$ADMIN_API_KEY" ]]; then echo "5"; else echo "4"; fi). Manage your deployment:${NC}"
echo -e "   ${CYAN}docker-compose logs -f${NC}     # View logs"
echo -e "   ${CYAN}docker-compose stop${NC}       # Stop services"
echo -e "   ${CYAN}docker-compose restart${NC}    # Restart services"
echo -e "   ${CYAN}docker-compose pull && docker-compose up -d${NC}  # Update to latest"
echo ""

# Show configuration summary
echo -e "${BLUE}Configuration Summary:${NC}"
echo -e "${YELLOW}=====================${NC}"
echo -e "Install Directory: ${CYAN}$INSTALL_DIR${NC}"
echo -e "Config Directory:  ${CYAN}$CONFIG_DIR${NC}"
echo -e "Deployment Mode:   ${CYAN}$DEPLOY_MODE${NC}"
echo -e "Server Domain:     ${CYAN}$SERVER_DOMAIN${NC}"
echo -e "Protocol:          ${CYAN}$PROTOCOL${NC}"
if [[ -n "$ADMIN_API_KEY" ]]; then
    echo -e "Admin Auth:        ${CYAN}Enabled${NC}"
fi
echo ""

# SSL reminder
if [[ "$USE_SSL" == "true" ]]; then
    echo -e "${YELLOW}📋 SSL Configuration Reminder:${NC}"
    echo -e "  • Place your SSL certificates in: ${CYAN}$INSTALL_DIR/ssl/${NC}"
    echo -e "  • Certificate file: ${CYAN}$SERVER_DOMAIN.crt${NC}"
    echo -e "  • Private key file: ${CYAN}$SERVER_DOMAIN.key${NC}"
    echo -e "  • Or use Let's Encrypt with certbot"
    echo ""
fi

# Final success message
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 SREoob Server installation completed successfully! 🎉         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Ready to start monitoring your infrastructure with SREoob!${NC}"
echo "" 