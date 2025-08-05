#!/usr/bin/env python3
"""
AVA OLO Agricultural Core v4.0.2
Production release with basic auth protection and 20 routers
"""
import uvicorn
import sys
import os
import logging
import asyncio
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates

# Set up logger
logger = logging.getLogger(__name__)

# Templates
templates = Jinja2Templates(directory="templates")

# Configuration
from modules.core.config import VERSION, BUILD_ID, constitutional_deployment_completion, config
from modules.core.language_service import get_language_service
from modules.core.translations import get_translations
from modules.api.health_routes import router as health_router

# Startup modules
from modules.core.startup_validator import StartupValidator
from modules.core.api_key_manager import APIKeyManager
from modules.core.database_manager import get_db_manager

# Core routers
from modules.api.deployment_routes import router as deployment_router, audit_router
from modules.api.database_routes import router as database_router, agricultural_router, debug_router
from modules.api.business_routes import router as business_router
# Dashboard routes moved to monitoring-dashboards service
from modules.api.deployment_webhook import router as webhook_router
from modules.api.system_routes import router as system_router
from modules.api.debug_services import router as debug_services_router
from modules.api.debug_deployment import router as debug_deployment_router
from modules.api.code_status import router as code_status_router
from modules.auth.routes import router as auth_router
from modules.weather.routes import router as weather_router
from modules.api.farmer_dashboard_routes import router as farmer_dashboard_router

# CAVA routers
from modules.cava.routes import router as cava_router

# Chat routers
from modules.api.chat_routes import router as chat_router
from modules.api.chat_history_routes import router as chat_history_router
from modules.api.task_management_routes import router as task_management_router
from modules.api.debug_edi_kante import router as debug_edi_router

# WhatsApp integration
from modules.whatsapp.webhook_handler import router as whatsapp_router

# Global authentication middleware
from modules.core.global_auth import GlobalAuthMiddleware

# Create FastAPI app
app = FastAPI(title="AVA OLO Agricultural Core", version=VERSION)

# Add global authentication middleware - this MUST protect everything
app.add_middleware(GlobalAuthMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Track startup status
STARTUP_STATUS = {
    "validation_result": None,
    "db_test": None,
    "monitoring_started": False,
    "total_routers_included": 0,
    "phase": "production",
    "error": None
}

# Root endpoint - Landing page
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Landing page with Sign In / New to AVA OLO options"""
    try:
        # Detect language from IP address
        language_service = get_language_service()
        
        # Get client IP - check for forwarded headers first (for deployment behind proxy)
        client_ip = request.headers.get("X-Forwarded-For")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "127.0.0.1"
        
        logger.info(f"Landing page accessed from IP: {client_ip}")
        
        # Try to detect language, but don't fail if it doesn't work
        try:
            detected_language = await language_service.detect_language_from_ip(client_ip)
        except Exception as e:
            logger.warning(f"Language detection failed for IP {client_ip}: {e}")
            detected_language = 'en'  # Default to English
        
        # Get translations for the detected language
        translations = get_translations(detected_language)
        
        return templates.TemplateResponse("landing.html", {
            "request": request,
            "version": VERSION,
            "language": detected_language,
            "t": translations
        })
    except Exception as e:
        logger.error(f"Error in landing page: {e}")
        # Return a basic English version if all else fails
        return templates.TemplateResponse("landing.html", {
            "request": request,
            "version": VERSION,
            "language": "en",
            "t": get_translations("en")
        })

# Health endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "version": VERSION}

# Debug endpoint to test auth - protected by global middleware
@app.get("/debug/auth-test")
async def auth_test(request: Request):
    """Debug endpoint to test if auth is working - protected by global middleware"""
    auth_header = request.headers.get("Authorization", "None")
    authenticated_user = getattr(request.state, 'authenticated_user', 'Unknown')
    return {
        "message": "Authentication successful!",
        "auth_header_present": bool(auth_header != "None"),
        "authenticated_user": authenticated_user,
        "path": str(request.url.path),
        "version": VERSION
    }

# Debug endpoint to test signin components
@app.get("/debug/signin-test")
async def signin_debug(request: Request):
    """Debug signin components to find the error"""
    import os
    import traceback
    
    debug_results = {
        "version": VERSION,
        "timestamp": str(request.headers.get("date", "unknown")),
        "tests": {}
    }
    
    # Test 1: Check template file
    try:
        template_path = "templates/auth/signin.html"
        exists = os.path.exists(template_path)
        if exists:
            size = os.path.getsize(template_path)
            debug_results["tests"]["template_file"] = {"status": "OK", "size": size}
        else:
            debug_results["tests"]["template_file"] = {"status": "MISSING"}
    except Exception as e:
        debug_results["tests"]["template_file"] = {"status": "ERROR", "error": str(e)}
    
    # Test 2: Check language service
    try:
        from modules.core.language_service import get_language_service
        lang_service = get_language_service()
        debug_results["tests"]["language_service"] = {"status": "OK", "type": str(type(lang_service))}
    except Exception as e:
        debug_results["tests"]["language_service"] = {"status": "ERROR", "error": str(e)}
    
    # Test 3: Check translations
    try:
        from modules.core.translations import get_translations
        t = get_translations('en')
        debug_results["tests"]["translations"] = {
            "status": "OK", 
            "type": str(type(t)),
            "has_sign_in_title": hasattr(t, 'sign_in_title'),
            "sign_in_title": getattr(t, 'sign_in_title', 'MISSING')
        }
    except Exception as e:
        debug_results["tests"]["translations"] = {"status": "ERROR", "error": str(e)}
    
    # Test 4: Try to simulate signin_page logic
    try:
        from modules.core.language_service import get_language_service
        from modules.core.translations import get_translations
        
        language_service = get_language_service()
        client_ip = "127.0.0.1"
        
        # Try language detection
        try:
            detected_language = await language_service.detect_language_from_ip(client_ip)
        except:
            detected_language = 'en'
            
        translations = get_translations(detected_language)
        
        # Prepare template context
        context = {
            "request": request,
            "version": VERSION,
            "language": detected_language,
            "t": translations
        }
        
        debug_results["tests"]["signin_logic"] = {
            "status": "OK",
            "detected_language": detected_language,
            "context_keys": list(context.keys())
        }
        
    except Exception as e:
        debug_results["tests"]["signin_logic"] = {
            "status": "ERROR", 
            "error": str(e),
            "traceback": traceback.format_exc()
        }
    
    return debug_results

# Minimal signin test endpoint to isolate the issue
@app.get("/debug/minimal-signin")
async def minimal_signin_test(request: Request):
    """Minimal signin test to isolate template rendering issue"""
    try:
        # Try to render just the template with minimal context
        return templates.TemplateResponse("auth/signin.html", {
            "request": request,
            "version": "v4.4.11",
            "language": "en",
            "t": {"sign_in_title": "Sign In", "whatsapp_label": "WhatsApp", "password_label": "Password", "sign_in_button": "Sign In"}
        })
    except Exception as e:
        import traceback
        return {
            "error": "Template rendering failed",
            "message": str(e),
            "traceback": traceback.format_exc(),
            "template_path": "auth/signin.html"
        }

# Include all routers
app.include_router(health_router)
app.include_router(deployment_router)
app.include_router(audit_router)
app.include_router(database_router)
app.include_router(agricultural_router)
app.include_router(debug_router)
app.include_router(business_router)
# Dashboard routers moved to monitoring-dashboards service
app.include_router(webhook_router)
app.include_router(system_router)
app.include_router(debug_services_router)
app.include_router(debug_deployment_router)
app.include_router(code_status_router)
app.include_router(auth_router)
app.include_router(weather_router)
app.include_router(farmer_dashboard_router)
app.include_router(cava_router)
app.include_router(chat_router)
app.include_router(chat_history_router)
app.include_router(whatsapp_router)
app.include_router(task_management_router)
app.include_router(debug_edi_router)
STARTUP_STATUS["total_routers_included"] = 22

# Startup event
@app.on_event("startup")
async def startup_event():
    """Core startup for production with 22 routers and basic auth"""
    global STARTUP_STATUS
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION} with 22 routers and basic auth protection")
    
    # Run validation
    try:
        validation_report = await StartupValidator.validate_and_fix()
        STARTUP_STATUS["validation_result"] = validation_report.get("system_ready", False)
    except Exception as e:
        STARTUP_STATUS["error"] = f"Validation: {str(e)}"
    
    # Test database
    try:
        db_manager = get_db_manager()
        if db_manager.test_connection(retries=5, delay=3):
            STARTUP_STATUS["db_test"] = "success"
    except Exception as e:
        STARTUP_STATUS["error"] = f"Database: {str(e)}"
    
    # Start monitoring
    try:
        asyncio.create_task(StartupValidator.continuous_health_check())
        STARTUP_STATUS["monitoring_started"] = True
    except Exception as e:
        STARTUP_STATUS["error"] = f"Monitoring: {str(e)}"
    
    logger.info("AVA OLO Agricultural Core ready - v4.0.2 Production with Basic Auth")
    constitutional_deployment_completion()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)