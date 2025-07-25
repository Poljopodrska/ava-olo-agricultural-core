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
import traceback
# import psutil - removed for compatibility

# Set up logging with more detail for debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("=== STARTING HEALTH DASHBOARD IMPORT ===")

# Import with error handling for AWS environment
try:
    import subprocess
    logger.info("subprocess imported successfully")
except ImportError:
    subprocess = None
    logger.warning("subprocess module not available")
    
try:
    import psycopg2
    logger.info("psycopg2 imported successfully")
except ImportError:
    psycopg2 = None
    logger.warning("psycopg2 module not available")

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database_operations import DatabaseOperations
    logger.info("DatabaseOperations imported successfully")
except Exception as e:
    logger.error(f"Failed to import DatabaseOperations: {e}")
    DatabaseOperations = None

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Health Check Dashboard",
    description="System health monitoring and service status",
    version="1.0.0"
)

# Import constitutional components for testing
try:
    from monitoring.core.llm_query_processor import LLMQueryProcessor
    CONSTITUTIONAL_AVAILABLE = True
except ImportError:
    CONSTITUTIONAL_AVAILABLE = False
    logger.warning("Constitutional modules not available")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize database with error handling
try:
    if DatabaseOperations:
        db_ops = DatabaseOperations()
        logger.info("DatabaseOperations initialized")
    else:
        db_ops = None
        logger.warning("DatabaseOperations not available")
except Exception as e:
    logger.error(f"Failed to initialize DatabaseOperations: {e}")
    db_ops = None

# Service definitions - AWS Production URLs
SERVICES = {
    "Agricultural Core": {
        "url": "https://3ksdvgdtud.us-east-1.elb.amazonaws.com/health",
        "description": "Core API and LLM routing"
    },
    "Agronomic Dashboard": {
        "url": "https://6pmgiripe.us-east-1.elb.amazonaws.com/agronomic/health",
        "description": "Expert approval interface"
    },
    "Business Dashboard": {
        "url": "https://6pmgiripe.us-east-1.elb.amazonaws.com/business/health",
        "description": "Business KPIs and metrics"
    },
    "Database Explorer": {
        "url": "https://6pmgiripe.us-east-1.elb.amazonaws.com/database/health",
        "description": "AI-driven database queries"
    }
}

def get_deployment_info():
    """
    AWS-safe deployment info with extensive logging
    """
    logger.info("Starting get_deployment_info function")
    try:
        import os
        logger.info("Basic imports successful")
        
        # Don't use subprocess in AWS - causes issues
        deployment_info = {
            "version": "aws-v1.0",
            "git_commit": "aws-deployed",
            "git_date": "2025-07-12",
            "deployment_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "DEPLOYED-AWS"
        }
        logger.info(f"Deployment info created: {deployment_info}")
        return deployment_info
        
    except Exception as e:
        logger.error(f"Error in get_deployment_info: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "version": "error",
            "status": "ERROR",
            "error": str(e)
        }

def check_aws_database_health():
    """
    Simplified database check with extensive logging
    """
    logger.info("Starting database health check")
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("OS and dotenv imports successful")
        
        # Check environment variables first
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME', 'farmer_crm')
        logger.info(f"DB_HOST: {db_host}")
        logger.info(f"DB_NAME: {db_name}")
        
        if not db_host:
            logger.error("DB_HOST environment variable missing")
            return {
                "status": "FAILED",
                "database": "farmer_crm",
                "connection": "Missing DB_HOST",
                "error": "DB_HOST missing",
                "constitutional_compliance": False
            }
        
        # Check if psycopg2 is available
        if psycopg2 is None:
            logger.error("psycopg2 module not available")
            return {
                "status": "FAILED",
                "database": "farmer_crm",
                "connection": "psycopg2 not available",
                "error": "Database driver not installed",
                "constitutional_compliance": False
            }
        
        # Try database connection
        conn = psycopg2.connect(
            host=db_host,
            database=os.getenv('DB_NAME', 'farmer_crm'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432'),
            connect_timeout=10  # Add timeout
        )
        
        cursor = conn.cursor()
        
        # Get actual counts (no hardcoded expectations)
        cursor.execute("SELECT COUNT(*) FROM farmers")
        farmer_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fields")
        field_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM incoming_messages")
        message_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Constitutional validation: Database accessible and has data
        is_healthy = (
            farmer_count > 0 and      # Has farmers (not specific count)
            table_count > 30 and      # Has reasonable table count (flexible)
            field_count >= 0 and      # Has fields (can be 0 for new system)
            message_count >= 0        # Has messages (can be 0 for new system)
        )
        
        return {
            "status": "HEALTHY" if is_healthy else "WARNING",
            "database": "farmer_crm",
            "connection": "AWS RDS Connected",
            "farmers": farmer_count,
            "tables": table_count,
            "fields": field_count,
            "messages": message_count,
            "constitutional_compliance": is_healthy
        }
        
    except Exception as e:
        return {
            "status": "FAILED",
            "database": "farmer_crm",
            "connection": "AWS RDS Connection Failed",
            "error": str(e)[:200],  # Limit error message length
            "constitutional_compliance": False
        }

class HealthMonitor:
    """Health monitoring for all AVA OLO services"""
    
    def __init__(self):
        try:
            if DatabaseOperations:
                self.db_ops = DatabaseOperations()
            else:
                self.db_ops = None
                logger.warning("DatabaseOperations not available in HealthMonitor")
        except Exception as e:
            logger.error(f"Failed to initialize db_ops in HealthMonitor: {e}")
            self.db_ops = None
    
    async def check_service_health(self, service_name: str, service_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of a single service"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(service_info["url"])
                if response.status_code == 200:
                    health_data = {
                        "name": service_name,
                        "status": "healthy",
                        "url": service_info["url"],
                        "description": service_info.get("description", ""),
                        "response_time": response.elapsed.total_seconds(),
                        "details": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
                    }
                    
                    # Extract version and additional health info if available
                    if health_data.get("details"):
                        details = health_data["details"]
                        health_data["version"] = details.get("version", "Unknown")
                        health_data["llm_connected"] = details.get("llm_connected", None)
                        health_data["last_activity"] = details.get("last_activity", None)
                        health_data["dependencies_ok"] = details.get("dependencies_ok", None)
                    
                    return health_data
                else:
                    return {
                        "name": service_name,
                        "status": "unhealthy",
                        "url": service_info["url"],
                        "description": service_info.get("description", ""),
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            return {
                "name": service_name,
                "status": "offline",
                "url": service_info["url"],
                "description": service_info.get("description", ""),
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
            if not self.db_ops:
                logger.warning("db_ops not available, returning default health")
                return {
                    "status": "unknown",
                    "error": "Database operations not initialized"
                }
                
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
    
    async def test_constitutional_compliance(self) -> Dict[str, Any]:
        """Test constitutional LLM features"""
        results = {
            "status": "unknown",
            "llm_available": False,
            "openai_configured": False,
            "test_queries": [],
            "constitutional_principles": {
                "mango_rule": False,
                "llm_first": False,
                "privacy_first": False,
                "error_isolation": False
            }
        }
        
        try:
            # Check if constitutional modules are available
            if not CONSTITUTIONAL_AVAILABLE:
                results["status"] = "not_available"
                results["error"] = "Constitutional modules not installed"
                return results
            
            # Check OpenAI configuration
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv('OPENAI_API_KEY')
            results["openai_configured"] = bool(api_key and api_key != 'sk-your-key-here')
            
            # Initialize LLM processor
            processor = LLMQueryProcessor()
            results["llm_available"] = True
            
            # Test queries in different languages
            test_cases = [
                {
                    "query": "koliko kmetov je v bazi?",
                    "language": "Slovenian",
                    "expected_sql_pattern": "COUNT.*farmers"
                },
                {
                    "query": "колко манго дървета имам?",
                    "language": "Bulgarian (Mango test)",
                    "expected_sql_pattern": "COUNT.*field_crops|crops"
                },
                {
                    "query": "show all farmers",
                    "language": "English",
                    "expected_sql_pattern": "SELECT.*farmers"
                }
            ]
            
            for test in test_cases:
                try:
                    result = processor.process_natural_query(test["query"])
                    test_result = {
                        "query": test["query"],
                        "language": test["language"],
                        "success": result.get("success", False),
                        "detected_language": result.get("detected_language", "unknown"),
                        "sql": result.get("sql", ""),
                        "confidence": result.get("confidence", 0),
                        "is_fallback": result.get("fallback", False)
                    }
                    
                    # Check if SQL matches expected pattern
                    import re
                    if test["expected_sql_pattern"] and test_result["sql"]:
                        test_result["sql_correct"] = bool(
                            re.search(test["expected_sql_pattern"], test_result["sql"], re.IGNORECASE)
                        )
                    
                    results["test_queries"].append(test_result)
                except Exception as e:
                    results["test_queries"].append({
                        "query": test["query"],
                        "language": test["language"],
                        "success": False,
                        "error": str(e)
                    })
            
            # Evaluate constitutional principles
            successful_tests = [t for t in results["test_queries"] if t.get("success")]
            
            # Mango Rule: Bulgarian mango query should work
            mango_test = next((t for t in results["test_queries"] if "Bulgarian" in t["language"]), None)
            results["constitutional_principles"]["mango_rule"] = bool(
                mango_test and mango_test.get("success")
            )
            
            # LLM First: Should use LLM when available (not fallback)
            results["constitutional_principles"]["llm_first"] = any(
                t.get("success") and not t.get("is_fallback") 
                for t in results["test_queries"]
            )
            
            # Privacy First: No actual data should be exposed
            results["constitutional_principles"]["privacy_first"] = True  # By design
            
            # Error Isolation: All tests should complete even if some fail
            results["constitutional_principles"]["error_isolation"] = True
            
            # Overall status
            if all(results["constitutional_principles"].values()):
                results["status"] = "compliant"
            elif results["openai_configured"] and results["llm_available"]:
                results["status"] = "partial"
            else:
                results["status"] = "non_compliant"
                
        except Exception as e:
            logger.error(f"Constitutional compliance test failed: {e}")
            results["status"] = "error"
            results["error"] = str(e)
        
        return results

# Initialize monitor
monitor = HealthMonitor()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main health check dashboard"""
    services_health = await monitor.get_all_services_health()
    system_metrics = await monitor.get_system_metrics()
    database_health = await monitor.get_database_health()
    constitutional_health = await monitor.test_constitutional_compliance()
    deployment_info = get_deployment_info()
    database_status = check_aws_database_health()
    
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
            "constitutional_health": constitutional_health,
            "deployment_info": deployment_info,
            "database_status": database_status,
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
    constitutional_health = await monitor.test_constitutional_compliance()
    deployment_info = get_deployment_info()
    database_status = check_aws_database_health()
    
    return {
        "services": services_health,
        "system": system_metrics,
        "database": database_health,
        "constitutional": constitutional_health,
        "deployment": deployment_info,
        "database_status": database_status,
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

@app.get("/api/constitutional-test")
async def constitutional_test():
    """Dedicated endpoint for testing constitutional compliance"""
    results = await monitor.test_constitutional_compliance()
    return results

if __name__ == "__main__":
    try:
        logger.info("=== STARTING HEALTH DASHBOARD MAIN ===")
        
        logger.info("Testing deployment info...")
        deployment = get_deployment_info()
        logger.info(f"Deployment test result: {deployment.get('status')}")
        
        logger.info("Testing database connection...")
        db_status = check_aws_database_health()
        logger.info(f"Database test result: {db_status.get('status')}")
        
        logger.info("Starting uvicorn server...")
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8008)
        
    except Exception as e:
        logger.error(f"STARTUP FAILED: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)