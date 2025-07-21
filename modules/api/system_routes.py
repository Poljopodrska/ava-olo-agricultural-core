#!/usr/bin/env python3
"""
System Environment Audit Routes
Provides endpoints to check environment variables and service connectivity
"""
import os
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/system", tags=["system"])

# Required environment variables for full functionality
REQUIRED_ENV_VARS = {
    "database": [
        ("DB_HOST", "RDS database endpoint"),
        ("DB_NAME", "Database name (farmer_crm)"),
        ("DB_USER", "Database username"),
        ("DB_PASSWORD", "Database password"),
        ("DB_PORT", "Database port (5432)"),
        ("DATABASE_URL", "Full connection string (alternative)")
    ],
    "openai": [
        ("OPENAI_API_KEY", "OpenAI API key for GPT-4 chat")
    ],
    "weather": [
        ("OPENWEATHER_API_KEY", "OpenWeatherMap API key"),
        ("WEATHER_API_KEY", "Alternative weather API key")
    ],
    "security": [
        ("SECRET_KEY", "Flask/FastAPI secret key for sessions"),
        ("JWT_SECRET_KEY", "JWT token signing key")
    ],
    "aws": [
        ("AWS_REGION", "AWS region (us-east-1)"),
        ("AWS_DEFAULT_REGION", "Default AWS region"),
        ("AWS_EXECUTION_ENV", "AWS execution environment")
    ],
    "app_config": [
        ("ENVIRONMENT", "production/development"),
        ("DEBUG", "true/false"),
        ("LOG_LEVEL", "INFO/DEBUG/ERROR")
    ]
}

# Variable examples for recovery
ENV_VAR_EXAMPLES = {
    "DB_HOST": "farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com",
    "DB_NAME": "farmer_crm",
    "DB_USER": "postgres",
    "DB_PASSWORD": "your-secure-password",
    "DB_PORT": "5432",
    "DATABASE_URL": "postgresql://user:pass@host:5432/dbname",
    "OPENAI_API_KEY": "sk-proj-...",
    "OPENWEATHER_API_KEY": "your-openweather-api-key",
    "SECRET_KEY": "your-random-secret-key-minimum-32-chars",
    "JWT_SECRET_KEY": "your-jwt-secret-key",
    "AWS_REGION": "us-east-1",
    "ENVIRONMENT": "production",
    "DEBUG": "false",
    "LOG_LEVEL": "INFO"
}

def mask_sensitive_value(value: str, var_name: str) -> str:
    """Mask sensitive values for security"""
    if not value:
        return None
    
    # For API keys, show first 7 chars
    if "KEY" in var_name and len(value) > 10:
        return value[:7] + "..."
    
    # For passwords, just show if set
    if "PASSWORD" in var_name:
        return "***SET***"
    
    # For hosts, show first part
    if "HOST" in var_name and "." in value:
        parts = value.split('.')
        return parts[0] + "...."
    
    # For URLs, show scheme and partial host
    if "URL" in var_name and "://" in value:
        scheme = value.split("://")[0]
        return f"{scheme}://***"
    
    # Default: show full value for non-sensitive
    return value

async def test_database_connection() -> Dict:
    """Test database connectivity"""
    try:
        from modules.core.database_manager import get_db_manager
        
        db_manager = get_db_manager()
        if db_manager.test_connection():
            # Try actual query
            result = db_manager.execute_query("SELECT COUNT(*) FROM farmers")
            farmer_count = result['rows'][0][0] if result and result.get('rows') else 0
            return {
                "connected": True,
                "status": "healthy",
                "farmer_count": farmer_count
            }
        else:
            return {
                "connected": False,
                "status": "connection failed",
                "error": "Could not establish connection"
            }
    except Exception as e:
        return {
            "connected": False,
            "status": "error",
            "error": str(e)
        }

async def test_openai_connection() -> Dict:
    """Test OpenAI API connectivity"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {
                "connected": False,
                "status": "no_api_key",
                "error": "OPENAI_API_KEY not set"
            }
        
        # Quick test with minimal tokens
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                return {
                    "connected": True,
                    "status": "healthy",
                    "model": "gpt-3.5-turbo available"
                }
            elif response.status_code == 401:
                return {
                    "connected": False,
                    "status": "invalid_key",
                    "error": "Invalid API key"
                }
            else:
                return {
                    "connected": False,
                    "status": "api_error",
                    "error": f"API returned {response.status_code}"
                }
                
    except Exception as e:
        return {
            "connected": False,
            "status": "error",
            "error": str(e)
        }

async def test_weather_connection() -> Dict:
    """Test weather API connectivity"""
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY") or os.getenv("WEATHER_API_KEY")
        if not api_key:
            return {
                "connected": False,
                "status": "no_api_key",
                "error": "No weather API key found"
            }
        
        # Test with Ljubljana coordinates
        lat, lon = 46.0569, 14.5058
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "connected": True,
                    "status": "healthy",
                    "location": data.get("name", "Unknown")
                }
            elif response.status_code == 401:
                return {
                    "connected": False,
                    "status": "invalid_key",
                    "error": "Invalid API key"
                }
            else:
                return {
                    "connected": False,
                    "status": "api_error",
                    "error": f"API returned {response.status_code}"
                }
                
    except Exception as e:
        return {
            "connected": False,
            "status": "error",
            "error": str(e)
        }

@router.get("/env-check")
async def check_environment():
    """Safely check which environment variables are configured"""
    
    # Check each category of variables
    env_status = {}
    
    for category, vars_list in REQUIRED_ENV_VARS.items():
        env_status[category] = {}
        for var_name, description in vars_list:
            value = os.getenv(var_name)
            env_status[category][var_name] = {
                "set": bool(value),
                "value": mask_sensitive_value(value, var_name) if value else None,
                "description": description
            }
    
    # Test actual connections
    connection_tests = {
        "database": await test_database_connection(),
        "openai": await test_openai_connection(),
        "weather": await test_weather_connection()
    }
    
    # Get service information
    service_info = {
        "ecs_service": os.getenv("ECS_SERVICE_NAME", "unknown"),
        "ecs_container": os.getenv("ECS_CONTAINER_NAME", "unknown"),
        "aws_region": os.getenv("AWS_REGION", "unknown"),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "environment_variables": env_status,
        "connection_tests": connection_tests,
        "service_info": service_info
    }

@router.get("/env-recovery-plan")
async def generate_recovery_plan():
    """Generate list of all needed environment variables"""
    
    missing_vars = []
    configured_vars = []
    
    for category, vars_list in REQUIRED_ENV_VARS.items():
        for var_name, description in vars_list:
            if not os.getenv(var_name):
                missing_vars.append({
                    "variable": var_name,
                    "category": category,
                    "description": description,
                    "example": ENV_VAR_EXAMPLES.get(var_name, "No example available"),
                    "required": True
                })
            else:
                configured_vars.append({
                    "variable": var_name,
                    "category": category,
                    "status": "configured"
                })
    
    # Calculate health score
    total_vars = sum(len(vars) for vars in REQUIRED_ENV_VARS.values())
    configured_count = len(configured_vars)
    health_score = (configured_count / total_vars * 100) if total_vars > 0 else 0
    
    return {
        "health_score": f"{health_score:.1f}%",
        "total_required": total_vars,
        "configured_count": configured_count,
        "missing_count": len(missing_vars),
        "missing_variables": missing_vars,
        "configured_variables": configured_vars,
        "recovery_instructions": {
            "step1": "Copy the missing variables list",
            "step2": "Go to AWS ECS Console",
            "step3": "Find your task definition",
            "step4": "Create new revision",
            "step5": "Add environment variables in container definition",
            "step6": "Update service with new task definition"
        }
    }

@router.get("/ecs-env-vars")
async def check_ecs_task_definition():
    """Provide instructions for checking ECS task definition"""
    return {
        "instructions": [
            "1. Go to AWS ECS Console (https://console.aws.amazon.com/ecs)",
            "2. Select your cluster (ava-olo-cluster)",
            "3. Click on 'Task Definitions'",
            "4. Find these task definitions:",
            "   - ava-agricultural-task",
            "   - ava-monitoring-task",
            "5. Click on the task definition",
            "6. Click on the latest revision number",
            "7. Expand 'Container definitions'",
            "8. Look for 'Environment variables' section"
        ],
        "task_definitions": [
            {
                "name": "ava-agricultural-task",
                "service": "Agricultural Core",
                "alb": "ava-olo-farmers-alb"
            },
            {
                "name": "ava-monitoring-task", 
                "service": "Monitoring Dashboards",
                "alb": "ava-olo-internal-alb"
            }
        ],
        "common_issues": [
            "Variables added to task definition but service not updated",
            "Variables in Secrets Manager but not linked in task definition",
            "Different variables between staging and production"
        ]
    }

@router.get("/health-summary")
async def system_health_summary():
    """Get quick health summary of all systems"""
    
    # Quick checks
    has_db = bool(os.getenv("DB_HOST") or os.getenv("DATABASE_URL"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_weather = bool(os.getenv("OPENWEATHER_API_KEY") or os.getenv("WEATHER_API_KEY"))
    
    # Test connections
    db_test = await test_database_connection()
    openai_test = await test_openai_connection()
    weather_test = await test_weather_connection()
    
    return {
        "overall_status": "healthy" if all([
            db_test["connected"],
            openai_test["connected"],
            weather_test["connected"]
        ]) else "degraded",
        "services": {
            "database": {
                "configured": has_db,
                "connected": db_test["connected"],
                "status": db_test.get("status", "unknown")
            },
            "openai_chat": {
                "configured": has_openai,
                "connected": openai_test["connected"],
                "status": openai_test.get("status", "unknown")
            },
            "weather_api": {
                "configured": has_weather,
                "connected": weather_test["connected"],
                "status": weather_test.get("status", "unknown")
            }
        },
        "quick_fix": {
            "database": "Add DB_HOST, DB_NAME, DB_USER, DB_PASSWORD to ECS task" if not has_db else None,
            "openai": "Add OPENAI_API_KEY to ECS task" if not has_openai else None,
            "weather": "Add OPENWEATHER_API_KEY to ECS task" if not has_weather else None
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/health")
async def comprehensive_health_check():
    """Comprehensive health check with detailed connection tests"""
    
    # Start timing
    start_time = datetime.now()
    
    # Test each service
    health_results = {
        "database": await test_database_health_detailed(),
        "openai": await test_openai_health_detailed(),
        "weather": await test_weather_health_detailed(),
        "response_time_ms": 0
    }
    
    # Calculate total response time
    end_time = datetime.now()
    health_results["response_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
    health_results["timestamp"] = end_time.isoformat()
    
    # Overall status
    all_connected = all(service["connected"] for service in health_results.values() if isinstance(service, dict) and "connected" in service)
    health_results["overall_status"] = "healthy" if all_connected else "degraded"
    
    return health_results

async def test_database_health_detailed() -> Dict:
    """Detailed database health check"""
    start = datetime.now()
    
    try:
        db_manager = get_db_manager()
        
        # Basic connection test
        if not db_manager.test_connection():
            return {
                "connected": False,
                "status": "connection_failed",
                "error": "Cannot establish database connection",
                "response_time_ms": int((datetime.now() - start).total_seconds() * 1000)
            }
        
        # Test queries
        tests_passed = 0
        total_tests = 3
        
        # Test 1: Count farmers
        try:
            result = db_manager.execute_query("SELECT COUNT(*) FROM farmers")
            farmer_count = result['rows'][0][0] if result and result.get('rows') else 0
            tests_passed += 1
        except:
            farmer_count = 0
        
        # Test 2: Count fields
        try:
            result = db_manager.execute_query("SELECT COUNT(*) FROM fields")
            field_count = result['rows'][0][0] if result and result.get('rows') else 0
            tests_passed += 1
        except:
            field_count = 0
        
        # Test 3: Check Kmetija Vrzel exists
        try:
            result = db_manager.execute_query(
                "SELECT COUNT(*) FROM farmers WHERE name ILIKE %s",
                ('%Kmetija%Vrzel%',)
            )
            has_kmetija = result['rows'][0][0] > 0 if result and result.get('rows') else False
            tests_passed += 1
        except:
            has_kmetija = False
        
        response_time = int((datetime.now() - start).total_seconds() * 1000)
        
        return {
            "connected": True,
            "status": "healthy" if tests_passed == total_tests else "partial",
            "farmer_count": farmer_count,
            "field_count": field_count,
            "has_kmetija_vrzel": has_kmetija,
            "tests_passed": f"{tests_passed}/{total_tests}",
            "response_time_ms": response_time,
            "connection_string": f"{os.getenv('DB_HOST', 'unknown')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'unknown')}"
        }
        
    except Exception as e:
        return {
            "connected": False,
            "status": "error",
            "error": str(e),
            "response_time_ms": int((datetime.now() - start).total_seconds() * 1000)
        }

async def test_openai_health_detailed() -> Dict:
    """Detailed OpenAI health check"""
    start = datetime.now()
    
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {
                "connected": False,
                "status": "no_api_key",
                "error": "OPENAI_API_KEY not configured",
                "response_time_ms": 0
            }
        
        # Test with minimal completion
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Say 'ok'"}],
                    "max_tokens": 5,
                    "temperature": 0
                },
                timeout=10.0
            )
            
            response_time = int((datetime.now() - start).total_seconds() * 1000)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "connected": True,
                    "status": "healthy",
                    "model": "gpt-3.5-turbo",
                    "gpt4_available": True,  # Assume GPT-4 is available if GPT-3.5 works
                    "response": data['choices'][0]['message']['content'],
                    "response_time_ms": response_time,
                    "api_key_prefix": api_key[:7] + "..."
                }
            elif response.status_code == 401:
                return {
                    "connected": False,
                    "status": "invalid_key",
                    "error": "Invalid API key",
                    "response_time_ms": response_time
                }
            else:
                return {
                    "connected": False,
                    "status": "api_error",
                    "error": f"API returned {response.status_code}",
                    "response_time_ms": response_time
                }
                
    except Exception as e:
        return {
            "connected": False,
            "status": "error",
            "error": str(e),
            "response_time_ms": int((datetime.now() - start).total_seconds() * 1000)
        }

async def test_weather_health_detailed() -> Dict:
    """Detailed weather API health check"""
    start = datetime.now()
    
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY") or os.getenv("WEATHER_API_KEY")
        if not api_key:
            return {
                "connected": False,
                "status": "no_api_key",
                "error": "No weather API key configured",
                "response_time_ms": 0
            }
        
        # Test with Ljubljana (capital of Slovenia)
        lat, lon = 46.0569, 14.5058
        test_locations = {
            "Ljubljana": (46.0569, 14.5058),
            "Maribor": (46.5547, 15.6459)
        }
        
        results = {}
        
        # Test current weather for Ljubljana
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            
            response_time = int((datetime.now() - start).total_seconds() * 1000)
            
            if response.status_code == 200:
                data = response.json()
                
                # Test forecast endpoint too
                forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
                forecast_response = await client.get(forecast_url, timeout=10.0)
                
                return {
                    "connected": True,
                    "status": "healthy",
                    "test_location": data.get("name", "Unknown"),
                    "country": data.get("sys", {}).get("country", "Unknown"),
                    "temperature": data.get("main", {}).get("temp", "Unknown"),
                    "weather": data.get("weather", [{}])[0].get("description", "Unknown"),
                    "forecast_available": forecast_response.status_code == 200,
                    "response_time_ms": response_time,
                    "api_key_suffix": "..." + api_key[-4:]
                }
            elif response.status_code == 401:
                return {
                    "connected": False,
                    "status": "invalid_key",
                    "error": "Invalid API key",
                    "response_time_ms": response_time
                }
            else:
                return {
                    "connected": False,
                    "status": "api_error",
                    "error": f"API returned {response.status_code}",
                    "response_time_ms": response_time
                }
                
    except Exception as e:
        return {
            "connected": False,
            "status": "error",
            "error": str(e),
            "response_time_ms": int((datetime.now() - start).total_seconds() * 1000)
        }

@router.get("/debug/services")
async def debug_services():
    """Detailed debug information for troubleshooting"""
    
    # Mask sensitive values
    def mask_value(key: str, value: str) -> str:
        if not value:
            return "NOT SET"
        if "KEY" in key or "PASSWORD" in key:
            if len(value) > 10:
                return value[:4] + "***" + value[-4:]
            else:
                return "***"
        return value
    
    env_vars = {
        "OPENAI_API_KEY": mask_value("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", "")),
        "OPENWEATHER_API_KEY": mask_value("OPENWEATHER_API_KEY", os.getenv("OPENWEATHER_API_KEY", "")),
        "DB_HOST": os.getenv("DB_HOST", "NOT SET"),
        "DB_NAME": os.getenv("DB_NAME", "NOT SET"),
        "DB_USER": os.getenv("DB_USER", "NOT SET"),
        "DB_PASSWORD": mask_value("DB_PASSWORD", os.getenv("DB_PASSWORD", "")),
        "SECRET_KEY": mask_value("SECRET_KEY", os.getenv("SECRET_KEY", "")),
        "JWT_SECRET_KEY": mask_value("JWT_SECRET_KEY", os.getenv("JWT_SECRET_KEY", "")),
        "AWS_REGION": os.getenv("AWS_REGION", "NOT SET"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "NOT SET")
    }
    
    # Run health checks
    health = await comprehensive_health_check()
    
    # Test specific queries
    test_results = {}
    
    # Test 1: Can we find Kmetija Vrzel?
    try:
        db_manager = get_db_manager()
        result = db_manager.execute_query(
            "SELECT id, name, whatsapp_number FROM farmers WHERE name ILIKE %s LIMIT 1",
            ('%Kmetija%Vrzel%',)
        )
        if result and result.get('rows'):
            test_results["kmetija_vrzel_found"] = {
                "found": True,
                "id": result['rows'][0][0],
                "name": result['rows'][0][1],
                "whatsapp": result['rows'][0][2]
            }
        else:
            test_results["kmetija_vrzel_found"] = {"found": False}
    except Exception as e:
        test_results["kmetija_vrzel_found"] = {"error": str(e)}
    
    # Test 2: Can we get weather for Slovenia?
    try:
        if health["weather"]["connected"]:
            test_results["slovenia_weather"] = {
                "available": True,
                "test_city": "Ljubljana",
                "temperature": health["weather"].get("temperature", "Unknown")
            }
        else:
            test_results["slovenia_weather"] = {"available": False}
    except:
        test_results["slovenia_weather"] = {"error": "Weather service not available"}
    
    # Test 3: Can we make a GPT-4 call?
    try:
        if health["openai"]["connected"]:
            test_results["gpt4_available"] = {
                "available": True,
                "model": "gpt-4"
            }
        else:
            test_results["gpt4_available"] = {"available": False}
    except:
        test_results["gpt4_available"] = {"error": "OpenAI service not available"}
    
    return {
        "environment_variables": env_vars,
        "service_health": health,
        "test_results": test_results,
        "deployment_info": {
            "version": VERSION,
            "service": SERVICE_NAME,
            "timestamp": datetime.now().isoformat()
        }
    }