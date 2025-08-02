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
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates

# Import configuration
from modules.core.config import VERSION, BUILD_ID, constitutional_deployment_completion, config
from modules.core.database_manager import get_db_manager
from modules.core.version_badge_middleware import VersionBadgeMiddleware

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

# Import WhatsApp webhook handler (removed old conflicting router)
from modules.whatsapp.webhook_handler import router as whatsapp_webhook_router

# Import payment modules
from modules.api.payment_routes import router as payment_router
from modules.api.admin_routes import router as admin_payment_router
from modules.stripe_webhook import router as stripe_webhook_router
from modules.usage_middleware import track_usage_middleware

# Import ENV dashboard module
from api.env_dashboard_routes import router as env_dashboard_router

# Import comprehensive audit routes
from modules.api.cava_comprehensive_audit_routes import router as cava_comprehensive_audit_router

# Import CAVA registration routes
from modules.api.cava_registration_routes import router as cava_registration_router

# Import chat history routes
from modules.api.chat_history_routes import router as chat_history_router

# Import dashboard chat routes
from modules.api.dashboard_chat_routes import router as dashboard_chat_router

# Import farmer debug routes
from modules.api.farmer_debug_routes import router as farmer_debug_router

# Import farmer dashboard routes
from modules.api.farmer_dashboard_routes import router as farmer_dashboard_router

# Import database test routes
from modules.api.db_test_routes import router as db_test_router

# Import migration routes
from modules.api.migration_routes import router as migration_router

# Import cleanup routes
from modules.api.database_cleanup_routes import router as cleanup_router
from modules.api.simple_cleanup import router as simple_cleanup_router
from modules.api.direct_cleanup import router as direct_cleanup_router
from modules.api.cascade_migration import router as cascade_router
from modules.api.final_cleanup import router as final_cleanup_router
from modules.api.hierarchy_implementation import router as hierarchy_router
from modules.api.smart_cleanup import router as smart_cleanup_router
from modules.api.robust_cleanup import router as robust_cleanup_router
from modules.api.farmer_query import router as farmer_query_router
from modules.api.quick_check import router as quick_check_router

# Import for startup
import asyncio
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Farmer Portal",
    version=VERSION,
    description="WhatsApp-style farmer portal with weather, chat, and farm management"
)

# Add usage tracking middleware
@app.middleware("http")
async def usage_tracking(request: Request, call_next):
    return await track_usage_middleware(request, call_next)

# Add version badge middleware
app.add_middleware(VersionBadgeMiddleware)

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
# app.include_router(chat_router)  # DISABLED - conflicts with CAVA
app.include_router(simple_registration_router)
app.include_router(cava_chat_router)
app.include_router(chat_history_router)
app.include_router(dashboard_chat_router)
app.include_router(farmer_debug_router)
app.include_router(farmer_dashboard_router)
app.include_router(db_test_router)
app.include_router(migration_router)
app.include_router(cleanup_router)
app.include_router(simple_cleanup_router)
app.include_router(direct_cleanup_router)
app.include_router(cascade_router)
app.include_router(final_cleanup_router)
app.include_router(hierarchy_router)
app.include_router(smart_cleanup_router)
app.include_router(robust_cleanup_router)
app.include_router(farmer_query_router)
app.include_router(quick_check_router)
app.include_router(cava_audit_router)
app.include_router(cava_setup_router)
app.include_router(cava_debug_router)
app.include_router(whatsapp_webhook_router)

# Include payment routers
app.include_router(payment_router)
app.include_router(admin_payment_router)
app.include_router(stripe_webhook_router)

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
app.include_router(cava_comprehensive_audit_router)
app.include_router(cava_registration_router)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup with comprehensive validation and auto-recovery"""
    print(f"🚀 Starting AVA OLO Agricultural Core {VERSION} with self-healing system")
    print(f"📦 Build ID: {BUILD_ID}")
    
    # NEW: Run comprehensive startup validation
    from modules.core.startup_validator import StartupValidator
    from modules.core.api_key_manager import APIKeyManager
    
    print("🔍 Running comprehensive startup validation...")
    validation_report = await StartupValidator.validate_and_fix()
    
    if validation_report["system_ready"]:
        print("✅ System validation passed - all systems operational")
    else:
        print("⚠️ System validation failed - operating in degraded mode")
        print(f"Failed checks: {[k for k,v in validation_report['checks'].items() if not v]}")
        print(f"Fixes applied: {validation_report.get('fixes_applied', [])}")
    
    # Start continuous health monitoring
    asyncio.create_task(StartupValidator.continuous_health_check())
    print("🏥 Started continuous health monitoring (checks every 5 minutes)")
    
    # Log API key diagnostic info
    api_key_info = APIKeyManager.get_diagnostic_info()
    print(f"🔑 API Key Status: {api_key_info}")
    
    # Initialize database connection pool with retry logic
    db_manager = get_db_manager()
    print("🔄 Testing database connection with retry logic...")
    if db_manager.test_connection(retries=5, delay=3):
        print("✅ Database connection established")
        
        # Run database migrations
        print("🔄 Running database migrations...")
        try:
            from modules.core.migration_runner import run_startup_migrations
            migration_result = run_startup_migrations()
            
            if migration_result["success"]:
                print(f"✅ {migration_result['message']}")
            else:
                print(f"⚠️ Migration warning: {migration_result['message']}")
        except Exception as e:
            print(f"⚠️ Migration failed: {str(e)} - continuing anyway")
        
        # Ensure CAVA tables exist (fallback if migrations didn't work)
        print("🔄 Ensuring CAVA tables exist...")
        try:
            from modules.api.cava_audit_routes import ensure_cava_tables_startup
            await ensure_cava_tables_startup()
            print("✅ CAVA tables verified")
        except Exception as e:
            print(f"⚠️ CAVA table check failed: {str(e)} - continuing anyway")
        
    else:
        print("⚠️ Database connection failed after retries - running in degraded mode")
        print("⚠️ Service will continue to run and serve requests without database")
    
    # Initialize OpenAI configuration - CONSTITUTIONAL REQUIREMENT
    print("🔑 Initializing OpenAI configuration...")
    from modules.core.openai_config import OpenAIConfig
    
    if OpenAIConfig.initialize():
        print("✅ OpenAI configured successfully - Constitutional compliance verified")
        openai_status = OpenAIConfig.get_status()
        print(f"🔑 API key format valid: {openai_status.get('api_key_format_valid', False)}")
        print(f"🔑 Key preview: {openai_status.get('api_key_preview', 'NOT_SET')}")
    else:
        print("🚨 CRITICAL WARNING: OpenAI configuration failed!")
        print("🏛️ CONSTITUTIONAL VIOLATION: System requires 95%+ LLM intelligence (Amendment #15)")
        print("⚠️  Chat service will be unavailable - NOT COMPLIANT!")
        
        # Show detailed status for debugging
        openai_status = OpenAIConfig.get_status()
        print(f"🔍 OpenAI Status: {openai_status}")
        
        # Try to load from .env.production if available
        try:
            from dotenv import load_dotenv
            env_path = ".env.production"
            if os.path.exists(env_path):
                load_dotenv(env_path)
                print("🔄 Attempting re-initialization after loading .env.production...")
                if OpenAIConfig.initialize(force=True):
                    print("✅ OpenAI configured after loading .env.production")
                else:
                    print("❌ OpenAI configuration still failed after .env.production")
            else:
                print("❌ .env.production file not found")
        except ImportError:
            print("⚠️  python-dotenv not installed, cannot auto-load .env files")
    
    # Initialize CAVA Chat Engine
    print("🤖 Initializing CAVA Chat Engine...")
    from modules.cava.chat_engine import initialize_cava
    cava_initialized = await initialize_cava()
    if cava_initialized:
        print("✅ CAVA Chat Engine ready for intelligent agricultural conversations")
    else:
        print("⚠️ CAVA Chat Engine initialization failed - chat may be limited")
    
    # Constitutional deployment completion
    constitutional_deployment_completion()

@app.get("/subscription-success", response_class=HTMLResponse)
async def subscription_success(request: Request):
    """Subscription success page"""
    return templates.TemplateResponse("subscription_success.html", {
        "request": request
    })

@app.get("/")
async def landing_page(request: Request):
    """Landing page with Sign In and New with AVA OLO buttons"""
    return templates.TemplateResponse("landing.html", {
        "request": request,
        "version": VERSION
    })

@app.get("/cava-audit")
async def cava_audit_page():
    """CAVA implementation audit dashboard"""
    return FileResponse("static/cava-audit.html")

@app.get("/cava-comprehensive-audit")
async def cava_comprehensive_audit_page():
    """CAVA comprehensive audit dashboard with advanced scoring"""
    return FileResponse("static/cava-comprehensive-audit.html")

@app.get("/cava-gpt-test")
async def cava_gpt_test_page():
    """CAVA GPT integration verification test page"""
    return FileResponse("static/cava-gpt-test.html")

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
async def dashboard(request: Request):
    """Redirect to farmer dashboard for standardized experience"""
    farmer_id = request.cookies.get("farmer_id")
    
    if not farmer_id:
        return RedirectResponse(url="/auth/signin", status_code=303)
    
    # Redirect to farmer dashboard for standardized UI
    return RedirectResponse(url="/farmer/dashboard", status_code=303)

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

@app.get("/run-migration")
async def run_migration_page():
    """Serve migration tool page"""
    return FileResponse("static/run-migration.html")

@app.get("/cleanup-farmers")
async def cleanup_farmers_page():
    """Serve cleanup tool page"""
    return FileResponse("static/cleanup-farmers.html")

@app.get("/hierarchy-setup")
async def hierarchy_setup_page():
    """Serve database hierarchy setup page"""
    return FileResponse("static/hierarchy-setup.html")

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

@app.get("/api/deployment/status")
async def deployment_status():
    """Get deployment status for version badge"""
    try:
        # Check if critical services are working
        db_manager = get_db_manager()
        db_connected = db_manager.test_connection()
        
        # Check for key features deployment - fix route checking
        features_deployed = {
            "version_badge": True,  # We're running this code
            "cava_endpoint": any("/api/v1/chat" in str(r.path) for r in app.routes),
            "audit_dashboard": any("/cava-audit" in str(r.path) for r in app.routes),
            "database": db_connected,
            "openai_configured": bool(os.getenv('OPENAI_API_KEY'))
        }
        
        fully_deployed = all(features_deployed.values())
        
        return {
            "version": VERSION,
            "fully_deployed": fully_deployed,
            "features": features_deployed,
            "deployment_time": os.getenv('DEPLOYMENT_TIMESTAMP', datetime.now().isoformat()),
            "build_id": BUILD_ID
        }
    except Exception as e:
        logger.error(f"Deployment status error: {e}")
        return {
            "version": VERSION,
            "fully_deployed": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

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

# ============================================================================
# SAFETY MONITORING ENDPOINTS - ZERO REGRESSION ADDITIONS ONLY
# These endpoints are completely isolated and cannot affect existing functionality
# ============================================================================

from modules.safety_monitor import SafetyMonitor
from fastapi.responses import JSONResponse

# Initialize safety monitor with its own isolated connection
safety_monitor = SafetyMonitor()

@app.get("/health-monitor", response_class=HTMLResponse)
async def health_monitor_dashboard():
    """
    Safety monitoring dashboard - READ ONLY
    Completely isolated from main application
    Cannot affect existing functionality
    """
    try:
        return HTMLResponse(content=safety_monitor.render_dashboard())
    except Exception as e:
        # If monitoring fails, it doesn't affect the main app
        return HTMLResponse(content=f"""
        <html>
        <head><title>Safety Monitor Error</title></head>
        <body>
            <h1>Safety Monitor Temporarily Unavailable</h1>
            <p>The monitoring system encountered an error but the main application is unaffected.</p>
            <p>Error: {str(e)}</p>
            <p><a href="/">Return to Main Application</a></p>
        </body>
        </html>
        """)

@app.get("/api/v1/safety/health")
async def safety_health_check():
    """
    JSON health check endpoint - READ ONLY
    Returns system health metrics without affecting operation
    """
    try:
        health_data = safety_monitor.check_system_health()
        return JSONResponse(content=health_data)
    except Exception as e:
        # Monitoring failure doesn't affect main app
        return JSONResponse(
            content={
                "status": "monitor_error",
                "message": str(e),
                "note": "Main application unaffected"
            },
            status_code=503
        )

# ============================================================================
# END OF SAFETY MONITORING ADDITIONS
# ============================================================================

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