# sreoob Monitoring Agent

[![Go Version](https://img.shields.io/badge/go-1.21%2B-blue.svg)](https://golang.org/dl/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![WebSocket](https://img.shields.io/badge/websocket-enabled-brightgreen.svg)](#real-time-synchronization)
[![Cross Platform](https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos-lightgrey.svg)](#cross-compilation)

A lightweight Go-based monitoring agent that connects to a SREoob master instance to monitor websites and services with **real-time synchronization**.

**🎯 Complete Workflow:**
1. **Deploy:** Run the one-liner installation script on any server
2. **Register:** Copy the generated API key to your SREoob dashboard  
3. **Monitor:** Agent automatically syncs and starts monitoring your sites
4. **Scale:** Deploy multiple agents across different locations/networks

## 🚀 Quick Start

**Get up and running in 30 seconds:**

```bash
curl -fsSL https://raw.githubusercontent.com/x86txt/SREoob/refs/heads/main/agent/install.sh | bash
```

*The installer will:*
- ✅ **Auto-detect your platform** (Linux/macOS/Windows, AMD64/ARM64)
- ✅ **Download pre-compiled binary** from GitHub releases
- ✅ **Generate secure API key** automatically
- ✅ **Create configuration files** and systemd service
- ✅ **Provide clear next steps** for dashboard registration

**Alternative (wget):**
```bash
wget -qO- https://raw.githubusercontent.com/x86txt/SREoob/refs/heads/main/agent/install.sh | bash
```

**What you'll need:**
- Your SREoob dashboard URL (e.g., `https://sreoob.example.com`)
- A name for your agent (e.g., "Production Monitor")
- 30 seconds of your time! ⚡

**Try the demo first:**
```bash
./agent/demo-install.sh  # Shows what the installation looks like
```

> **💡 Want the full setup process?** See the [detailed installation guide](#-installation) below.
> 
> **🔧 For developers:** 
> - Update the `GITHUB_REPO` variable in `install.sh` to point to your repository
> - Ensure your GitHub repo has releases with pre-compiled binaries (see [Cross-compilation](#cross-compilation))

## 📋 Table of Contents

- [Quick Start](#-quick-start) ⭐
- [Features](#-features)
- [Configuration](#-configuration)
- [Real-time Synchronization](#-real-time-synchronization)
- [Generating API Keys](#-generating-a-secure-api-key)
- [Environment Variables](#-setting-environment-variables)
- [Installation](#-installation)
- [Building from Source](#-building-from-source)
- [GitHub Actions & Releases](#-github-actions--releases)
- [Docker Deployment](#-docker-deployment)
- [Monitoring Behavior](#-monitoring-behavior)
- [Supported Site Types](#-supported-site-types)
- [Logging](#-logging)
- [Security](#-security-considerations)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)
- [Architecture](#-architecture)

## ✨ Features

- 🔒 **Secure**: Minimal attack surface with only essential dependencies
- ⚡ **Fast**: Written in Go for optimal performance and low resource usage
- 🔄 **Real-time**: WebSocket support for instant updates from master
- 🎯 **Flexible**: Supports HTTP/HTTPS and ping monitoring
- 🌐 **Distributed**: Can be deployed remotely from the master instance
- 🛡️ **Reliable**: Automatic reconnection and graceful error handling
- 📊 **Adaptive**: Sync frequency adapts to the fastest site check interval

## ⚙️ Configuration

The agent is configured using environment variables:

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MASTER_FQDN` | Master sreoob instance FQDN | `https://sreoob.example.com` |
| `API_KEY` | Authentication key (≥64 chars) | `abc123...` (64+ characters) |

> **Note**: If no protocol is specified in `MASTER_FQDN`, `https://` is assumed.

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_PORT` | `8081` | Port for agent-specific traffic |
| `USE_WEBSOCKET` | `true` | Enable WebSocket for real-time updates |
| `LOG_LEVEL` | `info` | Logging level (`debug`, `info`, `warn`, `error`) |

## 🔄 Real-time Synchronization

The agent uses multiple synchronization methods for optimal performance:

### WebSocket (Primary) 🚀

- **Real-time updates**: Instant notification when sites are added/removed from master
- **Persistent connection**: Maintains efficient WebSocket connection to master
- **Automatic fallback**: Falls back to HTTP polling if WebSocket fails

### HTTP Polling (Fallback) 📡

- **Adaptive frequency**: Syncs based on fastest site scan interval (minimum 10s)
- **Smart calculation**: If fastest site checks every 60s → agent syncs every 15s
- **Automatic adjustment**: Sync frequency updates when site intervals change

### Connection Details 🔗

| Connection Type | Endpoint | Purpose |
|----------------|----------|---------|
| **WebSocket** | `wss://master:8081/agent/ws` | Real-time updates, result submission |
| **HTTP API** | `https://master:8081/api/` | Fallback polling, connection testing |

## 🔐 Generating a Secure API Key

The agent requires a minimum **64-character** API key for authentication with the master server.

> **⚠️ Important**: Generate the API key **only once** and reuse it across all agents. If you already have agents deployed, use the same base64 key for consistency.

### For New Deployments 🆕

If this is your **first agent** or you're starting fresh:

#### Step 1: Generate API Key 🎯

```bash
# Generate key using the agent binary
./sreoob-agent -genkey

# This outputs:
# Generated API Key: abc123...def789 (copy this key)
# Argon2 Hash: $argon2id$v=19$m=65536,t=3,p=4$... (not needed for new workflow)
```

#### Step 2: Register Agent in Dashboard 🌐

1. **Open your SREoob dashboard** in a web browser
2. **Navigate to the Agents page** (`/agents`)
3. **Click "Add Agent"** button
4. **Fill in the form**:
   - **Agent Name**: e.g., "Production Monitor", "EU West Agent"
   - **API Key**: Paste the 64-character key from Step 1
   - **Description**: Optional description of the agent's purpose
5. **Click "Add Agent"** - the server will hash and store the key automatically

#### Step 3: Configure and Run Agent 🚀

```bash
# Set environment variables
export MASTER_FQDN="https://your-sreoob-master.com"
export API_KEY="abc123...def789"  # The key from Step 1

# Run the agent
./sreoob-agent
```

#### Linux / macOS 🐧 🍎

```bash
# Generate a 64-character random string
API_KEY=$(openssl rand -hex 32)
echo "Generated API Key: $API_KEY"
echo "Save this key - use it for ALL agents!"
```

#### Windows (PowerShell) 🪟

```powershell
# Generate a 64-character random string
$API_KEY = -join ((1..64) | ForEach {'{0:X}' -f (Get-Random -Max 16)})
Write-Host "Generated API Key: $API_KEY"
Write-Host "Save this key - use it for ALL agents!"
```

#### Alternative (Python - Any Platform) 🐍

```bash
python3 -c "import secrets; print('Generated API Key:', secrets.token_hex(32)); print('Save this key - use it for ALL agents!')"
```

### For Existing Deployments 🔄

If you **already have agents** registered in the dashboard:

#### Option A: Use Existing Key (Recommended) ✅
1. **Find your existing key**: Check your current agent's environment variables or config
2. **Use the same key**: Set `API_KEY` to the same value on all new agents
3. **No dashboard action needed**: The key is already registered

#### Option B: Register New Agent 🆕
1. **Follow the "New Deployments" process** above to generate and register a new agent
2. **Each registered agent** can have its own unique API key
3. **Multiple agents supported**: You can have different keys for different purposes

### Key Management Best Practices 🔒

- ✅ **Use the dashboard**: Register agents through the web interface for easy management
- ✅ **One key per agent**: Each agent can have its own unique API key for better security
- ✅ **Store securely**: Keep API keys in a secure location (password manager, vault)
- ✅ **Monitor in dashboard**: View agent status and last-seen times in the `/agents` page
- ✅ **Rotate when needed**: Generate new keys and update agents when required
- ✅ **Remove unused agents**: Delete old agent registrations from the dashboard

### Example Multi-Agent Setup 🌐

```bash
# Agent 1: Production Monitor
./sreoob-agent -genkey  # Generates key1
# Register "Production Monitor" in dashboard with key1
export API_KEY="key1..."
export MASTER_FQDN="https://sreoob.example.com"
./sreoob-agent

# Agent 2: Development Monitor  
./sreoob-agent -genkey  # Generates key2
# Register "Development Monitor" in dashboard with key2
export API_KEY="key2..."
export MASTER_FQDN="https://sreoob.example.com"
./sreoob-agent

# Each agent has its own unique key and identity
```

## 🌍 Setting Environment Variables

### Linux / macOS (Bash/Zsh)

<details>
<summary>Click to expand</summary>

```bash
# Set for current session
export MASTER_FQDN="https://your-sreoob-master.com"
export API_KEY="your-64-character-api-key-here"
export AGENT_PORT="8081"
export USE_WEBSOCKET="true"
export LOG_LEVEL="info"

# Make permanent by adding to ~/.bashrc or ~/.zshrc
echo 'export MASTER_FQDN="https://your-sreoob-master.com"' >> ~/.bashrc
echo 'export API_KEY="your-64-character-api-key-here"' >> ~/.bashrc
echo 'export AGENT_PORT="8081"' >> ~/.bashrc
echo 'export USE_WEBSOCKET="true"' >> ~/.bashrc
echo 'export LOG_LEVEL="info"' >> ~/.bashrc
source ~/.bashrc
```

</details>

### Windows (Command Prompt)

<details>
<summary>Click to expand</summary>

```cmd
REM Set for current session
set MASTER_FQDN=https://your-sreoob-master.com
set API_KEY=your-64-character-api-key-here
set AGENT_PORT=8081
set USE_WEBSOCKET=true
set LOG_LEVEL=info

REM Make permanent (requires admin privileges)
setx MASTER_FQDN "https://your-sreoob-master.com"
setx API_KEY "your-64-character-api-key-here"
setx AGENT_PORT "8081"
setx USE_WEBSOCKET "true"
setx LOG_LEVEL "info"
```

</details>

### Windows (PowerShell)

<details>
<summary>Click to expand</summary>

```powershell
# Set for current session
$env:MASTER_FQDN = "https://your-sreoob-master.com"
$env:API_KEY = "your-64-character-api-key-here"
$env:AGENT_PORT = "8081"
$env:USE_WEBSOCKET = "true"
$env:LOG_LEVEL = "info"

# Make permanent for current user
[Environment]::SetEnvironmentVariable("MASTER_FQDN", "https://your-sreoob-master.com", "User")
[Environment]::SetEnvironmentVariable("API_KEY", "your-64-character-api-key-here", "User")
[Environment]::SetEnvironmentVariable("AGENT_PORT", "8081", "User")
[Environment]::SetEnvironmentVariable("USE_WEBSOCKET", "true", "User")
[Environment]::SetEnvironmentVariable("LOG_LEVEL", "info", "User")
```

</details>

## 📦 Installation

### From Source

1. **Prerequisites**: Ensure you have [Go 1.21+](https://golang.org/dl/) installed
2. **Download**: Clone or download the agent code
3. **Build**: 

```bash
cd agent
go mod tidy
go build -o sreoob-agent
```

### Quick Start 🚀

```bash
# Generate secure API key and run
export MASTER_FQDN="https://your-sreoob-master.com"
export API_KEY=$(openssl rand -hex 32)
./sreoob-agent
```

### Using Environment Files

```bash
# Create .env file
cat > .env << 'EOF'
MASTER_FQDN=https://your-sreoob-master.com
API_KEY=your-64-character-api-key-generated-above
AGENT_PORT=8081
USE_WEBSOCKET=true
LOG_LEVEL=info
EOF

# Load and run
source .env
./sreoob-agent
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker build -t sreoob-agent .

# Run container
docker run -d \
  --name sreoob-agent \
  -e MASTER_FQDN=https://your-sreoob-master.com \
  -e API_KEY=your-64-character-api-key-generated-above \
  -e AGENT_PORT=8081 \
  -e USE_WEBSOCKET=true \
  --restart unless-stopped \
  sreoob-agent
```

### Docker Compose

```yaml
version: '3.8'
services:
  sreoob-agent:
    build: .
    restart: unless-stopped
    environment:
      - MASTER_FQDN=https://your-sreoob-master.com
      - API_KEY=your-64-character-api-key
      - AGENT_PORT=8081
      - USE_WEBSOCKET=true
      - LOG_LEVEL=info
```

## 📊 Monitoring Behavior

### Real-time Operation ⚡

- **WebSocket**: Receives instant updates when sites are added/removed
- **Adaptive sync**: HTTP fallback syncs based on fastest site scan interval
- **Result submission**: Sends check results back to master in real-time
- **Auto-recovery**: Automatically reconnects if connections are lost

### Site Monitoring 🎯

- Each site is monitored according to its configured scan interval
- Supports both HTTP/HTTPS and ping monitoring protocols
- Results are immediately submitted to master (WebSocket preferred, HTTP fallback)
- Graceful handling of temporary connection issues

### Performance Optimization 📈

| Scenario | Sync Frequency | Description |
|----------|----------------|-------------|
| Fast sites (10s checks) | Every 10s | Minimum sync interval |
| Normal sites (60s checks) | Every 15s | 4x faster than fastest |
| Slow sites (5m+ checks) | Every 5m | Maximum sync interval |

- **Efficient connections**: Persistent WebSocket with HTTP/2 fallback
- **Minimal resource usage**: Only syncs when needed

## 🌐 Supported Site Types

### HTTP/HTTPS Sites 🌍

```
✅ https://example.com
✅ http://internal-service.local:8080
✅ https://api.service.com/health
```

### Ping Monitoring 🏓

```
✅ ping://example.com
✅ ping://192.168.1.1
✅ ping://internal-host.local
```

## 📝 Logging

The agent provides structured logging with the following levels:

| Level | Description | Example |
|-------|-------------|---------|
| **INFO** | Normal operations | Site monitoring, connections |
| **WARN** | Warning conditions | Fallbacks, retries |
| **ERROR** | Error conditions | Failed checks, connection issues |
| **FATAL** | Critical errors | Configuration errors, startup failures |

### Example Log Output

```log
INFO: SREoob Agent starting - connecting to master at https://sreoob.example.com
INFO: Using custom agent port: 8081
INFO: WebSocket enabled for real-time updates
INFO: Successfully connected to master
INFO: WebSocket connection established
INFO: Starting monitoring for site 'Example Site' (ID: 1) with 30s interval
INFO: Monitoring refresh complete - 2 sites active, sync interval: 7.5s
✅ Example Site: up (0.142s)
❌ Test Site: down (5.001s) - Request failed: context deadline exceeded
INFO: Received site update via WebSocket: 3 sites
```

## 🔒 Security Considerations

- ✅ Always use **HTTPS** for the master FQDN in production
- ✅ Keep API keys **secure** and rotate them regularly
- ✅ Use **dedicated agent port** to isolate traffic
- ✅ Run the agent with **minimal privileges**
- ✅ Consider running in a **container** for additional isolation
- ✅ Monitor agent logs for **security events**
- ✅ WebSocket connections use **same authentication** as HTTP

## 🔧 Troubleshooting

### Connection Issues ❌

<details>
<summary><strong>"Failed to connect to master"</strong></summary>

- ✅ Verify the `MASTER_FQDN` is correct and accessible
- ✅ Check network connectivity
- ✅ Ensure the master instance is running
- ✅ Verify agent port is accessible if custom port is used

</details>

<details>
<summary><strong>"WebSocket connection failed"</strong></summary>

- ✅ Check if master supports WebSocket on agent port
- ✅ Verify firewall allows WebSocket traffic
- ✅ Agent will fall back to HTTP polling automatically

</details>

<details>
<summary><strong>"Configuration error"</strong></summary>

- ✅ Verify all required environment variables are set
- ✅ Check that `MASTER_FQDN` includes the protocol (http/https)
- ✅ Ensure `API_KEY` is at least 64 characters

</details>

### Performance Issues 📊

- 📈 Monitor CPU and memory usage
- 🔍 Check WebSocket connection status in logs
- ⚡ Verify sync frequency adapts to site intervals
- 🚀 Consider using custom agent port for better performance
- 🌐 Monitor network latency to master instance

## 👨‍💻 Development

### Building from Source

```bash
# Download dependencies
go mod tidy

# Build for current platform
go build -o sreoob-agent

# Build with optimizations
go build -ldflags "-s -w" -o sreoob-agent
```

### Running Tests

```bash
go test ./...
go test -v ./...  # Verbose output
go test -race ./...  # Race condition detection
```

### Cross-compilation

```bash
# Linux AMD64
GOOS=linux GOARCH=amd64 go build -o sreoob-agent-linux-amd64

# Windows AMD64
GOOS=windows GOARCH=amd64 go build -o sreoob-agent-windows-amd64.exe

# macOS AMD64 (Intel)
GOOS=darwin GOARCH=amd64 go build -o sreoob-agent-darwin-amd64

# macOS ARM64 (Apple Silicon)
GOOS=darwin GOARCH=arm64 go build -o sreoob-agent-darwin-arm64

# Linux ARM64 (for Raspberry Pi, etc.)
GOOS=linux GOARCH=arm64 go build -o sreoob-agent-linux-arm64
```

### Build Script

```bash
# Build for current platform
./build.sh

# Build for all platforms
./build.sh all
```

## 🏗️ Architecture

```mermaid
graph TB
    Agent[sreoob Agent] 
    Master[sreoob Master]
    
    Agent -.->|WebSocket<br/>wss://master:8081/agent/ws| Master
    Agent -.->|HTTP Fallback<br/>https://master:8081/api/| Master
    
    Agent -->|Monitor| Site1[Site 1<br/>30s interval]
    Agent -->|Monitor| Site2[Site 2<br/>60s interval] 
    Agent -->|Monitor| Site3[Site 3<br/>ping://host]
    
    Master -->|Real-time Updates| Agent
    Agent -->|Check Results| Master
```

### Communication Flow

```
Agent ←→ Master Communication:

WebSocket (Primary):
┌─────────┐     wss://master:8081/agent/ws     ┌────────┐
│  Agent  │ ←─────────────────────────────────→ │ Master │
└─────────┘                                     └────────┘
           ├── Real-time site updates
           ├── Instant result submission  
           └── Ping/pong keepalive

HTTP Fallback:
┌─────────┐     https://master:8081/api/       ┌────────┐
│  Agent  │ ←─────────────────────────────────→ │ Master │
└─────────┘                                     └────────┘
           ├── Site list polling (when WebSocket fails)
           ├── Result submission backup
           └── Connection testing

Monitoring Flow:
1. Agent connects to master via WebSocket + HTTP
2. Receives initial site list
3. Starts monitoring each site per its interval
4. Submits results via WebSocket (or HTTP if WS fails)
5. Receives real-time updates via WebSocket
6. Adapts sync frequency based on site intervals
```

## 🔨 Building from Source

### Local Development Build

```bash
# Quick build for current platform
cd agent
go build -o sreoob-agent

# Build with version info
./build-local.sh "1.0.0"

# Cross-platform build (all supported platforms)
./build-all.sh "1.0.0"
```

### Manual Cross-Platform Build

```bash
# Linux AMD64
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -ldflags="-s -w" -o sreoob-agent-linux-amd64

# Linux ARM64 (AWS Graviton, Raspberry Pi)
GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -ldflags="-s -w" -o sreoob-agent-linux-arm64

# Linux ARMv7 (Raspberry Pi)
GOOS=linux GOARCH=arm GOARM=7 CGO_ENABLED=0 go build -ldflags="-s -w" -o sreoob-agent-linux-arm

# Linux RISC-V 64-bit
GOOS=linux GOARCH=riscv64 CGO_ENABLED=0 go build -ldflags="-s -w" -o sreoob-agent-linux-riscv64

# macOS ARM64 (Apple Silicon)
GOOS=darwin GOARCH=arm64 CGO_ENABLED=0 go build -ldflags="-s -w" -o sreoob-agent-darwin-arm64

# Windows AMD64
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -ldflags="-s -w" -o sreoob-agent-windows-amd64.exe
```

### Build Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `build-local.sh` | Build for current platform | `./build-local.sh [version]` |
| `build-all.sh` | Cross-platform build | `./build-all.sh [version]` |

Both scripts support version embedding and create optimized binaries with:
- ✅ Static linking (no external dependencies)
- ✅ Stripped symbols for smaller size
- ✅ Version information embedded
- ✅ Build time and Git commit tracking

## 🚀 GitHub Actions & Releases

### Automated Release Pipeline

The repository includes a comprehensive GitHub Actions workflow that automatically:

1. **🔍 Detects Changes**: Triggers on pushes to `main` branch affecting agent code
2. **📊 Version Management**: Auto-increments version numbers (patch/minor/major)
3. **🏗️ Cross-Platform Builds**: Compiles for all supported platforms
4. **📦 Release Creation**: Creates GitHub releases with binaries and documentation
5. **🔒 Security**: Generates SHA256 checksums for all binaries

### Supported Build Platforms

| Platform | Architecture | Binary Name | AWS Compatible |
|----------|-------------|-------------|----------------|
| **Linux** | AMD64 | `sreoob-agent-linux-amd64` | ✅ EC2 x86_64 |
| **Linux** | ARM64 | `sreoob-agent-linux-arm64` | ✅ EC2 Graviton |
| **Linux** | ARMv7 | `sreoob-agent-linux-arm` | ✅ Raspberry Pi |
| **Linux** | RISC-V 64 | `sreoob-agent-linux-riscv64` | ✅ Future processors |
| **macOS** | ARM64 | `sreoob-agent-darwin-arm64` | ✅ Apple Silicon |
| **Windows** | AMD64 | `sreoob-agent-windows-amd64.exe` | ✅ Windows Server |

### Triggering Releases

#### Automatic (Recommended)
```bash
# Any push to main with agent changes triggers a patch release
git add agent/
git commit -m "feat: improve agent performance"
git push origin main
# → Creates release v1.0.1
```

#### Manual Release
```bash
# Trigger via GitHub Actions UI
# Go to: Actions → Build and Release SREoob Agent → Run workflow
# Choose version bump: patch/minor/major
```

#### Version Bump Types

| Type | When to Use | Example |
|------|-------------|---------|
| **patch** | Bug fixes, small improvements | `v1.0.0` → `v1.0.1` |
| **minor** | New features, backward compatible | `v1.0.0` → `v1.1.0` |
| **major** | Breaking changes | `v1.0.0` → `v2.0.0` |

### Release Features

Each release includes:

- ✅ **Pre-compiled binaries** for all platforms
- ✅ **SHA256 checksums** for security verification
- ✅ **Comprehensive release notes** with changelog
- ✅ **Installation instructions** and platform compatibility
- ✅ **Version information** embedded in binaries
- ✅ **Security hardening** with static linking and stripped symbols
- ✅ **Modern GitHub Actions**: Uses [`softprops/action-gh-release@v2`](https://github.com/softprops/action-gh-release) for reliable releases
- ✅ **Atomic uploads**: All assets uploaded together with proper error handling

### Using Released Binaries

```bash
# Download from GitHub releases
curl -fsSL https://github.com/x86txt/SREoob/releases/latest/download/sreoob-agent-linux-amd64 -o sreoob-agent
chmod +x sreoob-agent

# Verify checksum (recommended)
curl -fsSL https://github.com/x86txt/SREoob/releases/latest/download/SHA256SUMS -o SHA256SUMS
sha256sum -c SHA256SUMS --ignore-missing

# Check version
./sreoob-agent -version
```

### Development Workflow

```bash
# 1. Make changes to agent code
vim agent/main.go

# 2. Test locally
cd agent
./build-local.sh
./sreoob-agent-linux-amd64 -version

# 3. Commit and push
git add agent/
git commit -m "feat: add new monitoring feature"
git push origin main

# 4. GitHub Actions automatically:
#    - Builds all platforms
#    - Creates release v1.1.0
#    - Uploads binaries
#    - Updates documentation
```

### CI/CD Pipeline Details

```yaml
# Workflow triggers:
on:
  push:
    branches: [ main ]
    paths: [ 'agent/**', '.github/workflows/release.yml' ]
  workflow_dispatch:
    inputs:
      version_bump: [ patch, minor, major ]

# Required permissions:
permissions:
  contents: write

# Build matrix:
strategy:
  matrix:
    include:
      - { goos: linux, goarch: amd64 }
      - { goos: linux, goarch: arm64 }
      - { goos: linux, goarch: arm, goarm: 7 }
      - { goos: linux, goarch: riscv64 }
      - { goos: darwin, goarch: arm64 }
      - { goos: windows, goarch: amd64 }

# Modern release action:
- uses: softprops/action-gh-release@v2
  with:
    files: ./release-assets/*
    fail_on_unmatched_files: true
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- 📝 **Documentation**: Check this README and inline code comments
- 🐛 **Issues**: Report bugs via GitHub Issues
- 💬 **Discussions**: Use GitHub Discussions for questions
- 🔒 **Security**: Report security issues privately

---

<p align="center">
  <strong>Built with ❤️ using Go</strong><br>
  Fast • Secure • Real-time • Cross-platform
</p> 