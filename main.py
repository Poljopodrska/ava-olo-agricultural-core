#!/usr/bin/env python3
"""
AVA OLO Monitoring Dashboards - Modularized Main Application
Version: v2.3.0-ecs-ready
Refactored for AWS ECS deployment with modules under 100KB
"""
import uvicorn
import sys
import os
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# Import configuration
from modules.core.config import VERSION, BUILD_ID, constitutional_deployment_completion, config
from modules.core.database_manager import get_db_manager

# Import API routers
from modules.api.deployment_routes import router as deployment_router, audit_router
from modules.api.database_routes import router as database_router, agricultural_router, debug_router
from modules.api.health_routes import router as health_router
from modules.api.business_routes import router as business_router
from modules.api.dashboard_routes import router as dashboard_router, api_router as dashboard_api_router
from modules.api.deployment_webhook import router as webhook_router
from modules.api.system_routes import router as system_router
from modules.api.debug_services import router as debug_services_router
from modules.api.debug_deployment import router as debug_deployment_router
from modules.api.code_status import router as code_status_router
from api.deployment_security_routes import router as deployment_security_router

# Import dashboard modules
from modules.dashboards.agronomic import router as agronomic_router
from modules.dashboards.business import router as business_dashboard_router
from modules.dashboards.health import router as health_dashboard_router
from modules.dashboards.database import router as database_dashboard_router
from modules.dashboards.deployment import router as deployment_dashboard_router, api_router as deployment_api_router
from modules.dashboards.feature_status import router as feature_status_router

# Import auth module
from modules.auth.routes import router as auth_router

# Import weather module
from modules.weather.routes import router as weather_router

# Import CAVA module
from modules.cava.routes import router as cava_router

# Import fields module
from modules.fields.routes import router as fields_router

# Import chat module - CAVA-powered only
# from modules.chat.routes import router as chat_router  # DISABLED - conflicts with CAVA
from modules.chat.simple_registration import router as simple_registration_router
from modules.api.chat_routes import router as cava_chat_router
from modules.api.cava_audit_routes import router as cava_audit_router
from modules.api.cava_setup_routes import router as cava_setup_router
from modules.api.cava_debug_routes import router as cava_debug_router

# NEW: Import chat debug and behavioral audit routes  
from modules.api.chat_debug_routes import router as chat_debug_router
from modules.api.behavioral_audit_routes import router as behavioral_audit_router

# NEW: Import OpenAI configuration routes
from modules.api.openai_config_routes import router as openai_config_router

# NEW: Import memory training routes
from modules.api.memory_training_routes import router as memory_training_router

# NEW: Import emergency routes
from modules.api.emergency_routes import router as emergency_router

# Import WhatsApp module
from modules.whatsapp.routes import router as whatsapp_router

# Import ENV dashboard module
from api.env_dashboard_routes import router as env_dashboard_router

# Import for startup
import asyncio

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Farmer Portal",
    version=VERSION,
    description="WhatsApp-style farmer portal with weather, chat, and farm management"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler to prevent 503 errors"""
    print(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "The service encountered an error but is still running",
            "path": str(request.url)
        }
    )

# Include routers
app.include_router(deployment_router)
app.include_router(audit_router)
app.include_router(database_router)
app.include_router(agricultural_router)
app.include_router(debug_router)
app.include_router(health_router)
app.include_router(business_router)
app.include_router(dashboard_router)
app.include_router(dashboard_api_router)
app.include_router(agronomic_router)
app.include_router(business_dashboard_router)
app.include_router(health_dashboard_router)
app.include_router(database_dashboard_router)
app.include_router(deployment_dashboard_router)
app.include_router(deployment_api_router)
app.include_router(feature_status_router)
app.include_router(webhook_router)
app.include_router(auth_router)
app.include_router(weather_router)
app.include_router(cava_router)
app.include_router(fields_router)
# app.include_router(chat_router)  # DISABLED - conflicts with CAVA
app.include_router(simple_registration_router)
app.include_router(cava_chat_router)
app.include_router(cava_audit_router)
app.include_router(cava_setup_router)
app.include_router(cava_debug_router)
app.include_router(whatsapp_router)

# NEW: Include chat debug and behavioral audit routers
app.include_router(chat_debug_router)
app.include_router(behavioral_audit_router)

# NEW: Include OpenAI configuration router
app.include_router(openai_config_router)

# NEW: Include memory training router
app.include_router(memory_training_router)

# NEW: Include emergency router
app.include_router(emergency_router)

app.include_router(system_router)
app.include_router(debug_services_router)
app.include_router(debug_deployment_router)
app.include_router(code_status_router)
app.include_router(deployment_security_router)
app.include_router(env_dashboard_router)

@app.on_event("startup")
async def startup_event():
    """Non-blocking startup that doesn't crash the service"""
    try:
        print(f"🚀 Starting AVA OLO Agricultural Core {VERSION}")
        print(f"📦 Build ID: {BUILD_ID}")
        
        # Don't block startup - run validation in background
        asyncio.create_task(run_startup_validation())
        
        # Basic initialization only
        print("✅ Service started - validation running in background")
        
    except Exception as e:
        # Never let startup crash the entire service
        print(f"⚠️ Startup warning (non-fatal): {str(e)}")

async def run_startup_validation():
    """Run validation in background without blocking service"""
    try:
        # Wait a bit for service to fully start
        await asyncio.sleep(5)
        
        print("🔍 Running background validation...")
        
        # Simple OpenAI check without complex recovery
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            import openai
            openai.api_key = api_key
            print("✅ OpenAI API key found")
        else:
            print("⚠️ OpenAI API key not found - chat will be unavailable")
        
        # Simple database check
        try:
            from modules.core.database_manager import get_db_manager
            db_manager = get_db_manager()
            if db_manager.test_connection():
                print("✅ Database connected")
            else:
                print("⚠️ Database connection failed")
        except Exception as e:
            print(f"⚠️ Database issue: {e}")
            
    except Exception as e:
        print(f"⚠️ Background validation error: {e}")
        # Don't crash - service continues running

@app.get("/")
async def root():
    """Root endpoint that always works"""
    return {
        "service": "AVA OLO Agricultural Core",
        "version": VERSION,
        "status": "running",
        "endpoints": {
            "dashboard": "/dashboard",
            "chat_debug": "/chat-debug-audit",
            "health": "/health",
            "diagnostics": "/diagnostics"
        }
    }

@app.get("/cava-audit")
async def cava_audit_page():
    """CAVA implementation audit dashboard"""
    return FileResponse("static/cava-audit.html")

@app.get("/chat-debug-audit")
async def chat_debug_audit_page():
    """Combined chat debug and behavioral audit interface"""
    file_path = os.path.join("static", "chat-debug-audit.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        return {"error": "Debug interface not found", "path_checked": file_path}

@app.get("/api/v1/diagnostics")
async def list_diagnostic_endpoints():
    """List all available diagnostic endpoints"""
    return {
        "diagnostic_endpoints": [
            "/chat-debug-audit - Main debug interface",
            "/api/v1/chat/debug/status - Chat service status",
            "/api/v1/chat/debug/test-message - Test chat directly",
            "/api/v1/cava/audit - Component audit",
            "/api/v1/cava/behavioral-audit - Behavioral audit",
            "/api/v1/cava/behavioral-audit/quick - Quick mango test",
            "/cava-audit - Original CAVA audit interface"
        ],
        "chat_endpoints": [
            "/api/v1/chat - Main chat endpoint",
            "/register - Registration interface"
        ],
        "note": "Access these with the full URL: http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/"
    }

@app.get("/diagnostics")
async def diagnostics_index():
    """Serve diagnostics index page"""
    file_path = os.path.join("static", "diagnostics-index.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        # Fallback to JSON if file not found
        return await list_diagnostic_endpoints()

@app.get("/openai-wizard")
async def openai_setup_wizard():
    """Serve OpenAI setup wizard"""
    file_path = os.path.join("static", "openai-setup-wizard.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        return {"error": "OpenAI wizard not found", "path_checked": file_path}

@app.get("/dashboard")
async def dashboard():
    """Serve dashboard with fallback"""
    try:
        return FileResponse("static/dashboard.html")
    except:
        return {
            "error": "Dashboard temporarily unavailable",
            "message": "Please try /chat-debug-audit instead",
            "alternatives": ["/chat-debug-audit", "/diagnostics", "/health"]
        }

@app.get("/health")
async def health_check():
    """Basic health check that always works"""
    return {
        "status": "ok",
        "service": "AVA OLO Agricultural Core",
        "version": VERSION,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with database status"""
    db_manager = get_db_manager()
    db_healthy = db_manager.test_connection()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "version": VERSION,
        "database": "connected" if db_healthy else "disconnected",
        "service": "agricultural-core"
    }

@app.get("/version")
async def get_version():
    """Get current version"""
    return {"version": VERSION, "build_id": BUILD_ID}

@app.get("/api/v1/emergency/status")
async def emergency_status():
    """Emergency status check that always works"""
    status = {
        "service": "running",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Check OpenAI
    status["components"]["openai"] = bool(os.getenv("OPENAI_API_KEY"))
    
    # Check database
    try:
        db_manager = get_db_manager()
        if db_manager.test_connection():
            status["components"]["database"] = True
        else:
            status["components"]["database"] = False
    except:
        status["components"]["database"] = False
    
    return status

@app.get("/api/v1/system/health")
async def system_health():
    """Comprehensive system health check with auto-recovery"""
    from modules.core.startup_validator import StartupValidator
    from modules.core.api_key_manager import APIKeyManager
    
    # Re-run validation
    validation = await StartupValidator.validate_and_fix()
    
    return {
        "status": "healthy" if validation["system_ready"] else "degraded",
        "timestamp": datetime.now().isoformat(),
        "validation": validation,
        "api_key_info": APIKeyManager.get_diagnostic_info(),
        "quick_fix_available": not validation["system_ready"],
        "version": VERSION
    }

@app.get("/deployment-method")
async def deployment_method():
    """Test endpoint to verify automatic webhook deployment"""
    return {
        "method": "automatic-webhook",
        "manual_commands_needed": False,
        "version": VERSION,
        "message": "Monitoring dashboards deployed automatically via webhook!",
        "test_id": "v3.3.8-webhook-verification"
    }

@app.get("/dashboards/env", response_class=HTMLResponse) 
async def env_dashboard_page():
    """Direct route to ENV dashboard"""
    from api.env_dashboard_routes import _get_dashboard_html
    return HTMLResponse(_get_dashboard_html())

@app.get("/api/deployment/reality-check")
async def deployment_reality_check():
    """Verify actual deployed features vs version claims"""
    import os
    import datetime
    
    # Check if new features actually exist
    features_check = {
        "security_audit_endpoint": any(r.path == "/api/deployment/audit" for r in app.routes),
        "git_verification_module": os.path.exists("modules/core/git_verification.py"),
        "env_scanner_exists": os.path.exists("modules/env_scanner.py"),
        "env_dashboard_routes": any(r.path == "/api/env/scan" for r in app.routes),
        "deployment_security_endpoint": any(r.path == "/api/deployment/source" for r in app.routes),
        "deployment_timestamp": os.getenv('DEPLOYMENT_TIMESTAMP', 'NOT_SET'),
        "github_sha": os.getenv('GITHUB_SHA', 'NOT_SET'),
        "build_id": os.getenv('BUILD_ID', BUILD_ID)
    }
    
    # Get file modification times to verify fresh deployment
    file_checks = {}
    try:
        main_py_mtime = datetime.datetime.fromtimestamp(
            os.path.getmtime(__file__)
        ).isoformat()
        file_checks["main.py"] = main_py_mtime
    except:
        file_checks["main.py"] = "UNKNOWN"
        
    # Check for specific new modules
    for module_path in ["modules/env_scanner.py", "modules/env_verifier.py", "api/env_dashboard_routes.py"]:
        try:
            if os.path.exists(module_path):
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(module_path)).isoformat()
                file_checks[module_path] = mtime
            else:
                file_checks[module_path] = "NOT_FOUND"
        except:
            file_checks[module_path] = "ERROR"
    
    # Count actual features deployed
    feature_count = sum(1 for v in features_check.values() if v and v not in ['NOT_SET', 'NOT_FROM_GITHUB'])
    
    return {
        "claimed_version": VERSION,
        "actual_features": features_check,
        "file_timestamps": file_checks,
        "container_start": datetime.datetime.now().isoformat(),
        "infrastructure": "ECS_ONLY",
        "app_runner_removed": True,
        "feature_count": feature_count,
        "total_features": len(features_check),
        "reality_status": "REAL_DEPLOYMENT" if feature_count >= 5 else "VERSION_ONLY_UPDATE",
        "warning": "VERSION_ONLY_UPDATE - Features missing!" if feature_count < 5 else "OK - Real deployment verified"
    }

# Add remaining dashboard placeholders
@app.get("/database-dashboard", response_class=HTMLResponse)
async def database_dashboard():
    """Database dashboard placeholder"""
    return HTMLResponse(f"""
    <html>
    <head><title>Database Dashboard</title></head>
    <body>
        <h1>Database Dashboard</h1>
        <p>Version: {VERSION}</p>
        <p><a href="/">Back to Home</a></p>
    </body>
    </html>
    """)

@app.get("/health-dashboard", response_class=HTMLResponse)
async def health_dashboard():
    """Health dashboard placeholder"""
    return HTMLResponse(f"""
    <html>
    <head><title>Health Dashboard</title></head>
    <body>
        <h1>Health Dashboard</h1>
        <p>Version: {VERSION}</p>
        <p><a href="/api/v1/health/system-status">System Status</a></p>
        <p><a href="/">Back to Home</a></p>
    </body>
    </html>
    """)

@app.get("/ui-dashboard", response_class=HTMLResponse)
async def ui_dashboard():
    """UI dashboard placeholder"""
    return HTMLResponse(f"""
    <html>
    <head><title>UI Dashboard</title></head>
    <body>
        <h1>UI Dashboard</h1>
        <p>Version: {VERSION}</p>
        <p><a href="/">Back to Home</a></p>
    </body>
    </html>
    """)

# Redirect legacy endpoints
@app.get("/deployment-verify")
async def deployment_verify_redirect():
    """Redirect to new deployment verify endpoint"""
    return RedirectResponse(url="/api/deployment/verify")

if __name__ == "__main__":
    # Report deployment version
    constitutional_deployment_completion()
    
    # Run the application
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8080,
        log_level="info"
    )