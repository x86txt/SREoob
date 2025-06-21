from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

class SiteCreate(BaseModel):
    url: HttpUrl
    name: str

class Site(BaseModel):
    id: int
    url: str
    name: str
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