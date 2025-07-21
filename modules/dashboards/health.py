"""
AVA OLO Health Dashboard Module
Implements comprehensive system health monitoring
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import httpx
import asyncio
import psutil
import time
from datetime import datetime
import logging
from modules.core.database_manager import get_db_manager
from modules.core.config import config
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards/health", tags=["health_dashboard"])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
async def health_dashboard(request: Request):
    """Main health dashboard"""
    return templates.TemplateResponse("health_dashboard_constitutional.html", {
        "request": request
    })

@router.get("/api/all-checks", response_class=JSONResponse)
async def get_all_health_checks():
    """Run all health checks and return comprehensive status"""
    
    health_checks = []
    
    # 1. PostgreSQL Database Check
    postgres_check = await check_postgresql()
    health_checks.append(postgres_check)
    
    # 2. Pinecone Vector Database Check
    pinecone_check = await check_pinecone()
    health_checks.append(pinecone_check)
    
    # 3. Perplexity API Check
    perplexity_check = await check_perplexity()
    health_checks.append(perplexity_check)
    
    # 4. OpenAI API Check
    openai_check = await check_openai()
    health_checks.append(openai_check)
    
    # 5. WhatsApp API Check
    whatsapp_check = await check_whatsapp()
    health_checks.append(whatsapp_check)
    
    # 6. Redis Cache Check
    redis_check = await check_redis()
    health_checks.append(redis_check)
    
    # 7. AWS Services Check
    aws_check = await check_aws_services()
    health_checks.append(aws_check)
    
    # 8. Weather API Check
    weather_check = await check_weather_api()
    health_checks.append(weather_check)
    
    # 9. Agricultural Core Service Check
    agri_core_check = await check_agricultural_core()
    health_checks.append(agri_core_check)
    
    # 10. CAVA Service Check
    cava_check = await check_cava_service()
    health_checks.append(cava_check)
    
    # Calculate overall health
    total_checks = len(health_checks)
    healthy_checks = sum(1 for check in health_checks if check['status'] == 'healthy')
    overall_health = 'healthy' if healthy_checks == total_checks else 'degraded' if healthy_checks > total_checks / 2 else 'unhealthy'
    
    return {
        "success": True,
        "overall_health": overall_health,
        "healthy_services": healthy_checks,
        "total_services": total_checks,
        "checks": health_checks,
        "timestamp": datetime.now().isoformat()
    }

async def check_postgresql():
    """Check PostgreSQL database connection"""
    start_time = time.time()
    db_manager = get_db_manager()
    
    try:
        # Test connection with a simple query
        result = await db_manager.execute_query("SELECT 1")
        response_time = int((time.time() - start_time) * 1000)
        
        if result and result.get('success'):
            return {
                "service": "PostgreSQL Database",
                "status": "healthy",
                "response_time": response_time,
                "details": "Connection successful",
                "last_checked": datetime.now().isoformat()
            }
        else:
            return {
                "service": "PostgreSQL Database",
                "status": "unhealthy",
                "response_time": response_time,
                "details": "Query failed",
                "error": result.get('error', 'Unknown error'),
                "last_checked": datetime.now().isoformat()
            }
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        return {
            "service": "PostgreSQL Database",
            "status": "unhealthy",
            "response_time": response_time,
            "details": "Connection failed",
            "error": str(e),
            "last_checked": datetime.now().isoformat()
        }

async def check_pinecone():
    """Check Pinecone vector database"""
    start_time = time.time()
    
    try:
        # Check if Pinecone is configured
        pinecone_api_key = os.getenv('PINECONE_API_KEY')
        
        if not pinecone_api_key:
            return {
                "service": "Pinecone Vector Database",
                "status": "unconfigured",
                "response_time": 0,
                "details": "Pinecone API key not configured",
                "last_checked": datetime.now().isoformat()
            }
        
        # Try to connect to Pinecone (simplified check)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.pinecone.io/databases",
                headers={"Api-Key": pinecone_api_key},
                timeout=5.0
            )
            
        response_time = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            return {
                "service": "Pinecone Vector Database",
                "status": "healthy",
                "response_time": response_time,
                "details": "API accessible",
                "last_checked": datetime.now().isoformat()
            }
        else:
            return {
                "service": "Pinecone Vector Database",
                "status": "unhealthy",
                "response_time": response_time,
                "details": f"API returned status {response.status_code}",
                "last_checked": datetime.now().isoformat()
            }
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        return {
            "service": "Pinecone Vector Database",
            "status": "unhealthy",
            "response_time": response_time,
            "details": "Connection failed",
            "error": str(e),
            "last_checked": datetime.now().isoformat()
        }

async def check_perplexity():
    """Check Perplexity API"""
    start_time = time.time()
    
    try:
        perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
        
        if not perplexity_api_key:
            return {
                "service": "Perplexity API",
                "status": "unconfigured",
                "response_time": 0,
                "details": "Perplexity API key not configured",
                "last_checked": datetime.now().isoformat()
            }
        
        # Test API with a simple request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {perplexity_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                },
                timeout=10.0
            )
        
        response_time = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            return {
                "service": "Perplexity API",
                "status": "healthy",
                "response_time": response_time,
                "details": "API accessible",
                "last_checked": datetime.now().isoformat()
            }
        else:
            return {
                "service": "Perplexity API",
                "status": "unhealthy",
                "response_time": response_time,
                "details": f"API returned status {response.status_code}",
                "last_checked": datetime.now().isoformat()
            }
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        return {
            "service": "Perplexity API",
            "status": "unhealthy",
            "response_time": response_time,
            "details": "Connection failed",
            "error": str(e),
            "last_checked": datetime.now().isoformat()
        }

async def check_openai():
    """Check OpenAI API"""
    start_time = time.time()
    
    try:
        openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not openai_api_key:
            return {
                "service": "OpenAI API",
                "status": "unconfigured",
                "response_time": 0,
                "details": "OpenAI API key not configured",
                "last_checked": datetime.now().isoformat()
            }
        
        # Test API with a simple request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                },
                timeout=10.0
            )
        
        response_time = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            return {
                "service": "OpenAI API",
                "status": "healthy",
                "response_time": response_time,
                "details": "API accessible",
                "last_checked": datetime.now().isoformat()
            }
        else:
            return {
                "service": "OpenAI API",
                "status": "unhealthy",
                "response_time": response_time,
                "details": f"API returned status {response.status_code}",
                "last_checked": datetime.now().isoformat()
            }
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        return {
            "service": "OpenAI API",
            "status": "unhealthy",
            "response_time": response_time,
            "details": "Connection failed",
            "error": str(e),
            "last_checked": datetime.now().isoformat()
        }

async def check_whatsapp():
    """Check WhatsApp API"""
    start_time = time.time()
    
    try:
        # Check if WhatsApp is configured
        whatsapp_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        
        if not whatsapp_token:
            return {
                "service": "WhatsApp API",
                "status": "unconfigured",
                "response_time": 0,
                "details": "WhatsApp access token not configured",
                "last_checked": datetime.now().isoformat()
            }
        
        # Test WhatsApp Business API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.facebook.com/v17.0/me",
                params={"access_token": whatsapp_token},
                timeout=5.0
            )
        
        response_time = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            return {
                "service": "WhatsApp API",
                "status": "healthy",
                "response_time": response_time,
                "details": "API accessible",
                "last_checked": datetime.now().isoformat()
            }
        else:
            return {
                "service": "WhatsApp API",
                "status": "unhealthy",
                "response_time": response_time,
                "details": f"API returned status {response.status_code}",
                "last_checked": datetime.now().isoformat()
            }
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        return {
            "service": "WhatsApp API",
            "status": "unhealthy",
            "response_time": response_time,
            "details": "Connection failed",
            "error": str(e),
            "last_checked": datetime.now().isoformat()
        }

async def check_redis():
    """Check Redis cache"""
    start_time = time.time()
    
    try:
        # Try to connect to Redis
        import redis.asyncio as redis
        
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        client = redis.from_url(redis_url)
        
        # Test connection with ping
        await client.ping()
        await client.close()
        
        response_time = int((time.time() - start_time) * 1000)
        
        return {
            "service": "Redis Cache",
            "status": "healthy",
            "response_time": response_time,
            "details": "Connection successful",
            "last_checked": datetime.now().isoformat()
        }
    except ImportError:
        return {
            "service": "Redis Cache",
            "status": "unconfigured",
            "response_time": 0,
            "details": "Redis library not installed",
            "last_checked": datetime.now().isoformat()
        }
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        return {
            "service": "Redis Cache",
            "status": "unhealthy",
            "response_time": response_time,
            "details": "Connection failed",
            "error": str(e),
            "last_checked": datetime.now().isoformat()
        }

async def check_aws_services():
    """Check AWS services (ECS, RDS, etc.)"""
    start_time = time.time()
    
    try:
        # Check if running on AWS ECS
        ecs_metadata_uri = os.getenv('ECS_CONTAINER_METADATA_URI_V4')
        
        if ecs_metadata_uri:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{ecs_metadata_uri}/task", timeout=2.0)
                
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                return {
                    "service": "AWS Services (ECS)",
                    "status": "healthy",
                    "response_time": response_time,
                    "details": "Running on ECS",
                    "last_checked": datetime.now().isoformat()
                }
        
        # Check RDS connection (via PostgreSQL check)
        db_host = os.getenv('DB_HOST', '')
        if 'rds.amazonaws.com' in db_host:
            return {
                "service": "AWS Services (RDS)",
                "status": "healthy",
                "response_time": 0,
                "details": "Using AWS RDS",
                "last_checked": datetime.now().isoformat()
            }
        
        return {
            "service": "AWS Services",
            "status": "unconfigured",
            "response_time": 0,
            "details": "Not running on AWS",
            "last_checked": datetime.now().isoformat()
        }
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        return {
            "service": "AWS Services",
            "status": "unknown",
            "response_time": response_time,
            "details": "Could not determine AWS status",
            "error": str(e),
            "last_checked": datetime.now().isoformat()
        }

async def check_weather_api():
    """Check Weather API"""
    start_time = time.time()
    
    try:
        weather_api_key = os.getenv('WEATHER_API_KEY')
        
        if not weather_api_key:
            return {
                "service": "Weather API",
                "status": "unconfigured",
                "response_time": 0,
                "details": "Weather API key not configured",
                "last_checked": datetime.now().isoformat()
            }
        
        # Test OpenWeatherMap API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": "London",
                    "appid": weather_api_key
                },
                timeout=5.0
            )
        
        response_time = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            return {
                "service": "Weather API",
                "status": "healthy",
                "response_time": response_time,
                "details": "API accessible",
                "last_checked": datetime.now().isoformat()
            }
        else:
            return {
                "service": "Weather API",
                "status": "unhealthy",
                "response_time": response_time,
                "details": f"API returned status {response.status_code}",
                "last_checked": datetime.now().isoformat()
            }
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        return {
            "service": "Weather API",
            "status": "unhealthy",
            "response_time": response_time,
            "details": "Connection failed",
            "error": str(e),
            "last_checked": datetime.now().isoformat()
        }

async def check_agricultural_core():
    """Check Agricultural Core Service"""
    start_time = time.time()
    
    try:
        # Check if agricultural core is running
        agri_core_url = os.getenv('AGRICULTURAL_CORE_URL', 'http://localhost:8001')
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{agri_core_url}/health", timeout=5.0)
        
        response_time = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            return {
                "service": "Agricultural Core Service",
                "status": "healthy",
                "response_time": response_time,
                "details": "Service accessible",
                "last_checked": datetime.now().isoformat()
            }
        else:
            return {
                "service": "Agricultural Core Service",
                "status": "unhealthy",
                "response_time": response_time,
                "details": f"Service returned status {response.status_code}",
                "last_checked": datetime.now().isoformat()
            }
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        return {
            "service": "Agricultural Core Service",
            "status": "unhealthy",
            "response_time": response_time,
            "details": "Connection failed",
            "error": str(e),
            "last_checked": datetime.now().isoformat()
        }

async def check_cava_service():
    """Check CAVA Service"""
    start_time = time.time()
    
    try:
        # Check if CAVA is configured
        cava_enabled = os.getenv('CAVA_ENABLED', 'false').lower() == 'true'
        
        if not cava_enabled:
            return {
                "service": "CAVA Service",
                "status": "disabled",
                "response_time": 0,
                "details": "CAVA service is disabled",
                "last_checked": datetime.now().isoformat()
            }
        
        # Try to check CAVA health endpoint
        cava_url = os.getenv('CAVA_SERVICE_URL', 'http://localhost:8002')
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{cava_url}/health", timeout=5.0)
        
        response_time = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            return {
                "service": "CAVA Service",
                "status": "healthy",
                "response_time": response_time,
                "details": "Service accessible",
                "last_checked": datetime.now().isoformat()
            }
        else:
            return {
                "service": "CAVA Service",
                "status": "unhealthy",
                "response_time": response_time,
                "details": f"Service returned status {response.status_code}",
                "last_checked": datetime.now().isoformat()
            }
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        return {
            "service": "CAVA Service",
            "status": "unhealthy",
            "response_time": response_time,
            "details": "Connection failed",
            "error": str(e),
            "last_checked": datetime.now().isoformat()
        }

@router.get("/api/system-metrics", response_class=JSONResponse)
async def get_system_metrics():
    """Get system resource metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Network stats
        network = psutil.net_io_counters()
        
        return {
            "success": True,
            "metrics": {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "cores": psutil.cpu_count()
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "usage_percent": disk.percent
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_received": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_received": network.packets_recv
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "metrics": {}
        }