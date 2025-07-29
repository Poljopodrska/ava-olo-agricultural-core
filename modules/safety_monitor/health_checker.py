#!/usr/bin/env python3
"""
Automated Health Checker - Runs independently
Writes to file only, no database modifications
"""
import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthChecker:
    """
    Automated health checking system
    Completely isolated from main application
    """
    
    def __init__(self):
        self.health_log_path = Path('/tmp/ava_health_log.json')
        self.summary_dir = Path('/tmp')
        self.check_interval = 300  # 5 minutes
        self.health_endpoint = os.getenv(
            'HEALTH_ENDPOINT', 
            'http://localhost:8080/api/v1/safety/health'
        )
    
    async def check_health(self) -> dict:
        """Check system health and log results"""
        health_result = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'unknown',
            'response_time_ms': None,
            'data': None,
            'error': None
        }
        
        start_time = datetime.now(timezone.utc)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.health_endpoint,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                    health_result['response_time_ms'] = round(response_time, 2)
                    
                    if response.status == 200:
                        data = await response.json()
                        health_result['status'] = data.get('overall_status', 'unknown')
                        health_result['data'] = data
                    else:
                        health_result['status'] = 'unhealthy'
                        health_result['error'] = f'HTTP {response.status}'
                        
        except asyncio.TimeoutError:
            health_result['status'] = 'timeout'
            health_result['error'] = 'Request timed out after 30 seconds'
        except Exception as e:
            health_result['status'] = 'unreachable'
            health_result['error'] = str(e)
        
        # Log to file
        self._log_health_result(health_result)
        
        return health_result
    
    def _log_health_result(self, result: dict):
        """Append health check result to log file"""
        try:
            # Create log entry
            log_entry = {
                'timestamp': result['timestamp'],
                'status': result['status'],
                'response_time_ms': result['response_time_ms'],
                'error': result.get('error')
            }
            
            # If healthy, include key metrics
            if result['status'] == 'HEALTHY' and result.get('data'):
                metrics = result['data'].get('metrics', {})
                log_entry['metrics'] = {
                    'total_farmers': metrics.get('total_farmers'),
                    'registrations_today': metrics.get('registrations_today')
                }
            
            # Append to log file
            with open(self.health_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to write health log: {e}")
    
    async def run_continuous_monitoring(self):
        """Run health checks continuously"""
        logger.info(f"Starting health monitoring, checking every {self.check_interval} seconds")
        
        while True:
            try:
                result = await self.check_health()
                logger.info(f"Health check completed: {result['status']}")
                
                # Generate daily summary if needed
                self._check_daily_summary()
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
            
            # Wait for next check
            await asyncio.sleep(self.check_interval)
    
    def _check_daily_summary(self):
        """Generate daily summary if not already created"""
        today = datetime.now(timezone.utc).date().isoformat()
        summary_path = self.summary_dir / f'health_summary_{today}.json'
        
        # Only create if doesn't exist
        if not summary_path.exists():
            self.generate_daily_summary()
    
    def generate_daily_summary(self):
        """Generate daily health summary"""
        today = datetime.now(timezone.utc).date().isoformat()
        summary_path = self.summary_dir / f'health_summary_{today}.json'
        
        try:
            # Read today's logs
            health_checks = []
            if self.health_log_path.exists():
                with open(self.health_log_path, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            # Only include today's entries
                            if entry['timestamp'].startswith(today):
                                health_checks.append(entry)
                        except:
                            pass
            
            # Calculate statistics
            total_checks = len(health_checks)
            healthy_checks = sum(1 for h in health_checks if h['status'] == 'HEALTHY')
            uptime_percentage = (healthy_checks / total_checks * 100) if total_checks > 0 else 0
            
            # Get latest metrics
            latest_metrics = {}
            for check in reversed(health_checks):
                if check.get('metrics'):
                    latest_metrics = check['metrics']
                    break
            
            # Count incidents
            incidents = [h for h in health_checks if h['status'] not in ['HEALTHY', 'DEGRADED']]
            
            # Create summary
            summary = {
                'date': today,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_checks': total_checks,
                'healthy_checks': healthy_checks,
                'uptime_percentage': round(uptime_percentage, 2),
                'incidents_count': len(incidents),
                'latest_metrics': latest_metrics,
                'overall_status': 'HEALTHY' if uptime_percentage >= 95 else 'DEGRADED' if uptime_percentage >= 80 else 'UNHEALTHY'
            }
            
            # Write summary
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Daily summary generated: {summary_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate daily summary: {e}")


async def main():
    """Main entry point"""
    checker = HealthChecker()
    
    # Run single check if requested
    if '--once' in os.sys.argv:
        result = await checker.check_health()
        print(json.dumps(result, indent=2))
    else:
        # Run continuous monitoring
        await checker.run_continuous_monitoring()


if __name__ == "__main__":
    asyncio.run(main())