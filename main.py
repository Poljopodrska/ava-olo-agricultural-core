#!/usr/bin/env python3
"""
AVA OLO Monitoring Dashboards - Modularized Main Application
Version: v2.3.0-ecs-ready
Refactored for AWS ECS deployment with modules under 100KB
"""
import uvicorn
import sys
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
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

# Import chat module
from modules.chat.routes import router as chat_router
from modules.chat.simple_registration import router as simple_registration_router

# Import WhatsApp module
from modules.whatsapp.routes import router as whatsapp_router

# Import ENV dashboard module
from api.env_dashboard_routes import router as env_dashboard_router

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
app.include_router(chat_router)
app.include_router(simple_registration_router)
app.include_router(whatsapp_router)
app.include_router(system_router)
app.include_router(debug_services_router)
app.include_router(debug_deployment_router)
app.include_router(code_status_router)
app.include_router(deployment_security_router)
app.include_router(env_dashboard_router)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup with resilience"""
    print(f"🚀 Starting AVA OLO Agricultural Core {VERSION}")
    print(f"📦 Build ID: {BUILD_ID}")
    
    # Initialize database connection pool with retry logic
    db_manager = get_db_manager()
    print("🔄 Testing database connection with retry logic...")
    if db_manager.test_connection(retries=5, delay=3):
        print("✅ Database connection established")
    else:
        print("⚠️ Database connection failed after retries - running in degraded mode")
        print("⚠️ Service will continue to run and serve requests without database")
    
    # Check OpenAI configuration - CONSTITUTIONAL REQUIREMENT
    if not os.getenv("OPENAI_API_KEY"):
        print("🚨 CRITICAL WARNING: OPENAI_API_KEY not set!")
        print("🏛️ CONSTITUTIONAL VIOLATION: System requires 95%+ LLM intelligence (Amendment #15)")
        print("⚠️  Registration and chat will use fallback responses - NOT COMPLIANT!")
        
        # Try to load from .env.production if available
        try:
            from dotenv import load_dotenv
            env_path = ".env.production"
            if os.path.exists(env_path):
                load_dotenv(env_path)
                if os.getenv("OPENAI_API_KEY"):
                    print("✅ Loaded OPENAI_API_KEY from .env.production")
                else:
                    print("❌ .env.production exists but OPENAI_API_KEY not found")
            else:
                print("❌ .env.production file not found")
        except ImportError:
            print("⚠️  python-dotenv not installed, cannot auto-load .env files")
    else:
        print("✅ OpenAI API key configured - Constitutional compliance verified")
        print(f"🔑 Key prefix: {os.getenv('OPENAI_API_KEY')[:10]}...")
    
    # Constitutional deployment completion
    constitutional_deployment_completion()

@app.get("/")
async def landing_page(request: Request):
    """Landing page with Sign In and New with AVA OLO buttons"""
    return templates.TemplateResponse("landing.html", {
        "request": request,
        "version": VERSION
    })

@app.get("/dashboard")
async def dashboard(request: Request):
    """Basic dashboard - placeholder for three-panel layout"""
    farmer_name = request.cookies.get("farmer_name", "Farmer")
    farmer_id = request.cookies.get("farmer_id")
    
    if not farmer_id:
        return RedirectResponse(url="/auth/signin", status_code=303)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "version": VERSION,
        "farmer_name": farmer_name
    })

@app.get("/health")
async def health_check():
    """Fast health check endpoint for ALB - doesn't check DB to avoid startup issues"""
    # Quick health check that always returns healthy if the service is running
    # Database connection is checked separately in /health/detailed
    return {
        "status": "healthy",
        "version": VERSION,
        "service": "agricultural-core"
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