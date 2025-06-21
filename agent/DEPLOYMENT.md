# SREoob Agent Deployment Guide

This guide explains how to deploy the SREoob monitoring agent as a systemd service.

## Quick Start

### 1. Generate API Key

First, generate an API key and hash:

```bash
go run . -genkey
```

This will output:
- `AGENT_API_KEY` - Copy this to your agent configuration
- `AGENT_API_KEY_HASH` - Copy this to your server's `.env` file

### 2. Build the Agent

```bash
go build -o sreoob-agent .
```

### 3. Install as Systemd Service

```bash
sudo ./install.sh
```

### 4. Configure Environment Variables

Edit the systemd service file:

```bash
sudo nano /etc/systemd/system/sreoob-agent.service
```

Update these essential variables:

```ini
Environment=MASTER_FQDN=https://your-sreoob-server.com
Environment=AGENT_API_KEY=your_64_character_api_key_here
Environment=AGENT_ID=agent-prod-01
```

### 5. Start the Service

```bash
sudo systemctl enable sreoob-agent
sudo systemctl start sreoob-agent
```

### 6. Monitor the Service

```bash
# Check status
sudo systemctl status sreoob-agent

# View logs
sudo journalctl -u sreoob-agent -f

# View recent logs
sudo journalctl -u sreoob-agent --since "1 hour ago"
```

## Configuration

### Essential Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MASTER_FQDN` | SREoob server URL | `https://monitor.company.com` |
| `AGENT_API_KEY` | 64-character API key | Generated with `-genkey` |
| `AGENT_ID` | Unique agent identifier | `agent-prod-01` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_SERVER_PORT` | `5227` | Agent communication port |
| `AGENT_PORT` | `8081` | Local agent health check port |
| `USE_WEBSOCKET` | `true` | Enable WebSocket communication |
| `LOG_LEVEL` | `info` | Log level (debug, info, warn, error) |

## Communication Protocols

The agent uses a fallback protocol system:

1. **WebSocket (WSS)** - Real-time bidirectional communication
2. **HTTP/2** - Efficient HTTP communication
3. **HTTP/1.1** - Final fallback

## Security Features

The systemd service includes several security hardening features:

- Runs as dedicated `sreoob` user
- Restricted file system access
- Memory execution protection
- System call filtering
- Resource limits (512MB RAM, 50% CPU)

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status sreoob-agent

# Check logs for errors
sudo journalctl -u sreoob-agent --no-pager
```

### Connection Issues

```bash
# Test API key generation
/opt/sreoob-agent/sreoob-agent -genkey

# Check network connectivity
curl -v https://your-sreoob-server.com:5227/health
```

### Permission Issues

```bash
# Fix permissions
sudo chown -R sreoob:sreoob /opt/sreoob-agent
sudo chown -R sreoob:sreoob /var/log/sreoob-agent
```

## Manual Installation

If you prefer manual installation:

```bash
# Create user
sudo useradd --system --shell /bin/false sreoob

# Create directories
sudo mkdir -p /opt/sreoob-agent
sudo mkdir -p /var/log/sreoob-agent

# Copy binary
sudo cp sreoob-agent /opt/sreoob-agent/
sudo chmod +x /opt/sreoob-agent/sreoob-agent

# Set ownership
sudo chown -R sreoob:sreoob /opt/sreoob-agent
sudo chown -R sreoob:sreoob /var/log/sreoob-agent

# Install service
sudo cp sreoob-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
```

## Uninstallation

```bash
# Stop and disable service
sudo systemctl stop sreoob-agent
sudo systemctl disable sreoob-agent

# Remove files
sudo rm /etc/systemd/system/sreoob-agent.service
sudo rm -rf /opt/sreoob-agent
sudo rm -rf /var/log/sreoob-agent

# Remove user (optional)
sudo userdel sreoob

# Reload systemd
sudo systemctl daemon-reload
``` 