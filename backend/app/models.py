from pydantic import BaseModel, HttpUrl, field_validator, validator, constr
from typing import Optional, List
from datetime import datetime
import re
from .config import settings

class SiteCreate(BaseModel):
    url: str
    name: constr(min_length=1)
    scan_interval: str
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL supports http, https, and ping protocols."""
        if not v:
            raise ValueError('URL is required')
        
        # Check for supported protocols
        if v.startswith(('http://', 'https://')):
            # Validate as HTTP URL
            try:
                HttpUrl(v)
                return v
            except Exception:
                raise ValueError('Invalid HTTP/HTTPS URL format')
        elif v.startswith('ping://'):
            # Validate ping URL (domain or IP after ping://)
            host = v[7:]  # Remove 'ping://'
            if not host:
                raise ValueError('Ping URL requires a hostname or IP address')
            
            # Basic validation for hostname/IP
            if not re.match(r'^[a-zA-Z0-9.-]+$', host):
                raise ValueError('Invalid hostname or IP address for ping')
            
            return v
        else:
            raise ValueError('URL must start with http://, https://, or ping://')
        
        return v
    
    @validator('scan_interval')
    def validate_scan_interval(cls, v):
        """Validate scan interval format and range."""
        # Parse the interval string
        match = re.match(r'^(\d+(?:\.\d+)?)([smh])$', v.strip().lower())
        if not match:
            raise ValueError("Invalid format. Use 's', 'm', 'h' (e.g., '30s', '5m', '1h').")

        value, unit = match.groups()
        value = float(value)

        # Convert to seconds
        if unit == 's':
            seconds = value
        elif unit == 'm':
            seconds = value * 60
        elif unit == 'h':
            seconds = value * 3600

        # Check against configured limits
        min_seconds = settings.MIN_SCAN_INTERVAL_SECONDS
        max_seconds = settings.MAX_SCAN_INTERVAL_SECONDS
        
        if not (min_seconds <= seconds <= max_seconds):
            raise ValueError(f"Scan interval must be between {min_seconds}s and {max_seconds}s.")
        
        return v

class Site(BaseModel):
    id: int
    url: str
    name: str
    scan_interval: str = "60s"
    created_at: datetime

class SiteCheck(BaseModel):
    id: int
    site_id: int
    status: str
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    checked_at: datetime

class SiteStatus(BaseModel):
    id: int
    url: str
    name: str
    scan_interval: str = "60s"
    created_at: datetime
    status: Optional[str] = None
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    checked_at: Optional[datetime] = None
    total_up: int = 0
    total_down: int = 0

class MonitorStats(BaseModel):
    total_sites: int
    sites_up: int
    sites_down: int
    average_response_time: Optional[float] = None 