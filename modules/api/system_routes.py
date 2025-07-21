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