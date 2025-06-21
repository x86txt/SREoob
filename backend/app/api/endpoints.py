from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from ..models import SiteCreate, SiteStatus, SiteCheck, MonitorStats
from ..database import (
    add_site, get_sites, get_site_status, get_site_history, 
    delete_site as db_delete_site
)
from ..monitor import get_monitor

router = APIRouter()

@router.post("/sites", response_model=dict)
async def create_site(site: SiteCreate):
    """Add a new site to monitor."""
    try:
        site_id = await add_site(str(site.url), site.name)
        return {"id": site_id, "message": "Site added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sites", response_model=List[dict])
async def list_sites():
    """Get all sites being monitored."""
    return await get_sites()

@router.get("/sites/status", response_model=List[dict])
async def get_sites_status():
    """Get current status of all sites."""
    return await get_site_status()

@router.get("/sites/{site_id}/history", response_model=List[dict])
async def get_site_check_history(site_id: int, limit: int = 100):
    """Get check history for a specific site."""
    if limit > 1000:
        limit = 1000
    return await get_site_history(site_id, limit)

@router.delete("/sites/{site_id}")
async def delete_site(site_id: int):
    """Delete a site and all its check history."""
    try:
        await db_delete_site(site_id)
        return {"message": "Site deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/check/manual")
async def manual_check():
    """Manually trigger a check of all sites."""
    try:
        monitor = await get_monitor()
        async with monitor:
            results = await monitor.check_all_sites()
        return {"message": f"Checked {len(results)} sites", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=dict)
async def get_monitoring_stats():
    """Get monitoring statistics."""
    try:
        sites_status = await get_site_status()
        total_sites = len(sites_status)
        sites_up = sum(1 for site in sites_status if site.get('status') == 'up')
        sites_down = total_sites - sites_up
        
        # Calculate average response time for sites that are up
        up_sites_with_time = [
            site for site in sites_status 
            if site.get('status') == 'up' and site.get('response_time') is not None
        ]
        avg_response_time = None
        if up_sites_with_time:
            avg_response_time = sum(site['response_time'] for site in up_sites_with_time) / len(up_sites_with_time)
        
        return {
            "total_sites": total_sites,
            "sites_up": sites_up,
            "sites_down": sites_down,
            "average_response_time": avg_response_time
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 