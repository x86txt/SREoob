import asyncio
import aiohttp
import time
import logging
from typing import List, Dict, Any
from .database import get_sites, record_check

logger = logging.getLogger(__name__)

class SiteMonitor:
    def __init__(self):
        self.session = None
        self.monitoring = False
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_site(self, site: Dict[str, Any]) -> Dict[str, Any]:
        """Check a single site and return the result."""
        start_time = time.time()
        result = {
            'site_id': site['id'],
            'url': site['url'],
            'name': site['name'],
            'status': 'down',
            'response_time': None,
            'status_code': None,
            'error_message': None
        }
        
        try:
            async with self.session.get(site['url']) as response:
                response_time = time.time() - start_time
                result.update({
                    'status': 'up' if response.status < 400 else 'down',
                    'response_time': response_time,
                    'status_code': response.status,
                    'error_message': None if response.status < 400 else f"HTTP {response.status}"
                })
                
        except asyncio.TimeoutError:
            result.update({
                'response_time': time.time() - start_time,
                'error_message': 'Timeout'
            })
        except aiohttp.ClientError as e:
            result.update({
                'response_time': time.time() - start_time,
                'error_message': str(e)
            })
        except Exception as e:
            result.update({
                'response_time': time.time() - start_time,
                'error_message': f"Unexpected error: {str(e)}"
            })
            
        return result

    async def check_all_sites(self) -> List[Dict[str, Any]]:
        """Check all sites concurrently."""
        sites = await get_sites()
        if not sites:
            return []
            
        # Check all sites concurrently
        tasks = [self.check_site(site) for site in sites]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and record in database
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error checking site: {result}")
                continue
                
            valid_results.append(result)
            
            # Record the check result in database
            await record_check(
                site_id=result['site_id'],
                status=result['status'],
                response_time=result['response_time'],
                status_code=result['status_code'],
                error_message=result['error_message']
            )
            
        return valid_results

    async def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring of all sites."""
        self.monitoring = True
        logger.info(f"Starting site monitoring with {interval}s interval")
        
        while self.monitoring:
            try:
                results = await self.check_all_sites()
                logger.info(f"Checked {len(results)} sites")
                
                # Log summary
                up_count = sum(1 for r in results if r['status'] == 'up')
                down_count = len(results) - up_count
                logger.info(f"Sites: {up_count} up, {down_count} down")
                
            except Exception as e:
                logger.error(f"Error during monitoring cycle: {e}")
                
            # Wait for next cycle
            await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Stop the monitoring loop."""
        self.monitoring = False
        logger.info("Site monitoring stopped")

# Global monitor instance
monitor = SiteMonitor()

async def get_monitor():
    """Get the global monitor instance."""
    return monitor 