#!/bin/bash
set -e

# SREoob Agent Installation Script
# =================================

AGENT_USER="sreoob"
AGENT_GROUP="sreoob"
INSTALL_DIR="/opt/sreoob-agent"
LOG_DIR="/var/log/sreoob-agent"
SERVICE_FILE="/etc/systemd/system/sreoob-agent.service"

echo "SREoob Agent Installation Script"
echo "================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "ERROR: This script must be run as root (use sudo)" 
   exit 1
fi

# Check if binary exists
if [[ ! -f "./sreoob-agent" ]]; then
    echo "ERROR: sreoob-agent binary not found in current directory"
    echo "Please build the agent first with: go build -o sreoob-agent ."
    exit 1
fi

# Check if service file exists
if [[ ! -f "./sreoob-agent.service" ]]; then
    echo "ERROR: sreoob-agent.service file not found in current directory"
    exit 1
fi

echo "Step 1: Creating user and group..."
if ! id "$AGENT_USER" &>/dev/null; then
    useradd --system --shell /bin/false --home-dir "$INSTALL_DIR" --create-home "$AGENT_USER"
    echo "Created user: $AGENT_USER"
else
    echo "User $AGENT_USER already exists"
fi

echo "Step 2: Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"

echo "Step 3: Installing binary..."
cp "./sreoob-agent" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/sreoob-agent"

echo "Step 4: Setting permissions..."
chown -R "$AGENT_USER:$AGENT_GROUP" "$INSTALL_DIR"
chown -R "$AGENT_USER:$AGENT_GROUP" "$LOG_DIR"

echo "Step 5: Installing systemd service..."
cp "./sreoob-agent.service" "$SERVICE_FILE"

echo "Step 6: Configuring systemd..."
systemctl daemon-reload

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit the service file to configure your environment variables:"
echo "   sudo nano $SERVICE_FILE"
echo ""
echo "2. Required environment variables to configure:"
echo "   - MASTER_FQDN=https://your-sreoob-server.com"
echo "   - AGENT_API_KEY=your_64_character_api_key"
echo "   - AGENT_ID=unique_agent_name"
echo ""
echo "3. Generate an API key (if needed):"
echo "   $INSTALL_DIR/sreoob-agent -genkey"
echo ""
echo "4. Enable and start the service:"
echo "   sudo systemctl enable sreoob-agent"
echo "   sudo systemctl start sreoob-agent"
echo ""
echo "5. Check service status:"
echo "   sudo systemctl status sreoob-agent"
echo "   sudo journalctl -u sreoob-agent -f"
echo ""
echo "Installation directory: $INSTALL_DIR"
echo "Log directory: $LOG_DIR"
echo "Service file: $SERVICE_FILE" 