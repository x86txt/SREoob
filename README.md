# SiteUp Monitor

A simple website uptime monitoring service built with FastAPI backend and Next.js frontend. Monitor your websites with real-time status updates, response time tracking, and historical data.

## Features

- **Real-time Monitoring**: Automatically checks websites every 60 seconds
- **Clean UI**: Modern, responsive interface with TailwindCSS v4 and ShadCN/UI
- **Status Tracking**: Up/down status with response times and error details
- **Historical Data**: SQLite database stores all check history
- **Concurrent Checking**: Uses aiohttp for non-blocking HTTP requests
- **Manual Checks**: Trigger immediate checks when needed
- **Site Management**: Easy add/remove sites with validation

## Architecture

- **Backend**: FastAPI with aiohttp for async HTTP requests
- **Frontend**: Next.js with TypeScript, TailwindCSS v4, and ShadCN/UI
- **Database**: SQLite with aiosqlite for async operations
- **Deployment**: Docker with nginx reverse proxy

## Quick Start

### Prerequisites

- Python 3.11+ with uv package manager
- Node.js 18+
- Docker (optional)

### Development Setup

1. **Clone and setup backend**:
   ```bash
   # Install Python dependencies
   uv sync
   
   # Activate virtual environment
   source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
   
   # Start the backend
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Setup frontend**:
   ```bash
   cd frontend
   pnpm install
   pnpm dev
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Docker Setup

```bash
# Build and run all services
docker-compose up --build

# Access via nginx proxy
# http://localhost
```

## API Endpoints

- `GET /api/sites` - List all monitored sites
- `POST /api/sites` - Add a new site to monitor
- `DELETE /api/sites/{id}` - Remove a site
- `GET /api/sites/status` - Get current status of all sites
- `GET /api/sites/{id}/history` - Get check history for a site
- `GET /api/stats` - Get monitoring statistics
- `POST /api/check/manual` - Trigger manual check of all sites

## Configuration

### Backend Configuration

The backend automatically:
- Creates SQLite database on first run
- Starts monitoring all sites every 60 seconds
- Handles up to 100 concurrent site checks
- Stores unlimited historical data

### Frontend Configuration 

The frontend connects to the backend via:
- API proxy in `next.config.js` (development)
- Direct API calls to `/api/*` endpoints
- Auto-refresh every 30 seconds

## Database Schema

### Sites Table
- `id` - Primary key
- `url` - Website URL to monitor
- `name` - Display name for the site
- `created_at` - When site was added

### Site Checks Table
- `id` - Primary key
- `site_id` - Foreign key to sites
- `status` - 'up' or 'down'
- `response_time` - Response time in seconds
- `status_code` - HTTP status code
- `error_message` - Error details if down
- `checked_at` - When check was performed

## Monitoring Logic

1. **Check Interval**: Every 60 seconds
2. **Timeout**: 30 seconds per request
3. **Success Criteria**: HTTP status < 400
4. **Concurrent Checks**: All sites checked simultaneously
5. **Error Handling**: Network errors, timeouts, and HTTP errors logged

## Deployment

### Production with Docker

```bash
# Production build
docker-compose -f docker-compose.prod.yml up --build -d
```

### Manual Production Setup

1. **Backend**:
   ```bash
   uv sync --no-dev
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Frontend**:
   ```bash
   pnpm build
   pnpm start
   ```

3. **Nginx**: Use provided `nginx/nginx.conf`

## Security Considerations

- **No Authentication**: This is designed for personal/internal use
- **CORS**: Configured for localhost development
- **Input Validation**: URLs validated before adding
- **SQL Injection**: Protected by parameterized queries

## Development

### Project Structure
```
siteUp/
├── backend/           # FastAPI backend
│   └── app/
│       ├── main.py    # FastAPI app
│       ├── database.py # Database operations
│       ├── monitor.py  # Site monitoring logic
│       ├── models.py   # Pydantic models
│       └── api/        # API endpoints
├── frontend/          # Next.js frontend
│   └── src/
│       ├── app/       # App router pages
│       ├── components/ # React components
│       └── lib/       # Utilities and API client
├── nginx/             # Nginx configuration
└── docker-compose.yml # Docker setup
```

### Adding Features

1. **New API Endpoints**: Add to `backend/app/api/endpoints.py`
2. **Database Changes**: Modify `backend/app/database.py`
3. **UI Components**: Add to `frontend/src/components/`
4. **Monitoring Logic**: Extend `backend/app/monitor.py`

## License

This project is for personal use. Feel free to modify and extend as needed.

## Contributing

This is a personal project, but suggestions and improvements are welcome! 