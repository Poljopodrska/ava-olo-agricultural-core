#!/usr/bin/env python3
"""
Chat Debug Routes - Comprehensive debugging for chat service unavailability
Identifies OpenAI API key issues, route registration, and CAVA integration problems
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, Any

from modules.core.database_manager import DatabaseManager

router = APIRouter(prefix="/api/v1/chat/debug", tags=["chat-debug"])

class DebugResponse(BaseModel):
    status: str
    timestamp: str
    data: Dict[str, Any]

@router.get("/status")
async def debug_chat_status():
    """Comprehensive chat service debugging to identify unavailability cause"""
    
    status = {
        "service_available": False,
        "checks": {},
        "errors": [],
        "recommendations": [],
        "overall_score": 0
    }
    
    try:
        # Check 1: OpenAI API Key Configuration
        print("🔍 Checking OpenAI API key configuration...")
        api_key = os.getenv("OPENAI_API_KEY", "")
        
        status["checks"]["openai_api_key"] = {
            "present": bool(api_key),
            "length": len(api_key) if api_key else 0,
            "starts_with": api_key[:7] + "..." if len(api_key) > 7 else "NOT_SET",
            "valid_format": api_key.startswith("sk-") if api_key else False,
            "score": 0
        }
        
        if not api_key:
            status["errors"].append("CRITICAL: OPENAI_API_KEY environment variable not set")
            status["recommendations"].append("Add OPENAI_API_KEY to ECS task definition environment variables")
        elif not api_key.startswith("sk-"):
            status["errors"].append("OPENAI_API_KEY has invalid format (should start with 'sk-')")
            status["recommendations"].append("Check if API key is correct OpenAI format")
        elif len(api_key) < 40:
            status["errors"].append("OPENAI_API_KEY appears too short")
            status["recommendations"].append("Verify complete API key was set")
        else:
            status["checks"]["openai_api_key"]["score"] = 10
            print("✅ OpenAI API key properly configured")
        
        # Check 2: OpenAI Client Connection Test
        if status["checks"]["openai_api_key"]["present"]:
            print("🔍 Testing OpenAI connection...")
            try:
                from modules.chat.openai_key_manager import get_openai_client
                
                client = get_openai_client()
                
                if client:
                    # Test with minimal request
                    test_response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=1
                    )
                    
                    status["checks"]["openai_connection"] = {
                        "status": "connected",
                        "model_available": True,
                        "test_response": bool(test_response),
                        "score": 15
                    }
                    status["overall_score"] += 15
                    print("✅ OpenAI connection successful")
                else:
                    status["checks"]["openai_connection"] = {
                        "status": "client_unavailable",
                        "model_available": False,
                        "test_response": False,
                        "score": 0
                    }
                    status["errors"].append("OpenAI client could not be created")
                    
            except Exception as e:
                error_type = type(e).__name__
                status["checks"]["openai_connection"] = {
                    "status": "failed",
                    "model_available": False,
                    "test_response": False,
                    "error": str(e),
                    "error_type": error_type,
                    "score": 0
                }
                
                if "authentication" in str(e).lower() or "401" in str(e):
                    status["errors"].append("OpenAI API key authentication failed")
                    status["recommendations"].append("Check if API key is valid and has credits")
                elif "rate limit" in str(e).lower():
                    status["errors"].append("OpenAI rate limit exceeded")
                    status["recommendations"].append("Check OpenAI account credits and usage limits")
                else:
                    status["errors"].append(f"OpenAI connection failed: {str(e)}")
                    status["recommendations"].append("Check internet connectivity and OpenAI service status")
        
        # Check 3: Database Connection
        print("🔍 Testing database connection...")
        try:
            db_manager = DatabaseManager()
            async with db_manager.get_connection_async() as conn:
                count = await conn.fetchval("SELECT COUNT(*) FROM chat_messages")
                
                status["checks"]["database"] = {
                    "connected": True,
                    "chat_messages_count": count,
                    "tables_exist": True,
                    "score": 10
                }
                status["overall_score"] += 10
                print(f"✅ Database connected ({count} messages)")
                
        except Exception as e:
            status["checks"]["database"] = {
                "connected": False,
                "error": str(e),
                "score": 0
            }
            status["errors"].append(f"Database connection failed: {str(e)}")
            status["recommendations"].append("Check database credentials and network connectivity")
        
        # Check 4: Chat Route Registration
        print("🔍 Checking chat route registration...")
        try:
            from main import app
            
            chat_routes = []
            for route in app.routes:
                path = str(route.path)
                if "chat" in path.lower() and hasattr(route, 'methods'):
                    chat_routes.append({
                        "path": path,
                        "methods": list(route.methods),
                        "module": getattr(route.endpoint, '__module__', 'unknown') if hasattr(route, 'endpoint') else 'unknown'
                    })
            
            # Check for main chat endpoint
            main_chat_route = next((r for r in chat_routes if r["path"] == "/api/v1/chat"), None)
            
            status["checks"]["routes"] = {
                "chat_routes_count": len(chat_routes),
                "main_chat_registered": bool(main_chat_route),
                "paths": [r["path"] for r in chat_routes],
                "main_chat_module": main_chat_route["module"] if main_chat_route else None,
                "score": 10 if main_chat_route else 0
            }
            
            if main_chat_route:
                status["overall_score"] += 10
                print("✅ Main chat route registered")
            else:
                status["errors"].append("Main chat route (/api/v1/chat) not registered")
                status["recommendations"].append("Check main.py includes chat router properly")
                
        except Exception as e:
            status["checks"]["routes"] = {
                "error": str(e),
                "score": 0
            }
            status["errors"].append(f"Route check failed: {str(e)}")
        
        # Check 5: CAVA Memory Module
        print("🔍 Testing CAVA memory module...")
        try:
            from modules.cava.conversation_memory import CAVAMemory
            
            cava = CAVAMemory()
            test_context = await cava.get_conversation_context("+385TEST")
            
            status["checks"]["cava_memory"] = {
                "module_loaded": True,
                "can_get_context": isinstance(test_context, dict),
                "context_has_summary": bool(test_context.get("context_summary")),
                "score": 10
            }
            status["overall_score"] += 10
            print("✅ CAVA memory module working")
            
        except Exception as e:
            status["checks"]["cava_memory"] = {
                "module_loaded": False,
                "error": str(e),
                "score": 0
            }
            status["errors"].append(f"CAVA memory module failed: {str(e)}")
            status["recommendations"].append("Check CAVA module imports and database schema")
        
        # Check 6: Chat Endpoint Function
        print("🔍 Testing chat endpoint function...")
        try:
            from modules.api.chat_routes import chat_endpoint
            import inspect
            
            # Get function signature
            sig = inspect.signature(chat_endpoint)
            source_available = True
            
            try:
                source = inspect.getsource(chat_endpoint)
                has_cava_code = "CAVAMemory" in source or "get_enhanced_context" in source
                function_size = len(source)
            except:
                source_available = False
                has_cava_code = False
                function_size = 0
            
            status["checks"]["chat_endpoint"] = {
                "function_exists": True,
                "signature_valid": len(sig.parameters) > 0,
                "source_available": source_available,
                "has_cava_code": has_cava_code,
                "function_size": function_size,
                "score": 10 if has_cava_code else 5
            }
            
            if has_cava_code:
                status["overall_score"] += 10
                print("✅ Chat endpoint has CAVA integration")
            else:
                status["overall_score"] += 5
                status["errors"].append("Chat endpoint may not have CAVA integration")
                
        except ImportError as e:
            status["checks"]["chat_endpoint"] = {
                "function_exists": False,
                "error": str(e),
                "score": 0
            }
            status["errors"].append(f"Chat endpoint import failed: {str(e)}")
            status["recommendations"].append("Check chat_routes.py exists and has chat_endpoint function")
        except Exception as e:
            status["checks"]["chat_endpoint"] = {
                "function_exists": False,
                "error": str(e),
                "score": 0
            }
            status["errors"].append(f"Chat endpoint check failed: {str(e)}")
        
        # Overall Assessment
        max_score = 65  # 10 + 15 + 10 + 10 + 10 + 10
        status["overall_score"] = min(status["overall_score"], max_score)
        status["score_percentage"] = (status["overall_score"] / max_score) * 100
        
        if status["overall_score"] >= 50:
            status["service_available"] = True
            status["overall_status"] = "Service should be available"
            print("✅ Chat service checks passed")
        else:
            status["overall_status"] = f"Service unavailable - {len(status['errors'])} critical issues"
            print(f"❌ Chat service has issues (score: {status['overall_score']}/{max_score})")
        
        # Add specific next steps
        if not status["service_available"]:
            if not status["checks"]["openai_api_key"]["present"]:
                status["next_steps"] = [
                    "1. Add OPENAI_API_KEY to ECS task definition",
                    "2. Restart ECS service",
                    "3. Test again"
                ]
            elif status["checks"]["openai_connection"].get("error"):
                status["next_steps"] = [
                    "1. Verify OpenAI API key is correct",
                    "2. Check OpenAI account has credits",
                    "3. Test API key manually"
                ]
            else:
                status["next_steps"] = [
                    "1. Check application logs for detailed errors",
                    "2. Run /api/v1/chat/debug/test-message",
                    "3. Check ECS task environment variables"
                ]
        
        return DebugResponse(
            status="success",
            timestamp=datetime.now().isoformat(),
            data=status
        )
        
    except Exception as e:
        print(f"❌ Debug check failed: {str(e)}")
        return DebugResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            data={"error": str(e), "checks_completed": status.get("checks", {})}
        )

@router.post("/test-message")
async def test_chat_directly():
    """Test chat functionality directly to isolate issues"""
    
    print("🧪 Testing chat endpoint directly...")
    
    try:
        from modules.api.chat_routes import chat_endpoint, ChatRequest
        
        test_request = ChatRequest(
            wa_phone_number="+385DEBUG",
            message="Hello, this is a debug test message"
        )
        
        print(f"📝 Sending test request: {test_request.message}")
        
        response = await chat_endpoint(test_request)
        
        print(f"✅ Chat test successful")
        
        return {
            "status": "success",
            "chat_working": True,
            "test_request": {
                "phone": test_request.wa_phone_number,
                "message": test_request.message
            },
            "response": {
                "response": response.response if hasattr(response, 'response') else str(response),
                "model_used": getattr(response, 'model_used', 'unknown'),
                "context_used": getattr(response, 'context_used', False),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        import traceback
        
        print(f"❌ Chat test failed: {str(e)}")
        
        # Detailed error analysis
        error_analysis = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "is_openai_error": "openai" in str(e).lower(),
            "is_auth_error": "authentication" in str(e).lower() or "401" in str(e),
            "is_import_error": isinstance(e, ImportError),
            "is_db_error": "database" in str(e).lower() or "connection" in str(e).lower()
        }
        
        return {
            "status": "error",
            "chat_working": False,
            "error": str(e),
            "error_analysis": error_analysis,
            "traceback": traceback.format_exc(),
            "recommendation": "Check the error type and run /api/v1/chat/debug/status for detailed analysis"
        }

@router.get("/fix-attempt")
async def attempt_chat_fix():
    """Attempt to fix common chat service issues"""
    
    print("🔧 Attempting to fix chat service issues...")
    
    fixes_applied = []
    warnings = []
    
    try:
        # Fix 1: Check OpenAI API key availability
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            warnings.append("OpenAI API key not found in environment - needs ECS task definition update")
        else:
            fixes_applied.append("OpenAI API key found in environment")
        
        # Fix 2: Initialize OpenAI client properly
        try:
            from modules.chat.openai_key_manager import get_openai_client
            
            client = get_openai_client()
            if client:
                fixes_applied.append("OpenAI client initialized successfully")
            else:
                warnings.append("OpenAI client could not be initialized")
                
        except Exception as e:
            warnings.append(f"OpenAI client initialization failed: {str(e)}")
        
        # Fix 3: Verify chat route registration
        try:
            from main import app
            
            # Check if chat routes exist
            chat_paths = [str(r.path) for r in app.routes if "chat" in str(r.path).lower()]
            
            if "/api/v1/chat" in chat_paths:
                fixes_applied.append("Main chat route (/api/v1/chat) is registered")
            else:
                warnings.append("Main chat route not found - may need route re-registration")
                
        except Exception as e:
            warnings.append(f"Route verification failed: {str(e)}")
        
        # Fix 4: Test CAVA memory initialization
        try:
            from modules.cava.conversation_memory import CAVAMemory
            
            cava = CAVAMemory()
            test_context = await cava.get_conversation_context("+385TESTFIX")
            
            if isinstance(test_context, dict):
                fixes_applied.append("CAVA memory module working correctly")
            else:
                warnings.append("CAVA memory returned unexpected result")
                
        except Exception as e:
            warnings.append(f"CAVA memory test failed: {str(e)}")
        
        # Fix 5: Environment variable check
        env_vars_checked = [
            "OPENAI_API_KEY",
            "DB_HOST", 
            "DB_NAME",
            "DB_USER",
            "DB_PASSWORD"
        ]
        
        missing_env_vars = []
        for var in env_vars_checked:
            if not os.getenv(var):
                missing_env_vars.append(var)
        
        if missing_env_vars:
            warnings.append(f"Missing environment variables: {', '.join(missing_env_vars)}")
        else:
            fixes_applied.append("All critical environment variables present")
        
        # Fix 6: Database connection test
        try:
            db_manager = DatabaseManager()
            async with db_manager.get_connection_async() as conn:
                await conn.fetchval("SELECT 1")
            fixes_applied.append("Database connection verified")
            
        except Exception as e:
            warnings.append(f"Database connection issue: {str(e)}")
        
        # Determine overall fix status
        if not warnings:
            fix_status = "all_good"
            recommendation = "All systems appear functional. If chat still fails, check application logs."
        elif len(fixes_applied) > len(warnings):
            fix_status = "mostly_fixed"
            recommendation = "Some issues found but most systems working. Address warnings listed."
        else:
            fix_status = "issues_remain"
            recommendation = "Significant issues found. Address critical warnings before using chat."
        
        return {
            "fix_status": fix_status,
            "fixes_applied": fixes_applied,
            "warnings": warnings,
            "fixes_count": len(fixes_applied),
            "warnings_count": len(warnings),
            "recommendation": recommendation,
            "next_steps": [
                "Run /api/v1/chat/debug/status for detailed analysis",
                "Test with /api/v1/chat/debug/test-message",
                "Check ECS task definition if API key issues persist"
            ]
        }
        
    except Exception as e:
        return {
            "fix_status": "error",
            "error": str(e),
            "recommendation": "Fix attempt failed - check application logs for details"
        }

@router.get("/environment")
async def check_environment_variables():
    """Check critical environment variables for chat service"""
    
    critical_vars = {
        "OPENAI_API_KEY": "OpenAI API access",
        "DB_HOST": "Database connection",
        "DB_NAME": "Database name", 
        "DB_USER": "Database user",
        "DB_PASSWORD": "Database password"
    }
    
    optional_vars = {
        "DB_PORT": "Database port (defaults to 5432)",
        "AWS_REGION": "AWS region for services",
        "ECS_CONTAINER_METADATA_URI_V4": "ECS container metadata"
    }
    
    env_status = {
        "critical_vars": {},
        "optional_vars": {},
        "missing_critical": [],
        "environment_score": 0
    }
    
    # Check critical variables
    for var, description in critical_vars.items():
        value = os.getenv(var)
        
        if value:
            env_status["critical_vars"][var] = {
                "present": True,
                "description": description,
                "length": len(value),
                "preview": value[:7] + "..." if len(value) > 10 else value if var != "DB_PASSWORD" else "***"
            }
            env_status["environment_score"] += 20
        else:
            env_status["critical_vars"][var] = {
                "present": False,
                "description": description,
                "length": 0,
                "preview": "NOT_SET"
            }
            env_status["missing_critical"].append(var)
    
    # Check optional variables
    for var, description in optional_vars.items():
        value = os.getenv(var)
        
        env_status["optional_vars"][var] = {
            "present": bool(value),
            "description": description,
            "value": value if value and len(value) < 50 else (value[:47] + "..." if value else "NOT_SET")
        }
    
    # Assessment
    if not env_status["missing_critical"]:
        env_status["status"] = "all_critical_present"
        env_status["recommendation"] = "All critical environment variables are configured"
    else:
        env_status["status"] = "missing_critical_vars"
        env_status["recommendation"] = f"Missing critical variables: {', '.join(env_status['missing_critical'])}"
    
    env_status["container_info"] = {
        "is_ecs": bool(os.getenv("ECS_CONTAINER_METADATA_URI_V4")),
        "python_path": sys.path[0],
        "working_directory": os.getcwd(),
        "platform": sys.platform
    }
    
    return env_status