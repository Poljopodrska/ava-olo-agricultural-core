#!/usr/bin/env python3
"""
Health API routes for AVA OLO Monitoring Dashboards
Handles health checks, performance metrics, and system status
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse, HTMLResponse
import psutil
import time
import os
import traceback
import logging
from datetime import datetime
from typing import Dict, Any

from ..core.config import VERSION, BUILD_ID, get_api_keys
from ..core.database_manager import get_db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/health", tags=["health"])

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    try:
        # Test database connection
        db_manager = get_db_manager()
        db_healthy = db_manager.test_connection()
        
        return JSONResponse({
            "status": "healthy" if db_healthy else "degraded",
            "version": VERSION,
            "build_id": BUILD_ID,
            "timestamp": datetime.now().isoformat(),
            "database": "connected" if db_healthy else "disconnected"
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e),
            "version": VERSION
        }, status_code=503)

@router.get("/database")
async def database_health():
    """Check database performance and connectivity"""
    try:
        db_manager = get_db_manager()
        
        # Test query performance
        start_time = time.time()
        test_result = db_manager.execute_query("SELECT 1 as test", fetch_mode='one')
        query_time = time.time() - start_time
        
        # Test farmer count query (more realistic)
        start_time = time.time()
        farmer_count = db_manager.execute_query("SELECT COUNT(*) as count FROM ava_farmers", fetch_mode='one')
        farmer_query_time = time.time() - start_time
        
        # Determine health status based on performance
        if query_time > 0.5 or farmer_query_time > 1.0:
            status = "degraded"
            status_code = 503
        elif query_time > 0.2 or farmer_query_time > 0.5:
            status = "warning"
            status_code = 200
        else:
            status = "healthy"
            status_code = 200
        
        return JSONResponse({
            "status": status,
            "test_query_time": round(query_time, 4),
            "farmer_query_time": round(farmer_query_time, 4),
            "farmer_count": farmer_count['count'] if farmer_count else 0,
            "thresholds": {
                "warning": {"test": 0.2, "farmer": 0.5},
                "critical": {"test": 0.5, "farmer": 1.0}
            },
            "timestamp": datetime.now().isoformat()
        }, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=503)

@router.get("/performance")
async def performance_metrics():
    """Get system performance metrics"""
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_info = {
            "total_mb": round(memory.total / 1024 / 1024, 2),
            "available_mb": round(memory.available / 1024 / 1024, 2),
            "used_mb": round(memory.used / 1024 / 1024, 2),
            "percent": memory.percent
        }
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_info = {
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
            "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
            "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
            "percent": disk.percent
        }
        
        # Process info
        process = psutil.Process()
        process_info = {
            "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "cpu_percent": process.cpu_percent(interval=0.1),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()) if hasattr(process, 'open_files') else 0
        }
        
        # Database metrics
        db_manager = get_db_manager()
        db_metrics = db_manager.get_dashboard_metrics()
        
        return JSONResponse({
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": memory_info,
                "disk": disk_info
            },
            "process": process_info,
            "database": {
                "connected": db_metrics.get('active_connections', 0) > 0,
                "pool_available": db_metrics.get('pool_available', False),
                "farmer_count": db_metrics.get('farmer_count', 0),
                "total_hectares": db_metrics.get('total_hectares', 0)
            },
            "version": VERSION
        })
    except Exception as e:
        logger.error(f"Performance metrics failed: {e}")
        return JSONResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

# Extended health endpoints
@router.get("/database")
async def health_database():
    """Detailed database health check"""
    try:
        db_manager = get_db_manager()
        start_time = time.time()
        
        # Test connection
        connection_ok = db_manager.test_connection()
        connection_time = time.time() - start_time
        
        if not connection_ok:
            return JSONResponse({
                "status": "unhealthy",
                "connection": False,
                "error": "Database connection failed"
            }, status_code=503)
        
        # Test query performance
        query_start = time.time()
        result = db_manager.execute_query("SELECT COUNT(*) FROM farmers")
        query_time = time.time() - query_start
        
        farmer_count = result['rows'][0][0] if result.get('rows') else 0
        
        # Get table statistics
        stats_query = """
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
            n_live_tup as row_count
        FROM pg_stat_user_tables
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        LIMIT 10
        """
        
        stats_result = db_manager.execute_query(stats_query)
        table_stats = []
        for row in stats_result.get('rows', []):
            table_stats.append({
                "schema": row[0],
                "table": row[1],
                "size": row[2],
                "rows": row[3]
            })
        
        return JSONResponse({
            "status": "healthy",
            "connection": True,
            "connection_time_ms": round(connection_time * 1000, 2),
            "query_time_ms": round(query_time * 1000, 2),
            "farmer_count": farmer_count,
            "table_stats": table_stats,
            "pool_info": {
                "available": db_manager.pool_initialized,
                "type": "pooled" if db_manager.pool_initialized else "direct"
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=503)

@router.get("/services")
async def health_services():
    """Check health of external services"""
    try:
        api_keys = get_api_keys()
        
        services = {
            "google_maps": {
                "configured": bool(api_keys.get('google_maps')),
                "key_length": len(api_keys.get('google_maps', '')) if api_keys.get('google_maps') else 0
            },
            "openai": {
                "configured": bool(api_keys.get('openai')),
                "key_length": len(api_keys.get('openai', '')) if api_keys.get('openai') else 0
            }
        }
        
        # Check environment
        environment = {
            "aws_execution": bool(os.getenv('AWS_EXECUTION_ENV')),
            "environment": os.getenv('ENVIRONMENT', 'not_set'),
            "service_version": os.getenv('SERVICE_VERSION', VERSION)
        }
        
        return JSONResponse({
            "services": services,
            "environment": environment,
            "all_configured": all(s['configured'] for s in services.values()),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

# System status endpoints
@router.get("/system-status")
async def system_status():
    """Comprehensive system status"""
    try:
        # Collect all health data
        basic_health = await health_check()
        performance = await performance_metrics()
        database_health = await health_database()
        services_health = await health_services()
        
        # Parse responses
        basic = basic_health.body.decode() if hasattr(basic_health, 'body') else str(basic_health)
        perf = performance.body.decode() if hasattr(performance, 'body') else str(performance)
        db = database_health.body.decode() if hasattr(database_health, 'body') else str(database_health)
        services = services_health.body.decode() if hasattr(services_health, 'body') else str(services_health)
        
        import json
        
        status = {
            "overall_status": "healthy",
            "version": VERSION,
            "build_id": BUILD_ID,
            "components": {
                "api": json.loads(basic)['status'] == 'healthy',
                "database": json.loads(db).get('status') == 'healthy',
                "performance": "error" not in perf,
                "services": json.loads(services).get('all_configured', False)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Determine overall status
        if not all(status["components"].values()):
            if status["components"]["api"] and status["components"]["database"]:
                status["overall_status"] = "degraded"
            else:
                status["overall_status"] = "unhealthy"
        
        return JSONResponse(status)
    except Exception as e:
        return JSONResponse({
            "overall_status": "error",
            "error": str(e),
            "version": VERSION
        }, status_code=500)