# SiteUp Configuration

## Environment Variables

The SiteUp backend can be configured using environment variables. These can be set in your shell or in a `.env` file in the backend directory.

### Scan Interval Configuration

Control the allowed range for scan intervals when adding sites using human-readable time formats:

#### Production Settings (Default)
```bash
# Conservative ranges for production use
SCAN_RANGE_MIN="30s"    # 30 seconds minimum
SCAN_RANGE_MAX="5m"     # 5 minutes maximum
```

#### Development Settings
```bash
# Flexible ranges for development and testing
SCAN_RANGE_MIN="1s"     # 1 second minimum (fast testing)
SCAN_RANGE_MAX="1h"     # 1 hour maximum (long intervals)
```

#### Supported Time Formats
- **Seconds**: `1s`, `30s`, `0.5s` (decimal seconds supported)
- **Minutes**: `1m`, `5m`, `2.5m` (decimal minutes supported)  
- **Hours**: `1h`, `2h`, `0.5h` (decimal hours supported)

### Other Configuration

```bash
# Database
DATABASE_PATH=siteup.db

# API Server
API_PORT=8000
API_HOST=0.0.0.0

# Logging
LOG_LEVEL=INFO
```

## Usage Examples

### Development with Fast Testing
```bash
export SCAN_RANGE_MIN="1s"
export SCAN_RANGE_MAX="1h"
python -m app.main
```

### Production with Conservative Limits
```bash
export SCAN_RANGE_MIN="30s"
export SCAN_RANGE_MAX="5m"
python -m app.main
```

### Using .env file
Create a `.env` file in the backend directory:
```env
SCAN_RANGE_MIN="1s"
SCAN_RANGE_MAX="1h"
LOG_LEVEL=DEBUG
```

### More Examples
```bash
# Very conservative production
SCAN_RANGE_MIN="1m"
SCAN_RANGE_MAX="10m"

# Ultra-fast development testing
SCAN_RANGE_MIN="0.5s"
SCAN_RANGE_MAX="2h"

# Mixed units work fine
SCAN_RANGE_MIN="30s"
SCAN_RANGE_MAX="1h"
```

## Notes

- The frontend will automatically detect development mode when wider ranges are configured
- **Human-readable formats**: Use `"1s"`, `"5m"`, `"1h"` instead of raw seconds
- **Decimal values supported**: `"0.5s"`, `"2.5m"`, `"1.5h"` all work
- **Mixed units**: You can set min in seconds and max in hours if desired
- **Unit validation**: Only `s` (seconds), `m` (minutes), and `h` (hours) are supported
- All validation happens on both frontend and backend
- Changes require restarting the backend server 