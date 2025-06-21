# 🚀 SREoob Monitor

> 📡 A simple yet powerful website uptime monitoring service built with modern tech stack!

Keep your websites online and your mind at peace! 😌 Built with <svg width="20" height="20" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="#009688" d="M12 .0387C5.3729.0384.0003 5.3931 0 11.9988c-.001 6.6066 5.372 11.9628 12 11.9625 6.628.0003 12.001-5.3559 12-11.9625-.0003-6.6057-5.3729-11.9604-12-11.96m-.829 5.4153h7.55l-7.5805 5.3284h5.1828L5.279 18.5436q2.9466-6.5444 5.892-13.0896"/></svg> **FastAPI** backend and <svg width="20" height="20" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="#000000" d="M18.665 21.978C16.758 23.255 14.465 24 12 24 5.377 24 0 18.623 0 12S5.377 0 12 0s12 5.377 12 12c0 3.583-1.574 6.801-4.067 9.001L9.219 7.2H7.2v9.596h1.615V9.251l9.85 12.727Zm-3.332-8.533 1.6 2.061V7.2h-1.6v6.245Z"/></svg> **Next.js** frontend, SREoob Monitor provides real-time status updates, response time tracking, and comprehensive historical data.

## ⚡ Super Quick Deployment

### 🚀 Complete Stack (Recommended)
**Deploy the entire SREoob platform with guided setup:**

```bash
curl -fsSL https://raw.githubusercontent.com/x86txt/SREoob/main/install-server.sh | bash
```

✅ **Interactive setup** • ✅ **SSL/HTTPS support** • ✅ **Admin authentication** • ✅ **Complete stack or individual components** • ✅ **Production-ready nginx**

**Or deploy directly with Docker Compose:**

```bash
curl -fsSL https://github.com/x86txt/SREoob/releases/latest/download/docker-compose.yml | docker-compose -f - up -d
```

✅ **Backend + Frontend + Database** • ✅ **Production-ready nginx** • ✅ **Automatic updates** • ✅ **One-command deployment**

### 📡 Agent Deployment
**Deploy a monitoring agent in 30 seconds:**

```bash
curl -fsSL https://raw.githubusercontent.com/x86txt/SREoob/main/agent/install.sh | bash
```

✅ **Auto-detects your platform** • ✅ **Downloads pre-compiled binary** • ✅ **Generates secure API key** • ✅ **Creates systemd service** • ✅ **Provides clear next steps**

### 🐳 Individual Components
**Deploy specific components:**

```bash
# Backend only
docker run -d -p 8000:8000 -v sreoob-data:/data ghcr.io/x86txt/sreoob-backend:latest

# Frontend only  
docker run -d -p 3000:3000 ghcr.io/x86txt/sreoob-frontend:latest
```

> 🎯 **Perfect for:** Complete infrastructure monitoring with agents on remote servers, VPS instances, edge locations, or any Linux/macOS/Windows system.
> 
> 📖 **Documentation:** 
> - [📡 Agent Setup](agent/README.md) 
> - [🔧 Backend Config](backend/CONFIG.md)
> - [🎨 Frontend Guide](frontend/README.md)

---

## ✨ Features

🎯 **Real-time Monitoring** - Automatically checks websites every 60 seconds  
🎨 **Clean UI** - Modern, responsive interface with TailwindCSS v4 and ShadCN/UI  
📊 **Status Tracking** - Up/down status with response times and error details  
📚 **Historical Data** - SQLite database stores all check history  
⚡ **Concurrent Checking** - Uses aiohttp for non-blocking HTTP requests  
🔧 **Manual Checks** - Trigger immediate checks when needed  
🛠️ **Site Management** - Easy add/remove sites with validation  

---

## 🏗️ Architecture

| Component | Technology | Purpose |
|-----------|------------|---------|
| 🔧 **Backend** | FastAPI + aiohttp | Async HTTP requests & API |
| 🎨 **Frontend** | Next.js + TypeScript + TailwindCSS v4 | Modern UI & UX |
| 🗄️ **Database** | SQLite + aiosqlite | Async data operations |
| 🚢 **Deployment** | Docker + nginx | Containerized deployment |

### 🛠️ Tech Stack

<div align="center">

<svg width="48" height="48" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="margin: 0 10px;"><title>FastAPI</title><path fill="#009688" d="M12 .0387C5.3729.0384.0003 5.3931 0 11.9988c-.001 6.6066 5.372 11.9628 12 11.9625 6.628.0003 12.001-5.3559 12-11.9625-.0003-6.6057-5.3729-11.9604-12-11.96m-.829 5.4153h7.55l-7.5805 5.3284h5.1828L5.279 18.5436q2.9466-6.5444 5.892-13.0896"/></svg>
<svg width="48" height="48" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="margin: 0 10px;"><title>Next.js</title><path fill="#000000" d="M18.665 21.978C16.758 23.255 14.465 24 12 24 5.377 24 0 18.623 0 12S5.377 0 12 0s12 5.377 12 12c0 3.583-1.574 6.801-4.067 9.001L9.219 7.2H7.2v9.596h1.615V9.251l9.85 12.727Zm-3.332-8.533 1.6 2.061V7.2h-1.6v6.245Z"/></svg>
<svg width="48" height="48" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="margin: 0 10px;"><title>SQLite</title><path fill="#003B57" d="M21.678.521c-1.032-.92-2.28-.55-3.513.544a8.71 8.71 0 0 0-.547.535c-2.109 2.237-4.066 6.38-4.674 9.544.237.48.422 1.093.544 1.561a13.044 13.044 0 0 1 .164.703s-.019-.071-.096-.296l-.05-.146a1.689 1.689 0 0 0-.033-.08c-.138-.32-.518-.995-.686-1.289-.143.423-.27.818-.376 1.176.484.884.778 2.4.778 2.4s-.025-.099-.147-.442c-.107-.303-.644-1.244-.772-1.464-.217.804-.304 1.346-.226 1.478.152.256.296.698.422 1.186.286 1.1.485 2.44.485 2.44l.017.224a22.41 22.41 0 0 0 .056 2.748c.095 1.146.273 2.13.5 2.657l.155-.084c-.334-1.038-.47-2.399-.41-3.967.09-2.398.642-5.29 1.661-8.304 1.723-4.55 4.113-8.201 6.3-9.945-1.993 1.8-4.692 7.63-5.5 9.788-.904 2.416-1.545 4.684-1.931 6.857.666-2.037 2.821-2.912 2.821-2.912s1.057-1.304 2.292-3.166c-.74.169-1.955.458-2.362.629-.6.251-.762.337-.762.337s1.945-1.184 3.613-1.72C21.695 7.9 24.195 2.767 21.678.521m-18.573.543A1.842 1.842 0 0 0 1.27 2.9v16.608a1.84 1.84 0 0 0 1.835 1.834h9.418a22.953 22.953 0 0 1-.052-2.707c-.006-.062-.011-.141-.016-.2a27.01 27.01 0 0 0-.473-2.378c-.121-.47-.275-.898-.369-1.057-.116-.197-.098-.31-.097-.432 0-.12.015-.245.037-.386a9.98 9.98 0 0 1 .234-1.045l.217-.028c-.017-.035-.014-.065-.031-.097l-.041-.381a32.8 32.8 0 0 1 .382-1.194l.2-.019c-.008-.016-.01-.038-.018-.053l-.043-.316c.63-3.28 2.587-7.443 4.8-9.791.066-.069.133-.128.198-.194Z"/></svg>
<svg width="48" height="48" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="margin: 0 10px;"><title>Docker</title><path fill="#2496ED" d="M13.983 11.078h2.119a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.119a.185.185 0 00-.185.185v1.888c0 .102.083.185.185.185m-2.954-5.43h2.118a.186.186 0 00.186-.186V3.574a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.888c0 .102.082.185.185.185m0 2.716h2.118a.187.187 0 00.186-.186V6.29a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.887c0 .102.082.185.185.186m-2.93 0h2.12a.186.186 0 00.184-.186V6.29a.185.185 0 00-.185-.185H8.1a.185.185 0 00-.185.185v1.887c0 .102.083.185.185.186m-2.964 0h2.119a.186.186 0 00.185-.186V6.29a.185.185 0 00-.185-.185H5.136a.186.186 0 00-.186.185v1.887c0 .102.084.185.186.186m5.893 2.715h2.118a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.118a.185.185 0 00-.185.185v1.888c0 .102.082.185.185.185m-2.93 0h2.12a.185.185 0 00.184-.185V9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.184.185v1.888c0 .102.083.185.185.185m-2.964 0h2.119a.185.185 0 00.185-.185V9.006a.185.185 0 00-.184-.186h-2.12a.186.186 0 00-.186.186v1.887c0 .102.084.185.186.185m-2.92 0h2.12a.185.185 0 00.184-.185V9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.184.185v1.888c0 .102.082.185.185.185M23.763 9.89c-.065-.051-.672-.51-1.954-.51-.338.001-.676.03-1.01.087-.248-1.7-1.653-2.53-1.716-2.566l-.344-.199-.226.327c-.284.438-.49.922-.612 1.43-.23.97-.09 1.882.403 2.661-.595.332-1.55.413-1.744.42H.751a.751.751 0 00-.75.748 11.376 11.376 0 00.692 4.062c.545 1.428 1.355 2.48 2.41 3.124 1.18.723 3.1 1.137 5.275 1.137.983.003 1.963-.086 2.93-.266a12.248 12.248 0 003.823-1.389c.98-.567 1.86-1.288 2.61-2.136 1.252-1.418 1.998-2.997 2.553-4.4h.221c1.372 0 2.215-.549 2.68-1.009.309-.293.55-.65.707-1.046l.098-.288Z"/></svg>
<svg width="48" height="48" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="margin: 0 10px;"><title>NGINX</title><path fill="#009639" d="M12 0L1.605 6v12L12 24l10.395-6V6L12 0zm6 16.59c0 .705-.646 1.29-1.529 1.29-.631 0-1.351-.255-1.801-.81l-6-7.141v6.66c0 .721-.57 1.29-1.274 1.29H7.32c-.721 0-1.29-.6-1.29-1.29V7.41c0-.705.63-1.29 1.5-1.29.646 0 1.38.255 1.83.81l5.97 7.141V7.41c0-.721.6-1.29 1.29-1.29h.075c.72 0 1.29.6 1.29 1.29v9.18H18z"/></svg>

**FastAPI** • **Next.js** • **SQLite** • **Docker** • **nginx**

</div>

---

## 🚀 Quick Start

### 📋 Prerequisites

- 🐍 Python 3.11+ with `uv` package manager
- 📦 Node.js 18+ 
- 🐳 Docker (optional)

### 🛠️ Development Setup

#### 1️⃣ **Backend Setup**
```bash
# 📥 Install Python dependencies
uv sync

# 🔄 Activate virtual environment
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# 🚀 Start the backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2️⃣ **Frontend Setup**
```bash
cd frontend
pnpm install    # 📦 Install dependencies
pnpm dev        # 🎨 Start development server
```

#### 3️⃣ **Access Your App**
| Service | URL | Description |
|---------|-----|-------------|
| 🎨 **Frontend** | http://localhost:3000 | Main monitoring interface |
| 🔧 **Backend API** | http://localhost:8000 | FastAPI backend |
| 📚 **API Docs** | http://localhost:8000/docs | Interactive API documentation |

### <svg width="20" height="20" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="vertical-align: text-bottom;"><path fill="#2496ED" d="M13.983 11.078h2.119a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.119a.185.185 0 00-.185.185v1.888c0 .102.083.185.185.185m-2.954-5.43h2.118a.186.186 0 00.186-.186V3.574a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.888c0 .102.082.185.185.185m0 2.716h2.118a.187.187 0 00.186-.186V6.29a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.887c0 .102.082.185.185.186m-2.93 0h2.12a.186.186 0 00.184-.186V6.29a.185.185 0 00-.185-.185H8.1a.185.185 0 00-.185.185v1.887c0 .102.083.185.185.186m-2.964 0h2.119a.186.186 0 00.185-.186V6.29a.185.185 0 00-.185-.185H5.136a.186.186 0 00-.186.185v1.887c0 .102.084.185.186.186m5.893 2.715h2.118a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.118a.185.185 0 00-.185.185v1.888c0 .102.082.185.185.185m-2.93 0h2.12a.185.185 0 00.184-.185V9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.184.185v1.888c0 .102.083.185.185.185m-2.964 0h2.119a.185.185 0 00.185-.185V9.006a.185.185 0 00-.184-.186h-2.12a.186.186 0 00-.186.186v1.887c0 .102.084.185.186.185m-2.92 0h2.12a.185.185 0 00.184-.185V9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.184.185v1.888c0 .102.082.185.185.185M23.763 9.89c-.065-.051-.672-.51-1.954-.51-.338.001-.676.03-1.01.087-.248-1.7-1.653-2.53-1.716-2.566l-.344-.199-.226.327c-.284.438-.49.922-.612 1.43-.23.97-.09 1.882.403 2.661-.595.332-1.55.413-1.744.42H.751a.751.751 0 00-.75.748 11.376 11.376 0 00.692 4.062c.545 1.428 1.355 2.48 2.41 3.124 1.18.723 3.1 1.137 5.275 1.137.983.003 1.963-.086 2.93-.266a12.248 12.248 0 003.823-1.389c.98-.567 1.86-1.288 2.61-2.136 1.252-1.418 1.998-2.997 2.553-4.4h.221c1.372 0 2.215-.549 2.68-1.009.309-.293.55-.65.707-1.046l.098-.288Z"/></svg> Docker Setup

```bash
# 🏗️ Build and run all services
docker-compose up --build

# 🌐 Access via nginx proxy
# http://localhost
```

> 💡 **Pro tip**: The Docker setup includes nginx reverse proxy for a production-like environment!

## 🔗 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| 📋 `GET` | `/api/sites` | List all monitored sites |
| ➕ `POST` | `/api/sites` | Add a new site to monitor |
| 🗑️ `DELETE` | `/api/sites/{id}` | Remove a site |
| 📊 `GET` | `/api/sites/status` | Get current status of all sites |
| 📈 `GET` | `/api/sites/{id}/history` | Get check history for a site |
| 📈 `GET` | `/api/stats` | Get monitoring statistics |
| 🔄 `POST` | `/api/check/manual` | Trigger manual check of all sites |

---

## ⚙️ Configuration

### 🔧 Environment Configuration

Create a `.env` file in the backend directory for custom settings:

```bash
# Copy the example configuration
cp backend/env-example backend/.env
```

#### ⚙️ **Key Configuration Options**

| Setting | Default | Description |
|---------|---------|-------------|
| `SCAN_RANGE_MIN` | `"30s"` | 🕒 Minimum interval between site checks |
| `SCAN_RANGE_MAX` | `"5m"` | 🕒 Maximum interval between site checks |
| `DATABASE_PATH` | `siteup.db` | 🗄️ SQLite database file location |
| `LOG_LEVEL` | `INFO` | 📝 Logging verbosity (DEBUG/INFO/WARNING/ERROR) |

#### 🚀 **Environment Profiles**

**Production** (default):
```bash
SCAN_RANGE_MIN="30s"
SCAN_RANGE_MAX="5m"
```

**Development** (for testing):
```bash
SCAN_RANGE_MIN="1s"
SCAN_RANGE_MAX="1h"
```

> 💡 **Time formats**: Use `s` (seconds), `m` (minutes), `h` (hours). Decimals supported: `0.5s`, `2.5m`, `1.5h`

### 🔧 Backend Configuration

The backend automatically handles everything! 🎉

- ✅ Creates SQLite database on first run
- ⏰ Starts monitoring all sites based on their individual intervals
- 🚀 Handles up to 100 concurrent site checks
- 💾 Stores unlimited historical data
- ⚙️ Configurable via environment variables

### 🎨 Frontend Configuration 

The frontend seamlessly connects via:

- 🔄 API proxy in `next.config.js` (development)
- 🌐 Direct API calls to `/api/*` endpoints
- ⚡ Auto-refresh every 30 seconds for real-time updates
- 🎛️ Dynamic configuration via `/api/config` endpoint

## 🗄️ Database Schema

<details>
<summary><strong>📋 Sites Table</strong> (Click to expand)</summary>

| Column | Type | Description |
|--------|------|-------------|
| `id` | Primary Key | 🔑 Unique identifier |
| `url` | Text | 🌐 Website URL to monitor |
| `name` | Text | 🏷️ Display name for the site |
| `created_at` | Timestamp | 📅 When site was added |

</details>

<details>
<summary><strong>📊 Site Checks Table</strong> (Click to expand)</summary>

| Column | Type | Description |
|--------|------|-------------|
| `id` | Primary Key | 🔑 Unique identifier |
| `site_id` | Foreign Key | 🔗 Link to sites table |
| `status` | Text | 🟢🔴 'up' or 'down' |
| `response_time` | Float | ⏱️ Response time in seconds |
| `status_code` | Integer | 📊 HTTP status code |
| `error_message` | Text | ❌ Error details if down |
| `checked_at` | Timestamp | 🕒 When check was performed |

</details>

---

## 🔍 Monitoring Logic

| Step | Detail | Value |
|------|--------|-------|
| ⏰ **Check Interval** | How often sites are checked | Every 60 seconds |
| ⏱️ **Timeout** | Max wait time per request | 30 seconds |
| ✅ **Success Criteria** | What counts as "up" | HTTP status < 400 |
| 🚀 **Concurrent Checks** | Parallel processing | All sites simultaneously |
| 🛡️ **Error Handling** | What we track | Network errors, timeouts, HTTP errors |

> 🎯 **Smart monitoring**: All checks run concurrently for maximum efficiency!

## 🚀 Deployment

### <svg width="20" height="20" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="vertical-align: text-bottom;"><path fill="#2496ED" d="M13.983 11.078h2.119a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.119a.185.185 0 00-.185.185v1.888c0 .102.083.185.185.185m-2.954-5.43h2.118a.186.186 0 00.186-.186V3.574a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.888c0 .102.082.185.185.185m0 2.716h2.118a.187.187 0 00.186-.186V6.29a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.887c0 .102.082.185.185.186m-2.93 0h2.12a.186.186 0 00.184-.186V6.29a.185.185 0 00-.185-.185H8.1a.185.185 0 00-.185.185v1.887c0 .102.083.185.185.186m-2.964 0h2.119a.186.186 0 00.185-.186V6.29a.185.185 0 00-.185-.185H5.136a.186.186 0 00-.186.185v1.887c0 .102.084.185.186.186m5.893 2.715h2.118a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.118a.185.185 0 00-.185.185v1.888c0 .102.082.185.185.185m-2.93 0h2.12a.185.185 0 00.184-.185V9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.184.185v1.888c0 .102.083.185.185.185m-2.964 0h2.119a.185.185 0 00.185-.185V9.006a.185.185 0 00-.184-.186h-2.12a.186.186 0 00-.186.186v1.887c0 .102.084.185.186.185m-2.92 0h2.12a.185.185 0 00.184-.185V9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.184.185v1.888c0 .102.082.185.185.185M23.763 9.89c-.065-.051-.672-.51-1.954-.51-.338.001-.676.03-1.01.087-.248-1.7-1.653-2.53-1.716-2.566l-.344-.199-.226.327c-.284.438-.49.922-.612 1.43-.23.97-.09 1.882.403 2.661-.595.332-1.55.413-1.744.42H.751a.751.751 0 00-.75.748 11.376 11.376 0 00.692 4.062c.545 1.428 1.355 2.48 2.41 3.124 1.18.723 3.1 1.137 5.275 1.137.983.003 1.963-.086 2.93-.266a12.248 12.248 0 003.823-1.389c.98-.567 1.86-1.288 2.61-2.136 1.252-1.418 1.998-2.997 2.553-4.4h.221c1.372 0 2.215-.549 2.68-1.009.309-.293.55-.65.707-1.046l.098-.288Z"/></svg> Production with Docker

```bash
# 🏭 Production build
docker-compose -f docker-compose.prod.yml up --build -d
```

### 🔧 Manual Production Setup

<details>
<summary><strong>🛠️ Step-by-step manual deployment</strong> (Click to expand)</summary>

#### 1️⃣ **Backend**
```bash
uv sync --no-dev
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

#### 2️⃣ **Frontend**
```bash
pnpm build
pnpm start
```

#### 3️⃣ **Nginx**
Use the provided `nginx/nginx.conf` configuration

</details>

---

## 🔒 Security Considerations

| Aspect | Status | Note |
|--------|--------|------|
| 🔐 **Authentication** | None | Designed for personal/internal use |
| 🌐 **CORS** | Configured | Set up for localhost development |
| ✅ **Input Validation** | Enabled | URLs validated before adding |
| 🛡️ **SQL Injection** | Protected | Parameterized queries used |

> ⚠️ **Important**: This tool is designed for personal use. Consider adding authentication for public deployments!

---

## 🛠️ Development

### 📁 Project Structure
```
🗂️ siteUp/
├── 🔧 backend/              # FastAPI backend
│   └── app/
│       ├── main.py          # 🚀 FastAPI app
│       ├── database.py      # 🗄️ Database operations
│       ├── monitor.py       # 📡 Site monitoring logic
│       ├── models.py        # 📋 Pydantic models
│       └── api/             # 🔗 API endpoints
├── 🎨 frontend/             # Next.js frontend
│   └── src/
│       ├── app/             # 📄 App router pages
│       ├── components/      # ⚛️ React components
│       └── lib/             # 🔧 Utilities and API client
├── 🌐 nginx/                # Nginx configuration
└── 🐳 docker-compose.yml    # Docker setup
```

### 🚀 Adding Features

| Component | File Location | Purpose |
|-----------|---------------|---------|
| 🔗 **New API Endpoints** | `backend/app/api/endpoints.py` | Add new backend functionality |
| 🗄️ **Database Changes** | `backend/app/database.py` | Modify data structure |
| 🎨 **UI Components** | `frontend/src/components/` | Create new interface elements |
| 📡 **Monitoring Logic** | `backend/app/monitor.py` | Extend monitoring capabilities |

---

## 📜 License

This project is for personal use. Feel free to modify and extend as needed! 🎉

## 🤝 Contributing

This is a personal project, but suggestions and improvements are always welcome! 

**Found a bug?** 🐛 **Have an idea?** 💡 **Want to contribute?** 🙋‍♂️ 

Feel free to open an issue or submit a pull request! 

---

<div align="center">

**Made with ❤️ for keeping websites online!** 

*Happy monitoring!* 📊✨

</div> 