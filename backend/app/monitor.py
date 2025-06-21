import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
import httpx
from .database import get_sites, record_check, get_site_status
from .config import settings
import re

# Import ping3 for native ICMP ping
try:
    import ping3
    PING3_AVAILABLE = True
except ImportError:
    PING3_AVAILABLE = False
    logging.warning("ping3 library not available. Ping monitoring will be disabled.")

logger = logging.getLogger(__name__)

class SiteMonitor:
    """
    The SiteMonitor is responsible for periodically checking the status of all registered sites.
    """
    def __init__(self):
        self.sites: List[Dict[str, Any]] = []
        self._task: Optional[asyncio.Task] = None
        self.is_running = False

    async def start(self):
        """Starts the monitoring background task."""
        if not self.is_running:
            self.is_running = True
            await self.refresh_monitoring()
            logger.info("Site monitor started.")

    async def stop(self):
        """Stops the monitoring background task."""
        if self.is_running and self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                logger.info("Monitoring task successfully cancelled.")
            self.is_running = False
            logger.info("Site monitor stopped.")

    async def refresh_monitoring(self):
        """
        Refreshes the list of sites from the database and restarts the
        monitoring loop with the updated list.
        """
        if self._task:
            # Cancel the existing task before refreshing
            if not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass # Expected
        
        self.sites = await get_sites()
        
        if self.is_running:
            self._task = asyncio.create_task(self._monitor_loop())
        
        logger.info(f"Monitoring refreshed. Tracking {len(self.sites)} sites.")

    async def _monitor_loop(self):
        """The main loop that checks sites at their specified intervals."""
        last_check_times = {site['id']: 0 for site in self.sites}

        while True:
            try:
                current_time = time.time()
                sites_to_check_tasks = []

                for site in self.sites:
                    interval_seconds = self._parse_interval(site['scan_interval'])
                    if current_time - last_check_times.get(site['id'], 0) >= interval_seconds:
                        sites_to_check_tasks.append(site)
                
                if sites_to_check_tasks:
                    results = await self.check_sites(sites_to_check_tasks)
                    for site, result in zip(sites_to_check_tasks, results):
                        if result: # Ensure result is not None
                            await record_check(site['id'], **result)
                            last_check_times[site['id']] = current_time

                await asyncio.sleep(1) 
            except asyncio.CancelledError:
                logger.info("Monitor loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
                await asyncio.sleep(5) # Avoid rapid-fire errors

    async def check_sites(self, sites: List[Dict[str, Any]]) -> List[Optional[Dict[str, Any]]]:
        """Checks a list of sites concurrently."""
        # Separate HTTP/HTTPS sites from ping sites
        http_sites = [site for site in sites if not site['url'].startswith('ping://')]
        ping_sites = [site for site in sites if site['url'].startswith('ping://')]
        
        results = []
        
        # Check HTTP/HTTPS sites with httpx client
        if http_sites:
            async with httpx.AsyncClient(verify=False, timeout=10) as client:
                http_tasks = [self.check_single_site(client, site) for site in http_sites]
                http_results = await asyncio.gather(*http_tasks, return_exceptions=True)
                results.extend(http_results)
        
        # Check ping sites separately
        if ping_sites:
            ping_tasks = [self.check_ping_site(site) for site in ping_sites]
            ping_results = await asyncio.gather(*ping_tasks, return_exceptions=True)
            results.extend(ping_results)
        
        # Reorder results to match original site order
        if http_sites and ping_sites:
            ordered_results = []
            http_idx = ping_idx = 0
            for site in sites:
                if site['url'].startswith('ping://'):
                    ordered_results.append(ping_results[ping_idx])
                    ping_idx += 1
                else:
                    ordered_results.append(http_results[http_idx])
                    http_idx += 1
            return ordered_results
        
        return results

    async def check_all_sites(self) -> List[Optional[Dict[str, Any]]]:
        """Manually triggers a check of all sites."""
        return await self.check_sites(self.sites)
    
    async def check_sites_by_id(self, site_ids: Optional[List[int]] = None) -> List[Optional[Dict[str, Any]]]:
        """Manually triggers a check for a specific list of site IDs."""
        if site_ids is None:
            return await self.check_all_sites()
        
        sites_to_check = [site for site in self.sites if site['id'] in site_ids]
        return await self.check_sites(sites_to_check)

    @staticmethod
    async def check_single_site(client: httpx.AsyncClient, site: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Performs a single check for a given site (HTTP/HTTPS)."""
        url = site['url']
        start_time = time.time()
        try:
            response = await client.get(url)
            response_time = time.time() - start_time
            return {
                "status": "up" if response.is_success else "down",
                "status_code": response.status_code,
                "response_time": response_time,
                "error_message": None if response.is_success else response.reason_phrase,
            }
        except httpx.RequestError as e:
            response_time = time.time() - start_time
            logger.warning(f"Request failed for {url}: {e}")
            return {
                "status": "down",
                "status_code": None,
                "response_time": response_time,
                "error_message": str(e),
            }
        except Exception as e:
            logger.error(f"Unexpected error checking site {url}: {e}", exc_info=True)
            return None # Indicate a failure in the check itself

    @staticmethod
    async def check_ping_site(site: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Performs a ping check for a given site (ping://) using native ping3 library."""
        if not PING3_AVAILABLE:
            return {
                "status": "down",
                "status_code": None,
                "response_time": 0,
                "error_message": "ping3 library not available",
            }
        
        url = site['url']
        host = url.replace('ping://', '')
        
        try:
            # Use ping3 for native ICMP ping
            # Run in thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            response_time = await loop.run_in_executor(
                None, 
                lambda: ping3.ping(host, timeout=4, unit='s')
            )
            
            if response_time is not None:
                # Successful ping
                return {
                    "status": "up",
                    "status_code": 0,  # Use 0 for successful ping
                    "response_time": response_time,
                    "error_message": None,
                }
            elif response_time is False:
                # Host unknown/cannot resolve
                return {
                    "status": "down",
                    "status_code": None,
                    "response_time": 0,
                    "error_message": "Host unknown or cannot resolve",
                }
            else:
                # Timeout (response_time is None)
                return {
                    "status": "down",
                    "status_code": None,
                    "response_time": 4.0,  # Timeout duration
                    "error_message": "Ping timeout",
                }
        except Exception as e:
            logger.error(f"Error pinging {host}: {e}")
            return {
                "status": "down",
                "status_code": None,
                "response_time": 0,
                "error_message": str(e),
            }

    def _parse_interval(self, interval_str: Optional[str]) -> int:
        """Parses a time string like '30s', '5m', '1h' into seconds."""
        if not interval_str:
            return settings.MIN_SCAN_INTERVAL_SECONDS

        match = re.match(r'^(\d+)([smh])$', interval_str.lower())
        if not match:
            return settings.MIN_SCAN_INTERVAL_SECONDS

        value, unit = match.groups()
        value = int(value)
        if unit == 'm':
            value *= 60
        elif unit == 'h':
            value *= 3600
        
        return max(settings.MIN_SCAN_INTERVAL_SECONDS, min(value, settings.MAX_SCAN_INTERVAL_SECONDS))

    async def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        sites_status = await get_site_status()
        total_sites = len(sites_status)
        sites_up = sum(1 for s in sites_status if s.get('status') == 'up')
        sites_down = total_sites - sites_up
        
        up_sites_with_time = [s for s in sites_status if s.get('status') == 'up' and s.get('response_time') is not None]
        avg_response_time = None
        if up_sites_with_time:
            avg_response_time = sum(s['response_time'] for s in up_sites_with_time) / len(up_sites_with_time)

        return {
            "total_sites": total_sites,
            "sites_up": sites_up,
            "sites_down": sites_down,
            "average_response_time": avg_response_time,
        }

# --- Singleton Pattern ---
_monitor_instance: Optional[SiteMonitor] = None

def get_monitor() -> SiteMonitor:
    """Returns the singleton instance of the SiteMonitor."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = SiteMonitor()
    return _monitor_instance

# For convenience, but get_monitor() is preferred for clarity.
monitor_instance = get_monitor() 