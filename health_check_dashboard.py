"""
AVA OLO Health Check Dashboard - Port 8008
System health monitoring and service status dashboard
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import logging
import os
import sys
import httpx
import asyncio
from typing import Dict, Any, List
from datetime import datetime
# import psutil - removed for compatibility

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_operations import DatabaseOperations

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Health Check Dashboard",
    description="System health monitoring and service status",
    version="1.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize database
db_ops = DatabaseOperations()

# Service definitions
SERVICES = {
    "API Gateway": {"url": "http://localhost:8000/health", "port": 8000},
    "Mock WhatsApp": {"url": "http://localhost:8006/health", "port": 8006},
    "Agronomic Dashboard": {"url": "http://localhost:8007/health", "port": 8007},
    "Business Dashboard": {"url": "http://localhost:8004/health", "port": 8004},
    "Database Explorer": {"url": "http://localhost:8005/health", "port": 8005},
}

class HealthMonitor:
    """Health monitoring for all AVA OLO services"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
    
    async def check_service_health(self, service_name: str, service_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of a single service"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(service_info["url"])
                if response.status_code == 200:
                    return {
                        "name": service_name,
                        "status": "healthy",
                        "port": service_info["port"],
                        "response_time": response.elapsed.total_seconds(),
                        "details": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
                    }
                else:
                    return {
                        "name": service_name,
                        "status": "unhealthy",
                        "port": service_info["port"],
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            return {
                "name": service_name,
                "status": "offline",
                "port": service_info["port"],
                "error": str(e)
            }
    
    async def get_all_services_health(self) -> List[Dict[str, Any]]:
        """Check health of all services"""
        tasks = [
            self.check_service_health(name, info) 
            for name, info in SERVICES.items()
        ]
        return await asyncio.gather(*tasks)
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        try:
            # Basic system metrics without psutil
            import os
            
            # Get load average (Unix/Linux only)
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
            
            # Get memory info from /proc/meminfo if available
            memory_info = {}
            try:
                with open('/proc/meminfo', 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('MemTotal:'):
                            memory_info['total'] = int(line.split()[1]) / 1024 / 1024  # Convert to GB
                        elif line.startswith('MemAvailable:'):
                            memory_info['available'] = int(line.split()[1]) / 1024 / 1024
                    
                    if 'total' in memory_info and 'available' in memory_info:
                        memory_info['used'] = memory_info['total'] - memory_info['available']
                        memory_info['percent'] = round((memory_info['used'] / memory_info['total']) * 100, 1)
            except:
                pass
            
            return {
                "cpu": {
                    "load_1min": round(load_avg[0], 2),
                    "load_5min": round(load_avg[1], 2),
                    "load_15min": round(load_avg[2], 2)
                },
                "memory": {
                    "percent": memory_info.get('percent', 0),
                    "used_gb": round(memory_info.get('used', 0), 2),
                    "total_gb": round(memory_info.get('total', 0), 2)
                },
                "disk": {
                    "percent": 0,
                    "used_gb": 0,
                    "total_gb": 0
                }
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    async def get_database_health(self) -> Dict[str, Any]:
        """Check database health and statistics"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                
                # Check connection
                session.execute(text("SELECT 1"))
                
                # Get table counts
                farmers_count = session.execute(
                    text("SELECT COUNT(*) FROM farmers")
                ).scalar() or 0
                
                messages_count = session.execute(
                    text("SELECT COUNT(*) FROM incoming_messages")
                ).scalar() or 0
                
                fields_count = session.execute(
                    text("SELECT COUNT(*) FROM fields")
                ).scalar() or 0
                
                return {
                    "status": "healthy",
                    "database": "farmer_crm",
                    "statistics": {
                        "farmers": farmers_count,
                        "messages": messages_count,
                        "fields": fields_count
                    }
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Initialize monitor
monitor = HealthMonitor()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main health check dashboard"""
    services_health = await monitor.get_all_services_health()
    system_metrics = await monitor.get_system_metrics()
    database_health = await monitor.get_database_health()
    
    # Calculate overall health
    healthy_services = sum(1 for s in services_health if s["status"] == "healthy")
    total_services = len(services_health)
    
    return templates.TemplateResponse(
        "health_dashboard.html",
        {
            "request": request,
            "services": services_health,
            "system_metrics": system_metrics,
            "database_health": database_health,
            "healthy_services": healthy_services,
            "total_services": total_services,
            "overall_health": "healthy" if healthy_services == total_services else "degraded",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )

@app.get("/api/health")
async def api_health():
    """API endpoint for health data"""
    services_health = await monitor.get_all_services_health()
    system_metrics = await monitor.get_system_metrics()
    database_health = await monitor.get_database_health()
    
    return {
        "services": services_health,
        "system": system_metrics,
        "database": database_health,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "service": "Health Check Dashboard",
        "status": "healthy",
        "port": 8008,
        "purpose": "System health monitoring"
    }

if __name__ == "__main__":
    import uvicorn
    print("🏥 Starting AVA OLO Health Check Dashboard on port 8008")
    uvicorn.run(app, host="0.0.0.0", port=8008)