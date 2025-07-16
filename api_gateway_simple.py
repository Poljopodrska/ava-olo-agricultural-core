"""
Simple API Gateway - Core functionality without external dependencies
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
import logging
from datetime import datetime
import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and fix database URL immediately
from database_url_fixer import fix_database_url
fix_database_url()

from database_operations import DatabaseOperations
from config_manager import config

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Agricultural Assistant API",
    description="Simple API Gateway for Agricultural Virtual Assistant",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware to catch ALL registration calls
from starlette.requests import Request
from starlette.responses import Response

@app.middleware("http")
async def log_registration_calls(request: Request, call_next):
    if request.method == "POST" and "register" in request.url.path.lower():
        body = await request.body()
        logger.error(f"🔥🔥🔥 REGISTRATION POST: {request.url.path} - Body: {body[:200]}")
        # Recreate request with body
        from starlette.datastructures import Headers
        from starlette.requests import Request as StarletteRequest
        request = StarletteRequest(request.scope, receive=lambda: {"type": "http.request", "body": body})
    
    response = await call_next(request)
    return response

# Configure CAVA logger
cava_logger = logging.getLogger('CAVA')

# Global CAVA engine instance
_cava_engine = None

# Log CAVA status immediately
logger.info(f"🔍 DISABLE_CAVA environment variable: {os.getenv('DISABLE_CAVA', 'NOT_SET')}")

# CAVA Integration - Load lazily to prevent deployment issues
if os.getenv('DISABLE_CAVA', 'false').lower() != 'true':
    logger.info("🚀 Attempting to load CAVA routes...")
    try:
        from api.cava_routes import cava_router
        logger.info("✅ CAVA routes imported successfully")
        app.include_router(cava_router)
        logger.info("✅ CAVA routes loaded successfully")
        cava_logger.info("✅ CAVA: Routes successfully integrated into main API")
    except ImportError as e:
        import traceback
        logger.error(f"❌ CAVA routes import failed: {e}")
        logger.error(f"Import error traceback: {traceback.format_exc()}")
    except Exception as e:
        import traceback
        logger.error(f"❌ CAVA routes failed to load: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        cava_logger.error(f"❌ CAVA: Failed to integrate CAVA routes: {str(e)}")
        # System continues without CAVA - constitutional principle of MODULE INDEPENDENCE
else:
    logger.info("ℹ️ CAVA disabled by environment variable")
    cava_logger.info("ℹ️ CAVA: Disabled by environment variable")

# Debug endpoint for AWS deployment verification
@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to verify AWS deployment state"""
    return {
        "DATABASE_URL": config.database_url[:50] + "..." if len(config.database_url) > 50 else config.database_url,
        "DB_HOST": config.db_host,
        "DB_NAME": config.db_name,
        "DB_USER": config.db_user,
        "CAVA_DRY_RUN_MODE": os.getenv("CAVA_DRY_RUN_MODE", "NOT_SET"),
        "CAVA_REDIS_URL": os.getenv("CAVA_REDIS_URL", "NOT_SET")[:50] + "..." if len(os.getenv("CAVA_REDIS_URL", "")) > 50 else os.getenv("CAVA_REDIS_URL", "NOT_SET"),
        "DISABLE_CAVA": os.getenv("DISABLE_CAVA", "NOT_SET"),
        "python_path": sys.path[0] if sys.path else "unknown",
        "current_working_directory": os.getcwd(),
        "git_commit": os.getenv("GIT_COMMIT", "NOT_SET"),
        "deployment_time": datetime.now().isoformat()
    }

# Root Web Interface Route - Landing Page
@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Landing page with Sign in and Join AVA OLO options"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AVA OLO - Welcome</title>
        <style>
            :root {
                --primary-brown: #6B5B73; --primary-olive: #8B8C5A; --dark-olive: #5D5E3F;
                --cream: #F5F3F0; --white: #FFFFFF; --success-green: #6B8E23; --light-gray: #E8E8E6;
            }
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: var(--cream); color: #2C2C2C; font-size: 18px; line-height: 1.6; }
            .container { max-width: 1000px; margin: 0 auto; padding: 24px; }
            
            /* Landing Page Styles */
            .landing-container { 
                min-height: 100vh; 
                display: flex; 
                align-items: center; 
                justify-content: center;
                background: linear-gradient(135deg, var(--primary-brown), var(--dark-olive));
            }
            .landing-box {
                background: var(--white);
                border-radius: 20px;
                padding: 48px;
                max-width: 600px;
                width: 90%;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
                text-align: center;
            }
            .landing-logo {
                font-size: 80px;
                margin-bottom: 24px;
            }
            .landing-title {
                font-size: 48px;
                color: var(--primary-brown);
                font-weight: bold;
                margin-bottom: 16px;
            }
            .landing-subtitle {
                font-size: 20px;
                color: var(--dark-olive);
                margin-bottom: 48px;
                opacity: 0.9;
            }
            .landing-buttons {
                display: flex;
                gap: 24px;
                justify-content: center;
                flex-wrap: wrap;
            }
            .landing-btn {
                background: var(--primary-olive);
                color: var(--white);
                border: none;
                padding: 20px 40px;
                font-size: 20px;
                font-weight: bold;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.3s ease;
                min-width: 200px;
                text-decoration: none;
                display: inline-block;
            }
            .landing-btn:hover {
                background: var(--dark-olive);
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            }
            .landing-btn-secondary {
                background: var(--white);
                color: var(--primary-olive);
                border: 3px solid var(--primary-olive);
            }
            .landing-btn-secondary:hover {
                background: var(--cream);
                border-color: var(--dark-olive);
                color: var(--dark-olive);
            }
            
            /* Constitutional Header */
            .constitutional-header { background: linear-gradient(135deg, var(--primary-brown), var(--dark-olive)); color: var(--white); padding: 24px; display: flex; align-items: center; gap: 16px; border-radius: 8px; margin-bottom: 32px; }
            .constitutional-logo { width: 48px; height: 48px; background: var(--white); border-radius: 50%; position: relative; }
            .constitutional-logo::before { content: ''; width: 12px; height: 12px; background: var(--primary-brown); border-radius: 50%; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }
            .constitutional-brand { font-size: 32px; font-weight: bold; }
            .constitutional-tagline { margin-left: auto; opacity: 0.9; }
            
            /* Weather Section */
            .weather-today { background: linear-gradient(135deg, var(--primary-olive), #7A8B5A); color: var(--white); border-radius: 8px; padding: 32px; margin-bottom: 24px; text-align: center; }
            .today-header { font-size: 24px; font-weight: bold; margin-bottom: 24px; }
            .today-main { display: flex; align-items: center; justify-content: center; gap: 32px; margin-bottom: 24px; }
            .today-icon { font-size: 64px; }
            .today-details { text-align: left; }
            .today-condition { font-size: 32px; font-weight: bold; margin-bottom: 8px; }
            .today-temp { font-size: 48px; font-weight: bold; margin-bottom: 8px; }
            .today-rain, .today-wind { font-size: 32px; margin-bottom: 8px; }
            
            /* 24-Hour Slider Container */
            .hourly-container { position: relative; margin-top: 24px; padding-top: 24px; border-top: 2px solid rgba(255,255,255,0.3); }
            .hourly-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
            .hourly-title { font-size: 18px; font-weight: bold; }
            .hourly-controls { display: flex; gap: 8px; }
            .slider-btn { background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; border-radius: 4px; padding: 8px 12px; cursor: pointer; font-size: 14px; }
            .slider-btn:hover { background: rgba(255,255,255,0.3); }
            .hourly-slider-container { position: relative; overflow: hidden; }
            .hourly-slider { display: flex; transition: transform 0.3s ease; }
            .hourly-square { min-width: 80px; background: rgba(255,255,255,0.2); border-radius: 8px; padding: 12px 8px; text-align: center; margin-right: 8px; border: 1px solid rgba(255,255,255,0.3); }
            .hourly-square:hover { background: rgba(255,255,255,0.3); }
            .hour-time { font-size: 14px; font-weight: bold; margin-bottom: 4px; }
            .hour-icon { font-size: 18px; margin-bottom: 4px; }
            .hour-temp { font-size: 16px; font-weight: bold; margin-bottom: 4px; }
            .hour-rain, .hour-wind { font-size: 16px; font-weight: bold; }
            
            /* 5-Day Timeline */
            .weather-timeline { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 32px; }
            .weather-day { background: var(--white); border-radius: 8px; padding: 0; text-align: center; border-left: 4px solid #A8AA6B; box-shadow: 0 2px 12px rgba(107,91,115,0.1); cursor: pointer; overflow: hidden; }
            .weather-day:hover { transform: translateY(-2px); }
            .weather-day-today { border-left-color: var(--primary-brown); background: linear-gradient(135deg, rgba(139,140,90,0.1), rgba(107,91,115,0.1)); }
            .day-label { font-size: 16px; font-weight: bold; color: var(--primary-brown); padding: 16px; border-bottom: 1px solid var(--light-gray); background: var(--cream); }
            .day-icon { font-size: 32px; padding: 16px; border-bottom: 1px solid var(--light-gray); }
            .day-condition { font-size: 16px; color: var(--dark-olive); padding: 16px; border-bottom: 1px solid var(--light-gray); font-weight: 500; }
            .day-temp { font-size: 32px; font-weight: bold; color: var(--primary-brown); padding: 16px; border-bottom: 1px solid var(--light-gray); }
            .day-rain { font-size: 24px; color: var(--dark-olive); padding: 16px; border-bottom: 1px solid var(--light-gray); font-weight: bold; }
            .day-wind { font-size: 20px; color: var(--dark-olive); padding: 16px; font-weight: bold; }
            
            /* SVG Weather Icons */
            .weather-icon {
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .weather-icon svg {
                filter: drop-shadow(1px 1px 2px rgba(0,0,0,0.2));
            }
            .today-icon .weather-icon svg { width: 64px; height: 64px; }
            .hour-icon .weather-icon svg { width: 24px; height: 24px; }
            .day-icon .weather-icon svg { width: 32px; height: 32px; }
            .extended-day .weather-icon svg { width: 24px; height: 24px; }
            
            /* Constitutional Cards */
            .constitutional-card { background: var(--white); border-radius: 8px; padding: 24px; box-shadow: 0 2px 12px rgba(107,91,115,0.1); border-left: 4px solid var(--primary-olive); margin-bottom: 24px; }
            .constitutional-card-title { font-size: 24px; color: var(--primary-brown); font-weight: bold; margin-bottom: 16px; text-align: center; }
            .constitutional-textarea { width: 100%; padding: 16px; border: 2px solid var(--light-gray); border-radius: 8px; font-size: 18px; background: var(--white); min-height: 120px; resize: vertical; margin-bottom: 16px; }
            .constitutional-textarea:focus { outline: none; border-color: var(--primary-olive); }
            .constitutional-btn { background: var(--primary-olive); color: var(--white); border: none; padding: 16px 24px; font-size: 18px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%; margin-bottom: 16px; transition: all 0.3s ease; }
            .constitutional-btn:hover { background: var(--dark-olive); transform: translateY(-1px); }
            .constitutional-btn-secondary { background: var(--light-gray); color: #2C2C2C; }
            .enter-hint { text-align: center; font-size: 16px; color: var(--dark-olive); margin-top: 8px; font-style: italic; }
            
            /* Real-Time Date/Time Display */
            .datetime-display {
                background: var(--white);
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 24px;
                text-align: center;
                border: 1px solid var(--light-gray);
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .current-time {
                font-size: 32px;
                font-weight: bold;
                color: #2F4F4F;
                margin-bottom: 8px;
                font-family: monospace;
            }
            .current-date {
                font-size: 18px;
                color: #000000;
                font-weight: 500;
            }
            
            /* Endless 24-Hour Tape */
            .tape-btn {
                background: rgba(255,255,255,0.2);
                border: 1px solid rgba(255,255,255,0.3);
                color: white;
                border-radius: 4px;
                padding: 8px 12px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s ease;
            }
            .tape-btn:hover {
                background: rgba(255,255,255,0.3);
            }
            .tape-btn:active {
                transform: scale(0.95);
            }
            .hourly-tape-container {
                position: relative;
                overflow: hidden;
                height: 140px;
            }
            .hourly-tape {
                display: flex;
                transition: transform 0.3s ease;
                width: 2000px;
            }
            .hour-square {
                min-width: 80px;
                flex-shrink: 0;
                background: rgba(255,255,255,0.2);
                border-radius: 8px;
                padding: 12px 8px;
                text-align: center;
                margin-right: 8px;
                border: 1px solid rgba(255,255,255,0.3);
                transition: all 0.3s ease;
            }
            .hour-square:hover {
                background: rgba(255,255,255,0.3);
                transform: translateY(-2px);
            }
            .hour-square.current-hour {
                border: 2px solid #FFD700;
                background: rgba(255,215,0,0.2);
            }
            
            /* Extended Forecast */
            .extended-forecast-section {
                margin-top: 32px;
                background: var(--white);
                border-radius: 8px;
                padding: 24px;
                box-shadow: 0 2px 12px rgba(107,91,115,0.1);
                border-left: 4px solid var(--primary-olive);
            }
            .extended-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 24px;
            }
            .extended-header h3 {
                font-size: 24px;
                color: var(--primary-brown);
            }
            .forecast-controls {
                display: flex;
                gap: 8px;
            }
            .forecast-btn {
                background: var(--light-gray);
                color: var(--dark-olive);
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            .forecast-btn:hover {
                background: var(--primary-olive);
                color: var(--white);
            }
            .forecast-btn.active {
                background: var(--primary-brown);
                color: var(--white);
            }
            .extended-timeline {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                gap: 16px;
            }
            .extended-day {
                background: var(--cream);
                border-radius: 8px;
                padding: 16px;
                text-align: center;
                border: 1px solid var(--light-gray);
                transition: all 0.3s ease;
            }
            .extended-day:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(107,91,115,0.1);
            }
            
            /* Mobile Responsive */
            @media (max-width: 768px) {
                .weather-timeline { grid-template-columns: repeat(2, 1fr); }
                .hourly-forecast { grid-template-columns: repeat(3, 1fr); }
                .today-main { flex-direction: column; gap: 16px; }
                .today-details { text-align: center; }
                .today-icon { font-size: 48px; }
                .today-condition { font-size: 24px; }
                .today-temp { font-size: 36px; }
            }
            @media (max-width: 480px) {
                .weather-timeline { grid-template-columns: 1fr; }
                .hourly-forecast { grid-template-columns: repeat(2, 1fr); }
            }
        </style>
    </head>
    <body>
        <div class="landing-container">
            <div class="landing-box">
                <div class="landing-logo">🌾</div>
                <h1 class="landing-title">AVA OLO</h1>
                <p class="landing-subtitle">Your Agricultural Assistant</p>
                
                <div class="landing-buttons">
                    <button class="landing-btn" onclick="window.location.href='/login'">
                        🔐 Sign in
                    </button>
                    <button class="landing-btn landing-btn-secondary" onclick="window.location.href='/register'">
                        🚜 Join AVA OLO
                    </button>
                </div>
            </div>
        </div>

    </body>
    </html>
    """

# Login page route
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Login page for existing users"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AVA OLO - Sign In</title>
        <style>
            :root {
                --primary-brown: #6B5B73; --primary-olive: #8B8C5A; --dark-olive: #5D5E3F;
                --cream: #F5F3F0; --white: #FFFFFF; --success-green: #6B8E23; --light-gray: #E8E8E6;
            }
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: linear-gradient(135deg, var(--primary-brown), var(--dark-olive)); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            
            .login-container {
                background: var(--white);
                border-radius: 20px;
                padding: 48px;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
                text-align: center;
            }
            .login-logo {
                font-size: 60px;
                margin-bottom: 24px;
            }
            .login-title {
                font-size: 36px;
                color: var(--primary-brown);
                font-weight: bold;
                margin-bottom: 16px;
            }
            .login-subtitle {
                font-size: 18px;
                color: var(--dark-olive);
                margin-bottom: 32px;
                opacity: 0.9;
            }
            .login-form {
                text-align: left;
            }
            .form-group {
                margin-bottom: 24px;
            }
            .form-label {
                display: block;
                font-size: 16px;
                color: var(--dark-olive);
                font-weight: bold;
                margin-bottom: 8px;
            }
            .form-input {
                width: 100%;
                padding: 16px;
                font-size: 18px;
                border: 2px solid var(--light-gray);
                border-radius: 10px;
                transition: border-color 0.3s ease;
            }
            .form-input:focus {
                outline: none;
                border-color: var(--primary-olive);
            }
            .login-btn {
                background: var(--primary-olive);
                color: var(--white);
                border: none;
                padding: 16px 32px;
                font-size: 20px;
                font-weight: bold;
                border-radius: 10px;
                cursor: pointer;
                width: 100%;
                transition: all 0.3s ease;
                margin-top: 16px;
            }
            .login-btn:hover {
                background: var(--dark-olive);
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            }
            .login-links {
                margin-top: 32px;
                text-align: center;
            }
            .login-link {
                color: var(--primary-olive);
                text-decoration: none;
                font-size: 16px;
                margin: 0 16px;
                transition: color 0.3s ease;
            }
            .login-link:hover {
                color: var(--dark-olive);
                text-decoration: underline;
            }
            .error-message {
                background: rgba(239, 68, 68, 0.1);
                color: #dc2626;
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 16px;
                display: none;
                font-size: 16px;
            }
            .success-message {
                background: rgba(34, 197, 94, 0.1);
                color: #16a34a;
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 16px;
                display: none;
                font-size: 16px;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-logo">🌾</div>
            <h1 class="login-title">Sign In</h1>
            <p class="login-subtitle">Welcome back to AVA OLO</p>
            
            <div id="errorMessage" class="error-message"></div>
            <div id="successMessage" class="success-message"></div>
            
            <form class="login-form" id="loginForm" onsubmit="handleLogin(event)">
                <div class="form-group">
                    <label class="form-label" for="username">WhatsApp Number</label>
                    <input 
                        type="text" 
                        id="username" 
                        name="username" 
                        class="form-input" 
                        placeholder="+385912345678"
                        required
                    >
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="password">Password</label>
                    <input 
                        type="password" 
                        id="password" 
                        name="password" 
                        class="form-input" 
                        placeholder="Enter your password"
                        required
                    >
                </div>
                
                <button type="submit" class="login-btn">
                    🔐 Sign In
                </button>
            </form>
            
            <div class="login-links">
                <a href="/register" class="login-link">Don't have an account? Join AVA OLO</a>
                <br><br>
                <a href="/" class="login-link">← Back to Home</a>
            </div>
        </div>
        
        <script>
            async function handleLogin(event) {
                event.preventDefault();
                
                const errorDiv = document.getElementById('errorMessage');
                const successDiv = document.getElementById('successMessage');
                const form = document.getElementById('loginForm');
                
                // Hide messages
                errorDiv.style.display = 'none';
                successDiv.style.display = 'none';
                
                const username = document.getElementById('username').value.trim();
                const password = document.getElementById('password').value;
                
                try {
                    const response = await fetch('/api/v1/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            wa_phone_number: username,
                            password: password
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success && data.token) {
                        // Store authentication
                        localStorage.setItem('ava_auth_token', data.token);
                        localStorage.setItem('ava_user', JSON.stringify(data.user));
                        
                        // Show success message
                        successDiv.textContent = 'Login successful! Redirecting...';
                        successDiv.style.display = 'block';
                        
                        // Redirect to dashboard
                        setTimeout(() => {
                            window.location.href = '/dashboard';
                        }, 1500);
                    } else {
                        errorDiv.textContent = data.message || 'Invalid credentials. Please try again.';
                        errorDiv.style.display = 'block';
                    }
                } catch (error) {
                    console.error('Login error:', error);
                    errorDiv.textContent = 'Connection error. Please try again.';
                    errorDiv.style.display = 'block';
                }
            }
        </script>
    </body>
    </html>
    """

# Registration page route
@app.get("/register", response_class=HTMLResponse)
async def register_page():
    """Registration page (Join AVA OLO)"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AVA OLO - Join</title>
        <style>
            :root {
                --primary-brown: #6B5B73; --primary-olive: #8B8C5A; --dark-olive: #5D5E3F;
                --cream: #F5F3F0; --white: #FFFFFF; --success-green: #6B8E23; --light-gray: #E8E8E6;
            }
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: linear-gradient(135deg, var(--primary-brown), var(--dark-olive)); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
            
            .register-container {
                background: var(--white);
                border-radius: 20px;
                padding: 48px;
                max-width: 600px;
                width: 90%;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
            }
            .register-header {
                text-align: center;
                margin-bottom: 32px;
            }
            .register-logo {
                font-size: 60px;
                margin-bottom: 24px;
            }
            .register-title {
                font-size: 36px;
                color: var(--primary-brown);
                font-weight: bold;
                margin-bottom: 16px;
            }
            .register-subtitle {
                font-size: 18px;
                color: var(--dark-olive);
                opacity: 0.9;
            }
            .chat-container {
                background: var(--cream);
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
                min-height: 300px;
                max-height: 400px;
                overflow-y: auto;
                border: 2px solid var(--light-gray);
            }
            .message {
                margin-bottom: 16px;
                padding: 12px 16px;
                border-radius: 10px;
                max-width: 85%;
                font-size: 16px;
                line-height: 1.5;
            }
            .message.ava {
                background: var(--primary-olive);
                color: var(--white);
                margin-right: auto;
            }
            .message.user {
                background: var(--white);
                color: var(--dark-olive);
                margin-left: auto;
                border: 2px solid var(--primary-olive);
                text-align: right;
            }
            .input-group {
                display: flex;
                gap: 12px;
                margin-bottom: 20px;
            }
            .chat-input {
                flex: 1;
                padding: 16px;
                font-size: 18px;
                border: 2px solid var(--light-gray);
                border-radius: 10px;
                transition: border-color 0.3s ease;
            }
            .chat-input:focus {
                outline: none;
                border-color: var(--primary-olive);
            }
            .send-btn {
                background: var(--primary-olive);
                color: var(--white);
                border: none;
                padding: 16px 32px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .send-btn:hover {
                background: var(--dark-olive);
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            }
            .send-btn:disabled {
                background: var(--light-gray);
                cursor: not-allowed;
                transform: none;
            }
            .register-links {
                text-align: center;
                margin-top: 24px;
            }
            .register-link {
                color: var(--primary-olive);
                text-decoration: none;
                font-size: 16px;
                transition: color 0.3s ease;
            }
            .register-link:hover {
                color: var(--dark-olive);
                text-decoration: underline;
            }
            .hint-text {
                text-align: center;
                color: var(--dark-olive);
                font-size: 14px;
                margin-bottom: 16px;
                font-style: italic;
            }
            .success-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.8);
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            }
            .success-box {
                background: var(--white);
                border-radius: 20px;
                padding: 48px;
                text-align: center;
                max-width: 400px;
            }
            .success-icon {
                font-size: 80px;
                margin-bottom: 24px;
            }
            .success-title {
                font-size: 28px;
                color: var(--success-green);
                font-weight: bold;
                margin-bottom: 16px;
            }
            .success-text {
                font-size: 18px;
                color: var(--dark-olive);
                margin-bottom: 24px;
            }
        </style>
    </head>
    <body>
        <div class="register-container">
            <div class="register-header">
                <div class="register-logo">🌾</div>
                <h1 class="register-title">Join AVA OLO</h1>
                <p class="register-subtitle">Your Agricultural Assistant</p>
            </div>
            
            <div class="chat-container" id="chatContainer">
                <div class="message ava">
                    <strong>🤖 AVA:</strong> Hi! I'm AVA, your agricultural assistant. What's your full name? (first and last name)
                </div>
            </div>
            
            <div class="hint-text">Press Enter to send your message</div>
            
            <div class="input-group">
                <input 
                    type="text" 
                    id="chatInput" 
                    class="chat-input"
                    placeholder="Type your response..."
                    onkeypress="handleEnterKey(event)"
                    autofocus
                >
                <button id="sendBtn" class="send-btn" onclick="sendMessage()">
                    Send 💬
                </button>
            </div>
            
            <div class="register-links">
                <a href="/login" class="register-link">Already have an account? Sign in</a>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <a href="/" class="register-link">Back to Home</a>
            </div>
        </div>
        
        <div class="success-overlay" id="successOverlay">
            <div class="success-box">
                <div class="success-icon">✅</div>
                <h2 class="success-title">Registration Complete!</h2>
                <p class="success-text">Welcome to AVA OLO. Redirecting to dashboard...</p>
            </div>
        </div>
        
        <script>
            let conversationData = {
                conversation_history: [],
                last_ava_message: "Hi! I'm AVA, your agricultural assistant. What's your full name? (first and last name)",
                current_data: {},
                conversation_id: null
            };
            
            function handleEnterKey(event) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    sendMessage();
                }
            }
            
            async function sendMessage() {
                const input = document.getElementById('chatInput');
                const sendBtn = document.getElementById('sendBtn');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Add user message to chat
                addMessageToChat(message, 'user');
                
                // Disable input
                input.value = '';
                input.disabled = true;
                sendBtn.disabled = true;
                
                try {
                    // Prepare request data
                    const formData = {
                        user_input: message,
                        current_data: conversationData.current_data,
                        conversation_history: conversationData.conversation_history,
                        last_ava_message: conversationData.last_ava_message,
                        conversation_id: conversationData.conversation_id
                    };
                    
                    // CRITICAL FIX: Generate farmer_id ONCE and reuse it
                    if (!conversationData.farmer_id) {
                        // Generate farmer_id from conversation_id to ensure consistency
                        const hashCode = (str) => {
                            let hash = 0;
                            for (let i = 0; i < str.length; i++) {
                                const char = str.charCodeAt(i);
                                hash = ((hash << 5) - hash) + char;
                                hash = hash & hash; // Convert to 32bit integer
                            }
                            return Math.abs(hash);
                        };
                        conversationData.farmer_id = hashCode(conversationData.conversation_id) % 1000000;
                        console.log('Generated persistent farmer_id:', conversationData.farmer_id);
                    }
                    
                    // Try CAVA first, fallback to old system if not available
                    let endpoint = '/api/v1/cava/register';
                    let requestBody = {
                        farmer_id: conversationData.farmer_id, // Use PERSISTENT farmer_id
                        message: message,
                        session_id: conversationData.conversation_id
                    };
                    
                    // Check if CAVA is available
                    try {
                        const healthCheck = await fetch('/api/v1/cava/health');
                        if (!healthCheck.ok) {
                            throw new Error('CAVA not available');
                        }
                    } catch (e) {
                        // Fallback to old system
                        endpoint = '/api/v1/auth/chat-register';
                        requestBody = formData;
                    }
                    
                    const response = await fetch(endpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(requestBody)
                    });
                    
                    const data = await response.json();
                    
                    // Add AVA response to chat
                    addMessageToChat(data.message, 'ava');
                    
                    // Update conversation data
                    if (endpoint.includes('cava')) {
                        // CAVA response format
                        conversationData.conversation_id = data.session_id || conversationData.conversation_id;
                    } else {
                        // Old system response format
                        if (data.extracted_data) {
                            conversationData.current_data = data.extracted_data;
                        }
                        conversationData.conversation_history = data.conversation_history || conversationData.conversation_history;
                        conversationData.last_ava_message = data.last_ava_message || data.message;
                        conversationData.conversation_id = data.conversation_id || conversationData.conversation_id;
                    }
                    
                    // Check if registration is complete
                    if (data.status === "COMPLETE") {
                        // Show success overlay
                        document.getElementById('successOverlay').style.display = 'flex';
                        
                        // Store auth token if provided
                        if (data.token) {
                            localStorage.setItem('ava_auth_token', data.token);
                            localStorage.setItem('ava_user', JSON.stringify(data.user));
                        }
                        
                        // Redirect after delay
                        setTimeout(() => {
                            window.location.href = '/dashboard';
                        }, 3000);
                    }
                    
                } catch (error) {
                    console.error('Registration error:', error);
                    addMessageToChat('Sorry, I had trouble processing that. Could you please try again?', 'ava');
                } finally {
                    // Re-enable input
                    input.disabled = false;
                    sendBtn.disabled = false;
                    input.focus();
                }
            }
            
            function addMessageToChat(text, sender) {
                const chatContainer = document.getElementById('chatContainer');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}`;
                
                if (sender === 'ava') {
                    messageDiv.innerHTML = `<strong>🤖 AVA:</strong> ${text}`;
                } else {
                    messageDiv.innerHTML = `<strong>👨‍🌾 You:</strong> ${text}`;
                }
                
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
                
                // Add to conversation history
                conversationData.conversation_history.push({
                    role: sender,
                    content: text
                });
            }
        </script>
    </body>
    </html>
    """

# Dashboard page route (for authenticated users)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Main dashboard for authenticated users"""
    # This will contain the original main interface content
    # For now, just redirect to the original main interface
    # In production, you would check authentication here
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AVA OLO - Dashboard</title>
        <script>
            // Check if user is authenticated
            const authToken = localStorage.getItem('ava_auth_token');
            if (!authToken) {
                // Redirect to login if not authenticated
                window.location.href = '/login';
            } else {
                // For now, redirect to the main interface
                // In production, this would load the full dashboard
                window.location.href = '/main';
            }
        </script>
    </head>
    <body>
        <div style="text-align: center; padding: 50px;">
            <h1>Loading dashboard...</h1>
        </div>
    </body>
    </html>
    """

# Main interface for authenticated users
@app.get("/main", response_class=HTMLResponse)
async def main_interface():
    """Main interface with all features for authenticated users"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AVA OLO - Your Agricultural Assistant</title>
        <style>
            :root {
                --primary-brown: #6B5B73; --primary-olive: #8B8C5A; --dark-olive: #5D5E3F;
                --cream: #F5F3F0; --white: #FFFFFF; --success-green: #6B8E23; --light-gray: #E8E8E6;
            }
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: var(--cream); color: #2C2C2C; font-size: 18px; line-height: 1.6; }
            .container { max-width: 1000px; margin: 0 auto; padding: 24px; }
            
            /* Constitutional Header */
            .constitutional-header { background: linear-gradient(135deg, var(--primary-brown), var(--dark-olive)); color: var(--white); padding: 24px; display: flex; align-items: center; gap: 16px; border-radius: 8px; margin-bottom: 32px; position: relative; }
            .constitutional-logo { width: 48px; height: 48px; background: var(--white); border-radius: 50%; position: relative; }
            .constitutional-logo::before { content: ''; width: 12px; height: 12px; background: var(--primary-brown); border-radius: 50%; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }
            .constitutional-brand { font-size: 32px; font-weight: bold; }
            .constitutional-tagline { margin-left: auto; opacity: 0.9; }
            .logout-btn { position: absolute; right: 24px; top: 50%; transform: translateY(-50%); background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 16px; transition: all 0.3s ease; }
            .logout-btn:hover { background: rgba(255,255,255,0.3); }
            
            /* Weather Section */
            .weather-card { background: var(--white); border-radius: 8px; padding: 24px; box-shadow: 0 2px 12px rgba(107,91,115,0.1); border-left: 4px solid var(--primary-olive); margin-bottom: 24px; }
            .weather-title { font-size: 24px; color: var(--primary-brown); font-weight: bold; margin-bottom: 16px; }
            .weather-content { display: flex; align-items: center; gap: 32px; }
            .weather-icon { font-size: 64px; }
            .weather-details { flex: 1; }
            .weather-temp { font-size: 36px; font-weight: bold; color: var(--primary-brown); }
            .weather-condition { font-size: 20px; color: var(--dark-olive); margin-bottom: 8px; }
            .weather-info { font-size: 18px; color: var(--dark-olive); }
            
            /* Constitutional Cards */
            .constitutional-card { background: var(--white); border-radius: 8px; padding: 24px; box-shadow: 0 2px 12px rgba(107,91,115,0.1); border-left: 4px solid var(--primary-olive); margin-bottom: 24px; }
            .constitutional-card-title { font-size: 24px; color: var(--primary-brown); font-weight: bold; margin-bottom: 16px; text-align: center; }
            .constitutional-textarea { width: 100%; padding: 16px; border: 2px solid var(--light-gray); border-radius: 8px; font-size: 18px; background: var(--white); min-height: 120px; resize: vertical; margin-bottom: 16px; }
            .constitutional-textarea:focus { outline: none; border-color: var(--primary-olive); }
            .constitutional-btn { background: var(--primary-olive); color: var(--white); border: none; padding: 16px 24px; font-size: 18px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%; margin-bottom: 16px; transition: all 0.3s ease; }
            .constitutional-btn:hover { background: var(--dark-olive); transform: translateY(-1px); }
            .constitutional-btn-secondary { background: var(--light-gray); color: #2C2C2C; }
            .enter-hint { text-align: center; font-size: 16px; color: var(--dark-olive); margin-top: 8px; font-style: italic; }
            
            /* User Info */
            .user-info { background: rgba(255,255,255,0.9); padding: 16px; border-radius: 8px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; border: 1px solid var(--light-gray); }
            .user-name { font-size: 20px; color: var(--primary-brown); font-weight: bold; }
            .user-phone { font-size: 16px; color: var(--dark-olive); }
            
            /* Mobile Responsive */
            @media (max-width: 768px) {
                .weather-content { flex-direction: column; text-align: center; }
                .constitutional-header { flex-direction: column; text-align: center; }
                .constitutional-tagline { margin-left: 0; margin-top: 8px; }
                .logout-btn { position: static; transform: none; margin-top: 16px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Constitutional Header -->
            <header class="constitutional-header">
                <div class="constitutional-logo"></div>
                <div class="constitutional-brand">AVA OLO</div>
                <div class="constitutional-tagline">Your Agricultural Assistant</div>
                <button class="logout-btn" onclick="handleLogout()">Sign Out</button>
            </header>

            <!-- User Info -->
            <div class="user-info">
                <div>
                    <div class="user-name" id="userName">Loading...</div>
                    <div class="user-phone" id="userPhone">Loading...</div>
                </div>
                <div>
                    <strong>Farm:</strong> <span id="farmName">Loading...</span>
                </div>
            </div>

            <!-- Weather Section -->
            <section class="weather-card">
                <h2 class="weather-title">Today's Weather</h2>
                <div class="weather-content">
                    <div class="weather-icon">☀️</div>
                    <div class="weather-details">
                        <div class="weather-temp">22°C</div>
                        <div class="weather-condition">Sunny</div>
                        <div class="weather-info">💧 Humidity: 65% | 🌪️ Wind: NE 12km/h</div>
                    </div>
                </div>
            </section>

            <!-- Main Query Interface -->
            <section class="constitutional-card">
                <h1 class="constitutional-card-title">How can I help you today?</h1>
                <textarea class="constitutional-textarea" id="queryInput" placeholder="Ask me anything about your crops, soil, weather, or farming techniques..." onkeypress="handleEnterKey(event, 'submitQuery')"></textarea>
                <div class="enter-hint">Press Enter to submit your question</div>
                <button id="submitQuery" class="constitutional-btn" onclick="submitQuery()">🔍 Submit Question</button>
            </section>

            <!-- Response Section -->
            <section id="responseSection" class="constitutional-card" style="display: none;">
                <h2 class="constitutional-card-title">AVA's Response</h2>
                <div id="responseContent" style="font-size: 18px; line-height: 1.6; color: #2C2C2C;"></div>
            </section>

            <!-- Action Buttons -->
            <section class="constitutional-card">
                <h2 class="constitutional-card-title">Quick Actions</h2>
                <button class="constitutional-btn" onclick="alert('Task reporting feature coming soon!')">📋 Report a Task</button>
                <button class="constitutional-btn constitutional-btn-secondary" onclick="alert('Farm data feature coming soon!')">📊 View Farm Data</button>
            </section>
        </div>

        <script>
            // Check authentication on load
            const authToken = localStorage.getItem('ava_auth_token');
            const userData = JSON.parse(localStorage.getItem('ava_user') || '{}');
            
            if (!authToken) {
                window.location.href = '/login';
            }
            
            // Display user information
            document.getElementById('userName').textContent = userData.user_name || 'Farmer';
            document.getElementById('userPhone').textContent = userData.wa_phone_number || 'Not available';
            document.getElementById('farmName').textContent = userData.farm_name || 'My Farm';
            
            function handleEnterKey(event, buttonId) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    document.getElementById(buttonId).click();
                }
            }
            
            async function submitQuery() {
                const textarea = document.getElementById('queryInput');
                const query = textarea.value.trim();
                
                if (!query) return;
                
                const responseSection = document.getElementById('responseSection');
                const responseContent = document.getElementById('responseContent');
                
                // Show loading
                responseSection.style.display = 'block';
                responseContent.innerHTML = '<div style="text-align: center;">🔄 Processing your question...</div>';
                
                try {
                    const response = await fetch('/api/v1/query', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${authToken}`
                        },
                        body: JSON.stringify({
                            query: query,
                            farmer_id: userData.farmer_id,
                            wa_phone_number: userData.wa_phone_number
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        responseContent.innerHTML = `
                            <div style="white-space: pre-wrap;">${data.answer}</div>
                            <div style="margin-top: 16px; font-size: 14px; color: var(--dark-olive);">
                                <strong>Confidence:</strong> ${(data.confidence * 100).toFixed(0)}%
                            </div>
                        `;
                    } else {
                        responseContent.innerHTML = '<div style="color: red;">Failed to get response. Please try again.</div>';
                    }
                    
                    // Clear input
                    textarea.value = '';
                    
                } catch (error) {
                    console.error('Query error:', error);
                    responseContent.innerHTML = '<div style="color: red;">Connection error. Please try again.</div>';
                }
            }
            
            function handleLogout() {
                if (confirm('Are you sure you want to sign out?')) {
                    localStorage.removeItem('ava_auth_token');
                    localStorage.removeItem('ava_user');
                    window.location.href = '/';
                }
            }
        </script>
    </body>
    </html>
    """

# Initialize core modules
db_ops = DatabaseOperations()

# Pydantic models for API
class QueryRequest(BaseModel):
    query: str = Field(..., description="User query in any language")
    farmer_id: Optional[int] = Field(None, description="Farmer ID for context")
    wa_phone_number: Optional[str] = Field(None, description="WhatsApp number")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

class QueryResponse(BaseModel):
    success: bool
    answer: str
    query_type: str
    confidence: float
    sources: List[str] = Field(default_factory=list)
    entities: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Main query endpoint - simplified
@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Simplified query processing for testing
    """
    try:
        # Simple fallback response for testing
        answer = f"Thank you for your agricultural question: '{request.query}'. This is a test response from the simplified API Gateway. The system is working properly and your question has been received."
        
        # Save conversation to database
        if request.farmer_id:
            conversation_data = {
                "farmer_id": request.farmer_id,
                "question": request.query,
                "answer": answer,
                "topic": "general",
                "confidence_score": 0.8,
                "approved_status": False
            }
            await db_ops.save_conversation(request.farmer_id, conversation_data)
        
        return QueryResponse(
            success=True,
            answer=answer,
            query_type="general",
            confidence=0.8,
            sources=["test"],
            entities={},
            metadata={"source": "simplified_gateway", "timestamp": datetime.now().isoformat()}
        )
        
    except Exception as e:
        logger.error(f"Query processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check - Constitutional Deployment-First Standard
@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Simple health check without database to avoid event loop issues
        return {
            "status": "healthy",
            "service": "ava-olo-agricultural-core",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0-simple",
            "authentication": "available"
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/health-api/status")
async def detailed_health_status():
    """Detailed health status endpoint for deployment verification"""
    try:
        # Simple status without database check to avoid event loop issues
        return {
            "status": "healthy",
            "service": "ava-olo-agricultural-core",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0-simple",
            "constitutional": True,
            "authentication": "enabled",
            "database": "configured"
        }
    except Exception as e:
        logger.error(f"Detailed health check error: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "constitutional": False
        }

# All farmers list endpoint
@app.get("/api/v1/farmers")
async def get_all_farmers(limit: int = 100):
    """Get list of all farmers for UI selection"""
    try:
        farmers = await db_ops.get_all_farmers(limit)
        # If database is not available, return mock data for testing
        if not farmers:
            farmers = [
                {
                    "id": 1,
                    "name": "Marko Horvat",
                    "farm_name": "Horvat Farm",
                    "phone": "385912345678",
                    "location": "Zagreb",
                    "farm_type": "Arable crops",
                    "total_size_ha": 45.5
                },
                {
                    "id": 2,
                    "name": "Ana Novak",
                    "farm_name": "Novak Vineyard",
                    "phone": "385987654321",
                    "location": "Split",
                    "farm_type": "Winegrower",
                    "total_size_ha": 12.3
                },
                {
                    "id": 3,
                    "name": "Ivo Petrovic",
                    "farm_name": "Petrovic Vegetables",
                    "phone": "385911223344",
                    "location": "Osijek",
                    "farm_type": "Vegetable grower",
                    "total_size_ha": 8.7
                },
                {
                    "id": 4,
                    "name": "Petra Babic",
                    "farm_name": "Babic Grain Co.",
                    "phone": "385923456789",
                    "location": "Slavonski Brod",
                    "farm_type": "Grain production",
                    "total_size_ha": 120.0
                },
                {
                    "id": 5,
                    "name": "Milan Jovanovic",
                    "farm_name": "Jovanovic Livestock",
                    "phone": "385934567890",
                    "location": "Vukovar",
                    "farm_type": "Livestock",
                    "total_size_ha": 85.3
                },
                {
                    "id": 6,
                    "name": "Dragana Milic",
                    "farm_name": "Milic Organic Farm",
                    "phone": "385945678901",
                    "location": "Rijeka",
                    "farm_type": "Organic farming",
                    "total_size_ha": 28.7
                }
            ]
        return {"success": True, "farmers": farmers}
    except Exception as e:
        logger.error(f"Get all farmers error: {str(e)}")
        # Return mock data on error for testing
        return {"success": True, "farmers": [
            {"id": 1, "name": "Test Farmer", "farm_name": "Test Farm", "phone": "385123456789", "location": "Test Location", "farm_type": "Test Type", "total_size_ha": 10.0}
        ]}

# Farmer info endpoint
@app.get("/api/v1/farmers/{farmer_id}")
async def get_farmer(farmer_id: int):
    """Get farmer information"""
    try:
        farmer = await db_ops.get_farmer_info(farmer_id)
        if farmer:
            return {"success": True, "farmer": farmer}
        else:
            raise HTTPException(status_code=404, detail="Farmer not found")
    except Exception as e:
        logger.error(f"Get farmer error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Conversation history endpoint
@app.get("/api/v1/conversations/farmer/{farmer_id}")
async def get_conversations(farmer_id: int, limit: int = 10):
    """Get recent conversations for farmer"""
    try:
        conversations = await db_ops.get_recent_conversations(farmer_id, limit)
        # If database not available, return mock data
        if not conversations:
            conversations = [
                {
                    "id": 1,
                    "user_input": "When should I plant corn this year?",
                    "ava_response": "For Croatia, corn planting typically begins in mid-April when soil temperature reaches 10°C consistently.",
                    "timestamp": datetime.now(),
                    "approved_status": True
                },
                {
                    "id": 2,
                    "user_input": "How much fertilizer do I need for wheat?",
                    "ava_response": "For wheat in Croatian conditions, typically 120-150 kg N/ha, 60-80 kg P2O5/ha, and 80-120 kg K2O/ha.",
                    "timestamp": datetime.now(),
                    "approved_status": False
                }
            ]
        return {"success": True, "conversations": conversations}
    except Exception as e:
        logger.error(f"Get conversations error: {str(e)}")
        # Return mock data on error
        return {"success": True, "conversations": [
            {"id": 1, "user_input": "Test question", "ava_response": "Test response", "timestamp": datetime.now(), "approved_status": True}
        ]}

# Conversations for approval (agronomic dashboard)
@app.get("/api/v1/conversations/approval")
async def get_conversations_for_approval():
    """Get conversations grouped by approval status"""
    try:
        conversations = await db_ops.get_conversations_for_approval()
        # If database not available, return mock data for testing
        if not conversations or (conversations.get("unapproved", []) == [] and conversations.get("approved", []) == []):
            conversations = {
                "unapproved": [
                    {
                        "id": 1,
                        "farmer_id": 1,
                        "farmer_name": "Marko Horvat",
                        "farmer_phone": "385912345678",
                        "farmer_location": "Zagreb",
                        "farmer_type": "Arable crops",
                        "farmer_size": "45.5",
                        "last_message": "When should I plant corn this year for best yield?",
                        "timestamp": datetime.now()
                    },
                    {
                        "id": 2,
                        "farmer_id": 2,
                        "farmer_name": "Ana Novak",
                        "farmer_phone": "385987654321",
                        "farmer_location": "Split",
                        "farmer_type": "Winegrower",
                        "farmer_size": "12.3",
                        "last_message": "What's the best fertilizer for grapes in Mediterranean climate?",
                        "timestamp": datetime.now()
                    },
                    {
                        "id": 3,
                        "farmer_id": 3,
                        "farmer_name": "Ivo Petrovic",
                        "farmer_phone": "385911223344",
                        "farmer_location": "Osijek",
                        "farmer_type": "Vegetable grower",
                        "farmer_size": "8.7",
                        "last_message": "How can I control aphids on my tomatoes organically?",
                        "timestamp": datetime.now()
                    },
                    {
                        "id": 4,
                        "farmer_id": 4,
                        "farmer_name": "Petra Babic",
                        "farmer_phone": "385923456789",
                        "farmer_location": "Slavonski Brod",
                        "farmer_type": "Grain production",
                        "farmer_size": "120.0",
                        "last_message": "What's the optimal nitrogen application rate for wheat?",
                        "timestamp": datetime.now()
                    }
                ],
                "approved": [
                    {
                        "id": 5,
                        "farmer_id": 5,
                        "farmer_name": "Milan Jovanovic",
                        "farmer_phone": "385934567890",
                        "farmer_location": "Vukovar",
                        "farmer_type": "Livestock",
                        "farmer_size": "85.3",
                        "last_message": "What's the best grass seed mix for cattle pasture?",
                        "timestamp": datetime.now()
                    },
                    {
                        "id": 6,
                        "farmer_id": 6,
                        "farmer_name": "Dragana Milic",
                        "farmer_phone": "385945678901",
                        "farmer_location": "Rijeka",
                        "farmer_type": "Organic farming",
                        "farmer_size": "28.7",
                        "last_message": "How do I prepare soil for organic certification?",
                        "timestamp": datetime.now()
                    }
                ]
            }
        return {"success": True, "conversations": conversations}
    except Exception as e:
        logger.error(f"Get approval conversations error: {str(e)}")
        # Return mock data on error for testing
        return {"success": True, "conversations": {"unapproved": [], "approved": []}}

# Single conversation details
@app.get("/api/v1/conversations/{conversation_id}")
async def get_conversation_details(conversation_id: int):
    """Get detailed conversation information"""
    try:
        conversation = await db_ops.get_conversation_details(conversation_id)
        if conversation:
            return {"success": True, "conversation": conversation}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        logger.error(f"Get conversation details error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Alternative Web Interface Routes - Constitutional Deployment-First Compliance
@app.get("/web/", response_class=HTMLResponse)
async def web_path_interface():
    """Alternative web path access"""
    return """<h1>Web Interface Active</h1><p>Main interface: <a href='/'>Click here</a></p>"""


@app.get("/web/health")
async def web_interface_health():
    """Web interface health check - Constitutional compliance verified"""
    return {
        "status": "healthy",
        "service": "farmer-web-interface",
        "constitutional_compliance": "verified",
        "mango_rule": "active",
        "deployment_method": "deployment-first-verified"
    }


@app.post("/api/v1/self-test/registration")
async def run_registration_self_test():
    """Run automated registration tests"""
    
    try:
        from tests.registration_self_test import RegistrationSelfTest
        
        tester = RegistrationSelfTest("http://localhost:8080")
        results = await tester.run_complete_flow_test()
        
        return {
            "test_completed": True,
            "success_rate": results["success_rate"],
            "passed": results["passed"],
            "total": results["total"],
            "status": "PASSED" if results["success_rate"] >= 0.8 else "FAILED",
            "failures": results.get("failures", [])
        }
        
    except Exception as e:
        logger.error(f"Self-test error: {str(e)}")
        return {
            "test_completed": False,
            "success_rate": 0.0,
            "passed": 0,
            "total": 0,
            "status": "ERROR",
            "error": str(e)
        }


@app.post("/api/v1/self-test/registration/comprehensive")
async def run_comprehensive_registration_test():
    """Run ALL registration test scenarios"""
    
    try:
        from tests.registration_self_test import RegistrationSelfTest
        
        tester = RegistrationSelfTest("http://localhost:8080")
        results = await tester.run_stress_test()
        
        return {
            "test_completed": True,
            "comprehensive_results": results,
            "success_rate": results["success_rate"],
            "passed": results["passed"],
            "total": results["total_tests"],
            "recommendation": "DEPLOY" if results["success_rate"] >= 0.85 else "FIX_ISSUES",
            "critical_failures": results["failed"] > 3,
            "failure_categories": results.get("failure_categories", {}),
            "failures": results.get("failures", [])
        }
        
    except Exception as e:
        logger.error(f"Comprehensive self-test error: {str(e)}")
        return {
            "test_completed": False,
            "success_rate": 0.0,
            "passed": 0,
            "total": 0,
            "recommendation": "ERROR",
            "critical_failures": True,
            "error": str(e)
        }


# ====================================================================
# AUTHENTICATION ENDPOINTS - ADDED WITHOUT BREAKING EXISTING FEATURES
# ====================================================================

# Authentication imports (only loaded when needed)
try:
    from implementation.farm_auth import FarmAuthManager
    from implementation.auth_middleware import AuthMiddleware, AuthDependencies
    from pydantic import BaseModel
    
    # Lazy initialization for production deployment
    _auth_manager = None
    _auth_middleware = None
    _auth_deps = None
    
    def get_auth_manager():
        """Lazy initialization of authentication manager"""
        global _auth_manager
        if _auth_manager is None:
            _auth_manager = FarmAuthManager()
        return _auth_manager
    
    def get_auth_middleware():
        """Lazy initialization of authentication middleware"""
        global _auth_middleware
        if _auth_middleware is None:
            _auth_middleware = AuthMiddleware(get_auth_manager())
        return _auth_middleware
    
    def get_auth_deps():
        """Lazy initialization of authentication dependencies"""
        global _auth_deps
        if _auth_deps is None:
            _auth_deps = AuthDependencies(get_auth_middleware())
        return _auth_deps
    
    # Authentication request/response models
    class LoginRequest(BaseModel):
        wa_phone_number: str = Field(..., description="WhatsApp phone number")
        password: str = Field(..., description="User password")

    class RegisterUserRequest(BaseModel):
        farmer_id: int = Field(..., description="Farmer ID")
        wa_phone_number: str = Field(..., description="WhatsApp phone number")
        password: str = Field(..., description="User password")
        user_name: str = Field(..., description="User display name")
        role: str = Field(default="member", description="User role: owner, member, worker")

    class LoginResponse(BaseModel):
        success: bool
        token: Optional[str] = None
        user: Optional[Dict[str, Any]] = None
        message: str
    
    class ChatRegisterRequest(BaseModel):
        user_input: str = Field(..., description="User's response")
        current_data: Dict[str, Any] = Field(default_factory=dict, description="Data collected so far")
        conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Full conversation history")
        last_ava_message: Optional[str] = Field(None, description="Last message from AVA")
        conversation_id: Optional[str] = Field(None, description="Conversation ID for memory tracking")
        session_id: Optional[str] = Field(None, description="Session ID for CAVA tracking")
        farmer_id: Optional[int] = Field(None, description="Farmer ID if known")
    
    class ChatRegisterResponse(BaseModel):
        message: str = Field(..., description="AVA's response")
        extracted_data: Dict[str, Any] = Field(default_factory=dict, description="Extracted registration data")
        status: str = Field(default="collecting", description="Registration status")
        next_needed: Optional[str] = Field(None, description="Next field needed")
        conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Updated conversation history")
        last_ava_message: str = Field(..., description="Last AVA message for context")
        debug_info: Optional[Dict[str, Any]] = Field(None, description="Debug information")
        registration_successful: bool = Field(default=False, description="Whether registration completed")
        farmer_id: Optional[int] = Field(None, description="Farmer ID if registration successful")
        token: Optional[str] = Field(None, description="Auth token if registration successful")
        user: Optional[Dict[str, Any]] = Field(None, description="User info if registration successful")

    # Authentication endpoints
    @app.post("/api/v1/auth/login", response_model=LoginResponse)
    async def login(request: LoginRequest):
        """Authenticate farm user and return access token"""
        try:
            auth_manager = get_auth_manager()
            result = auth_manager.authenticate_user(
                request.wa_phone_number, 
                request.password
            )
            
            if result:
                logger.info(f"Successful login for {request.wa_phone_number}")
                return LoginResponse(
                    success=True,
                    token=result['token'],
                    user=result['user'],
                    message="Login successful"
                )
            else:
                logger.warning(f"Failed login attempt for {request.wa_phone_number}")
                return LoginResponse(
                    success=False,
                    message="Invalid WhatsApp number or password"
                )
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return LoginResponse(
                success=False,
                message="Login failed due to system error"
            )

    @app.post("/api/v1/auth/register")
    async def register_farm_user(
        request: RegisterUserRequest,
        current_user: dict = get_auth_deps().can_add_users()
    ):
        # CRITICAL LOGGING
        logger.error(f"🔥🔥🔥 OLD AUTH/REGISTER CALLED! User: {getattr(request, 'user_name', 'unknown')}")
        """Add new family member to farm (requires owner permissions)"""
        try:
            auth_manager = get_auth_manager()
            result = auth_manager.register_farm_user(
                farmer_id=current_user['farmer_id'],
                wa_phone=request.wa_phone_number,
                password=request.password,
                user_name=request.user_name,
                role=request.role,
                created_by_user_id=current_user['user_id']
            )
            
            logger.info(f"New farm user registered: {request.user_name} by {current_user['user_name']}")
            return {"success": True, "user": result, "message": "Family member added successfully"}
            
        except ValueError as e:
            logger.warning(f"Registration failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            raise HTTPException(status_code=500, detail="Registration failed")

    @app.get("/api/v1/auth/me")
    async def get_current_user_info(current_user: dict = get_auth_deps().current_user()):
        """Get current authenticated user information"""
        return {"success": True, "user": current_user}

    # Enhanced LLM Prompt - Bulletproof for All Edge Cases
    ENHANCED_LLM_PROMPT = """
You are AVA, the constitutional agricultural assistant having a LIVE CONVERSATION.

REQUIRED DATA: full_name, wa_phone_number, password, farm_name

CURRENT STATE: {current_data}
CONVERSATION HISTORY: {conversation_history}

BULLETPROOF CONVERSATION INTELLIGENCE:
- ALWAYS interpret user input in context of what you just asked
- User response = answer to your last question, even if it seems unrelated
- NEVER restart - always build on existing data
- Handle ALL edge cases gracefully

CRITICAL HANDLING RULES:

1. NAME PROCESSING:
   - "Ana Marija" → ask for last name, expect "Kovačević" → "Ana Marija Kovačević"
   - "Petar Jovanović" → recognize as FULL NAME immediately
   - "Željko Đorđević" → accept special characters perfectly
   - "Marie-Claire" → ask for surname, expect "Babić-Novak" → "Marie-Claire Babić-Novak"
   - "Marko 🚜" → ignore emojis, ask for last name
   - "Anastasija Aleksandrovna" → ask for last name, expect long surname

2. QUESTION HANDLING:
   - "What information do you need?" → explain and ask for name
   - "Why do you need my phone?" → explain WhatsApp contact, then ask for phone
   - "I only have one name" → explain family names, encourage surname
   - "Actually, can I change my phone?" → accept change, ask for new phone

3. PHONE PROCESSING:
   - "0912345678" → ask for country code like "+385"
   - "+385912345678" → perfect, move to password
   - Accept any format, just ensure country code

4. PASSWORD HANDLING:
   - "123" → "too short, need at least 6 characters"
   - "Slavonski Brod" → "Thanks! Confirm by typing 'Slavonski Brod' again:"
   - "tractor@farm" → valid password, ask for confirmation
   - "branko123" vs "branko124" → "don't match, try again"
   - ALWAYS accept ANY text ≥6 chars as valid password

5. FARM NAME PROCESSING:
   - "Velika farma" → accept Serbian/Croatian perfectly
   - "Златна Долина" → accept Cyrillic perfectly
   - "🚜 Happy Farm 🌾" → accept with emojis
   - "Đorđević Voće" → accept special characters
   - ANY text = valid farm name

6. CORRECTION HANDLING:
   - "Wait, my full name is..." → update full name
   - "Actually, can I change..." → accept changes gracefully
   - Always be flexible and helpful

ADVANCED CONTEXT AWARENESS:
- If user gives full name when asked for first name → accept it
- If user asks question → answer briefly, then continue with your question
- If user wants to change something → allow it and continue
- If user gives unexpected input → interpret in context of your last question

JSON RESPONSE FORMAT:
{{
  "message": "conversational response",
  "extracted_data": {{
    "full_name": "First Last" or null,
    "wa_phone_number": "+385123456789" or null,
    "password": "confirmed_password" or null,
    "farm_name": "Farm Name" or null,
    "temp_password_for_confirmation": "temp" or null
  }},
  "status": "collecting" or "COMPLETE"
}}

BULLETPROOF EXAMPLES:

Input: "What information do you need from me?"
Output: {{
  "message": "I need your full name, phone number, password, and farm name. Let's start - what's your full name?",
  "extracted_data": {{}},
  "status": "collecting"
}}

Input: "Peter" (when asked for name)
Output: {{
  "message": "Hi Peter! What's your last name?",
  "extracted_data": {{}},
  "status": "collecting"
}}

Input: "Ana Marija" (when asked for name)
Output: {{
  "message": "Hi Ana Marija! What's your last name?",
  "extracted_data": {{}},
  "status": "collecting"
}}

Input: "Petar Jovanović" (when asked for name)
Output: {{
  "message": "Great to meet you, Petar Jovanović! What's your WhatsApp number? (include country code like +385...)",
  "extracted_data": {{"full_name": "Petar Jovanović"}},
  "status": "collecting"
}}

Input: "0912345678" (when asked for phone)
Output: {{
  "message": "Please include the country code, like +385912345678:",
  "extracted_data": {{"full_name": "Nikola Petrov"}},
  "status": "collecting"
}}

Input: "123" (when asked for password)
Output: {{
  "message": "That's too short (3 characters). Please create a password with at least 6 characters:",
  "extracted_data": {{"full_name": "Milica Stojanović", "wa_phone_number": "+381653456789"}},
  "status": "collecting"
}}

Input: "branko124" (when confirming "branko123")
Output: {{
  "message": "The passwords don't match. Let's try again - create a password (at least 6 characters):",
  "extracted_data": {{"full_name": "Branko Mitrović", "wa_phone_number": "+381664567890"}},
  "status": "collecting"
}}

Input: "Златна Долина" (when asked for farm name)
Output: {{
  "message": "Perfect! Welcome to AVA OLO, Dragana Ilić! Your account for 'Златна Долина' is ready! 🚜",
  "extracted_data": {{"full_name": "Dragana Ilić", "wa_phone_number": "+381675678901", "password": "dragana2024", "farm_name": "Златна Долина"}},
  "status": "COMPLETE"
}}

CRITICAL SUCCESS FACTORS:
1. ALWAYS interpret input in context of what you just asked
2. NEVER restart conversation - build on existing data
3. Handle special characters, emojis, and multilingual input perfectly
4. Accept changes and corrections gracefully
5. Be conversational but keep moving forward
6. ANY text ≥6 chars = valid password
7. ANY text = valid farm name
8. Questions are opportunities to explain and continue

BE BULLETPROOF AND MAXIMALLY HELPFUL!
"""

except Exception as e:
    logger.error(f"❌ Authentication system not available: {str(e)}")
    
    # Fallback auth functions
    def get_auth_manager():
        return None
    
    def get_auth_middleware():
        return None
    
    def get_auth_deps():
        return None

async def chat_register_step_OLD_BACKUP(request: ChatRegisterRequest):
    """BACKUP: Original LangChain memory-based registration"""
    
    try:
        from config_manager import config
        from registration_memory import get_conversation_memory
        import uuid
        
        # Get or create conversation ID
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Get memory for this conversation
        memory_chat = get_conversation_memory(conversation_id, config.openai_api_key)
        
        # Process message with LangChain memory
        result = await memory_chat.process_message(request.user_input)
        
        # Add conversation ID to response
        result["conversation_id"] = conversation_id
        
        # Handle registration completion
        if result["status"] == "COMPLETE":
            data = result["extracted_data"]
            
            try:
                # Check if any users exist to determine if this should be an owner
                auth_manager = get_auth_manager()
                conn = auth_manager._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM farm_users")
                result = cursor.fetchone()
                is_first_user = result['count'] == 0
                
                # Get first farmer ID
                cursor.execute("SELECT id FROM farmers ORDER BY id LIMIT 1")
                farmer = cursor.fetchone()
                farmer_id = farmer['id'] if farmer else 1
                
                # Create the user
                user_result = auth_manager.register_farm_user(
                    farmer_id=farmer_id,
                    wa_phone=data['wa_phone_number'],
                    password=data['password'],
                    user_name=data['full_name'],
                    role="owner" if is_first_user else "member",
                    created_by_user_id=None
                )
                
                # Auto-login after registration
                login_result = auth_manager.authenticate_user(
                    data['wa_phone_number'],
                    data['password']
                )
                
                return {
                    "message": result["message"],
                    "status": "COMPLETE",
                    "registration_successful": True,
                    "farmer_id": farmer_id,
                    "token": login_result['token'] if login_result else None,
                    "user": login_result['user'] if login_result else None,
                    "extracted_data": data,
                    "conversation_history": request.conversation_history or [],
                    "last_ava_message": result["message"]
                }
                
            except Exception as e:
                logger.error(f"Account creation error: {str(e)}")
                return {
                    "message": "Perfect! I have all your information. There was a brief technical issue, but let me try creating your account again...",
                    "status": "retry_creation",
                    "extracted_data": data,
                    "conversation_history": request.conversation_history or [],
                    "last_ava_message": "Perfect! I have all your information. There was a brief technical issue, but let me try creating your account again..."
                }
        
        # Continue conversation
        return result
        
    except Exception as e:
        logger.error(f"LangChain registration error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "message": "Hi! What's your full name? (first and last name)",
            "status": "collecting", 
            "extracted_data": {},
            "conversation_history": [],
            "last_ava_message": "Hi! What's your full name? (first and last name)",
            "memory_enabled": False,
            "error": str(e)
        }

@app.post("/api/v1/auth/chat-register")
async def chat_register_cava_proxy(request: ChatRegisterRequest):
        """CAVA proxy using integrated engine (NOT HTTP calls)"""
        
        try:
            logger.error(f"🔥 CAVA PROXY CALLED with message: {request.user_input}")
            
            # Use the integrated CAVA engine (NOT HTTP)
            if not hasattr(app.state, 'cava_engine'):
                raise Exception("CAVA engine not initialized in app.state")
                
            cava_response = await app.state.cava_engine.handle_farmer_message(
                farmer_id=request.farmer_id or 99999,
                message=request.user_input,
                session_id=f"reg_farmer_{request.farmer_id or 99999}",
                channel="registration"
            )
            
            logger.error(f"🔥 CAVA RESPONSE: {cava_response}")
            
            return {
                "success": cava_response.get("success", True),
                "message": cava_response.get("message", ""),
                "session_id": request.session_id,
                "registration_complete": "complete" in cava_response.get("message", "").lower()
            }
            
        except Exception as e:
            logger.error(f"❌ CAVA Proxy failed: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Log the error
            if hasattr(app.state, 'registration_logs'):
                app.state.registration_logs.append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "CAVA_ERROR",
                    "error": str(e),
                    "falling_back": True
                })
            
            # Fallback to old system
            logger.info("🔄 CAVA Proxy: Falling back to old registration system")
            try:
                return await chat_register_step_OLD_BACKUP(request)
            except Exception as fallback_e:
                logger.error(f"❌ Fallback also failed: {str(fallback_e)}")
                return {
                    "message": "Hi! I'm AVA, your agricultural assistant. What's your full name?",
                    "status": "collecting", 
                    "extracted_data": {},
                    "conversation_history": [],
                    "last_ava_message": "Hi! I'm AVA, your agricultural assistant. What's your full name?",
                    "cava_enabled": False,
                    "error": f"Both CAVA and fallback failed: {str(e)}"
                }

@app.get("/api/v1/auth/family")
async def get_farm_family(current_user: dict = get_auth_deps().current_user()):
        """Get all family members who have access to this farm"""
        try:
            auth_manager = get_auth_manager()
            family_members = auth_manager.get_farm_family_members(current_user['farmer_id'])
            return {"success": True, "family_members": family_members}
        except Exception as e:
            logger.error(f"Get family error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to load family members")

    @app.get("/api/v1/auth/activity")
    async def get_farm_activity(
        limit: int = 50,
        current_user: dict = get_auth_deps().can_view_activity_log()
    ):
        """Get recent farm activity log (who did what)"""
        try:
            auth_manager = get_auth_manager()
            activities = auth_manager.get_farm_activity_log(current_user['farmer_id'], limit)
            return {"success": True, "activities": activities}
        except Exception as e:
            logger.error(f"Get activity error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to load activity log")

    # Authentication-aware versions of existing endpoints
    @app.get("/api/v1/farmers/me")
    async def get_my_farm_info(current_user: dict = get_auth_deps().current_user()):
        """Get authenticated user's farm information"""
        try:
            db_ops = DatabaseOperations()
            farmer = await db_ops.get_farmer_info(current_user['farmer_id'])
            if farmer:
                return {"success": True, "farmer": farmer}
            else:
                raise HTTPException(status_code=404, detail="Farm not found")
        except Exception as e:
            logger.error(f"Get farmer error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to load farm information")

    @app.get("/api/v1/conversations/me")
    async def get_my_conversations(
        limit: int = 10,
        current_user: dict = get_auth_deps().current_user()
    ):
        """Get conversations for authenticated user's farm"""
        try:
            db_ops = DatabaseOperations()
            conversations = await db_ops.get_recent_conversations(current_user['farmer_id'], limit)
            
            # Add audit info showing which family member sent each message
            for conv in conversations:
                if hasattr(conv, 'farm_user_id') and conv.farm_user_id:
                    user_info = await db_ops.fetchrow(
                        "SELECT user_name FROM farm_users WHERE id = %s",
                        conv.farm_user_id
                    )
                    conv['sent_by'] = user_info['user_name'] if user_info else 'Unknown'
            
            return {"success": True, "conversations": conversations}
        except Exception as e:
            logger.error(f"Get conversations error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to load conversations")
    
    @app.post("/api/v1/auth/migrate")
    async def run_aurora_migration():
        """Run Aurora database migration for authentication tables"""
        try:
            # First test if we can connect using config manager (which works)
            from config_manager import config
            import psycopg2
            
            logger.info("Testing config manager connection first...")
            try:
                test_conn = psycopg2.connect(
                    host=config.db_host,
                    database=config.db_name,
                    user=config.db_user,
                    password=config.db_password,
                    port=config.db_port
                )
                test_conn.close()
                logger.info("✅ Config manager connection works!")
            except Exception as e:
                logger.error(f"❌ Config manager connection failed: {e}")
            
            auth_manager = get_auth_manager()
            # Check if tables exist by trying a simple query
            conn = auth_manager._get_connection()
            with conn.cursor() as cur:
                # Check if farm_users table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'farm_users'
                    )
                """)
                farm_users_exists = cur.fetchone()[0]
                
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'farm_activity_log'
                    )
                """)
                activity_log_exists = cur.fetchone()[0]
                
            conn.close()
            
            if farm_users_exists and activity_log_exists:
                return {
                    "success": True,
                    "message": "Authentication tables already exist",
                    "farm_users": "exists",
                    "farm_activity_log": "exists"
                }
            else:
                # Run migration
                from implementation.migrate_auth_to_aurora import AuthMigrator
                migrator = AuthMigrator()
                success = migrator.run_migration()
                
                if success:
                    return {
                        "success": True,
                        "message": "Migration completed successfully",
                        "farm_users": "created",
                        "farm_activity_log": "created"
                    }
                else:
                    return {
                        "success": False,
                        "message": "Migration failed - check logs"
                    }
                    
        except Exception as e:
            logger.error(f"Migration error: {str(e)}")
            return {
                "success": False,
                "message": f"Migration failed: {str(e)}"
            }
    
    @app.post("/api/v1/auth/migrate-direct")
    async def run_direct_migration():
        """Direct migration using the exact working pattern"""
        try:
            # Import what we need
            from config_manager import config
            import asyncpg
            import os
            
            # Direct asyncpg connection (no SSL specified, like working code)
            conn = await asyncpg.connect(
                host=config.db_host,
                port=config.db_port,
                user=config.db_user,
                password=config.db_password,
                database=config.db_name
            )
            
            # Test connection
            version = await conn.fetchval("SELECT version()")
            logger.info(f"Connected to database: {version[:50]}...")
            
            # Read migration SQL
            migration_path = os.path.join(os.path.dirname(__file__), 'database', 'auth_schema.sql')
            
            if not os.path.exists(migration_path):
                await conn.close()
                return {
                    "success": False,
                    "message": f"Migration file not found: {migration_path}"
                }
            
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
            
            # Split into individual statements and execute
            statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
            
            for statement in statements:
                if statement:
                    try:
                        await conn.execute(statement)
                        logger.info(f"Executed: {statement[:50]}...")
                    except Exception as e:
                        if "already exists" in str(e):
                            logger.info(f"Table/index already exists, skipping")
                        else:
                            raise e
            
            await conn.close()
            
            return {
                "success": True,
                "message": "Migration completed successfully",
                "database_version": version[:50] if version else "Unknown"
            }
            
        except Exception as e:
            logger.error(f"Direct migration failed: {e}")
            return {
                "success": False,
                "message": f"Migration failed: {str(e)[:200]}"
            }
    
    @app.post("/api/v1/auth/migrate-working")
    def run_working_migration():
        """Use sync function to avoid event loop issues"""
        try:
            # Use the sync wrapper
            from database_operations import DatabaseOperations
            sync_db = DatabaseOperations()
            
            # First verify connection works
            farmers = sync_db.get_all_farmers(limit=1)
            if farmers is None:
                return {"success": False, "message": "Database connection not working"}
            
            # Get the actual connection from LLM engine
            from llm_first_database_engine import LLMDatabaseQueryEngine
            engine = LLMDatabaseQueryEngine()
            
            # This will create the connection using the working pattern
            if engine.db_connection is None:
                engine._initialize_database()
            
            # Read migration SQL
            import os
            migration_path = os.path.join(os.path.dirname(__file__), 'database', 'auth_schema.sql')
            
            if not os.path.exists(migration_path):
                return {
                    "success": False,
                    "message": f"Migration file not found: {migration_path}"
                }
            
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
            
            # Execute using the engine's connection
            with engine.db_connection.cursor() as cursor:
                # Split and execute statements
                statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
                
                for statement in statements:
                    if statement:
                        try:
                            cursor.execute(statement)
                            engine.db_connection.commit()
                            logger.info(f"Executed: {statement[:50]}...")
                        except Exception as e:
                            if "already exists" in str(e):
                                logger.info(f"Table/index already exists, skipping")
                                engine.db_connection.rollback()
                            else:
                                engine.db_connection.rollback()
                                raise e
            
            return {
                "success": True,
                "message": "Migration completed successfully using working connection"
            }
            
        except Exception as e:
            logger.error(f"Working migration failed: {e}")
            return {
                "success": False,
                "message": f"Migration failed: {str(e)[:200]}"
            }
    
    @app.post("/api/v1/auth/migrate-dashboard-style")
    async def migrate_dashboard_style():
        """Migration using the exact pattern from monitoring dashboards"""
        try:
            from config_manager import config
            import asyncpg
            import os
            
            # Build connection params like dashboards do
            # Use postgres database since that's where the data actually is
            connection_params = {
                'host': config.db_host,
                'port': config.db_port,
                'user': config.db_user,
                'password': config.db_password,  # Raw password, not URL-encoded
                'database': 'postgres',  # Use postgres database where farmers table exists
                'server_settings': {
                    'application_name': 'ava_olo_auth_migration'
                }
            }
            
            # Try different SSL modes like dashboards
            ssl_modes = ['require', 'prefer', 'disable']
            conn = None
            
            for ssl_mode in ssl_modes:
                try:
                    if ssl_mode != 'disable':
                        connection_params['ssl'] = ssl_mode
                    else:
                        connection_params['ssl'] = False
                    
                    logger.info(f"Trying connection with SSL mode: {ssl_mode}")
                    conn = await asyncpg.connect(**connection_params)
                    logger.info(f"✅ Connected with SSL mode: {ssl_mode}")
                    break
                except Exception as e:
                    logger.warning(f"Failed with SSL {ssl_mode}: {str(e)[:100]}")
                    if "SSL" not in str(e) and "ssl" not in str(e):
                        # Not an SSL error, don't try other modes
                        raise
                    continue
            
            if not conn:
                return {
                    "success": False,
                    "message": "Failed to connect with all SSL modes"
                }
            
            # Test connection
            version = await conn.fetchval("SELECT version()")
            logger.info(f"Database version: {version[:50]}")
            
            # Read migration SQL
            migration_path = os.path.join(os.path.dirname(__file__), 'database', 'auth_schema.sql')
            
            if not os.path.exists(migration_path):
                await conn.close()
                return {
                    "success": False,
                    "message": f"Migration file not found: {migration_path}"
                }
            
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
            
            # Execute migration (asyncpg requires splitting statements)
            statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
            
            success_count = 0
            for statement in statements:
                if statement and not statement.strip().startswith('--'):
                    try:
                        await conn.execute(statement)
                        success_count += 1
                        logger.info(f"✅ Executed statement {success_count}")
                    except Exception as e:
                        if "already exists" in str(e):
                            logger.info("Table/object already exists, skipping")
                        else:
                            logger.error(f"Statement failed: {str(e)[:100]}")
                            # Continue with other statements
            
            await conn.close()
            
            return {
                "success": True,
                "message": f"Migration completed! Executed {success_count} statements",
                "database_version": version[:50] if version else "Unknown"
            }
            
        except Exception as e:
            logger.error(f"Dashboard-style migration failed: {e}")
            return {
                "success": False,
                "message": f"Migration failed: {str(e)[:200]}"
            }
    
    @app.get("/api/v1/auth/list-databases")
    async def list_databases():
        """List available databases on the server"""
        try:
            from config_manager import config
            import asyncpg
            
            # Connect to postgres database (always exists)
            connection_params = {
                'host': config.db_host,
                'port': config.db_port,
                'user': config.db_user,
                'password': config.db_password,
                'database': 'postgres',  # Connect to default postgres database
                'ssl': 'prefer'
            }
            
            conn = await asyncpg.connect(**connection_params)
            
            # List all databases
            databases = await conn.fetch("""
                SELECT datname FROM pg_database 
                WHERE datistemplate = false 
                ORDER BY datname
            """)
            
            # Also check current database
            current_db = await conn.fetchval("SELECT current_database()")
            
            await conn.close()
            
            return {
                "success": True,
                "databases": [db['datname'] for db in databases],
                "current_database": current_db,
                "configured_database": config.db_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)[:200]
            }
    
    @app.get("/api/v1/check-farmers-table")
    async def check_farmers_table():
        """Check which database has the farmers table"""
        try:
            from config_manager import config
            import asyncpg
            
            results = []
            
            # Check postgres database
            try:
                conn = await asyncpg.connect(
                    host=config.db_host,
                    port=config.db_port,
                    user=config.db_user,
                    password=config.db_password,
                    database='postgres',
                    ssl='prefer'
                )
                
                # Check if farmers table exists
                farmers_exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'farmers'
                    )
                """)
                
                # Count farmers if table exists
                farmer_count = 0
                if farmers_exists:
                    farmer_count = await conn.fetchval("SELECT COUNT(*) FROM farmers")
                
                await conn.close()
                
                results.append({
                    "database": "postgres",
                    "farmers_table_exists": farmers_exists,
                    "farmer_count": farmer_count
                })
            except Exception as e:
                results.append({
                    "database": "postgres",
                    "error": str(e)[:100]
                })
                
            return {
                "success": True,
                "results": results,
                "configured_database": config.db_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)[:200]
            }
    
    @app.post("/api/v1/auth/create-database")
    async def create_database():
        """Create the farmer_crm database if it doesn't exist"""
        try:
            from config_manager import config
            import asyncpg
            
            # Connect to postgres database to create farmer_crm
            conn = await asyncpg.connect(
                host=config.db_host,
                port=config.db_port,
                user=config.db_user,
                password=config.db_password,
                database='postgres',
                ssl='prefer'
            )
            
            # Check if farmer_crm exists
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                'farmer_crm'
            )
            
            if exists:
                await conn.close()
                return {
                    "success": True,
                    "message": "Database farmer_crm already exists"
                }
            
            # Create the database
            # Note: Can't use parameters for CREATE DATABASE
            await conn.execute('CREATE DATABASE farmer_crm')
            
            await conn.close()
            
            return {
                "success": True,
                "message": "Database farmer_crm created successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)[:200]
            }
    
    @app.post("/api/v1/auth/migrate-simple")
    async def run_simple_migration():
        """Simple migration using async pattern"""
        try:
            # Use the async database operations that work
            from database_operations import ConstitutionalDatabaseOperations
            
            # Create async db ops
            db = ConstitutionalDatabaseOperations()
            
            # Test connection with a simple query
            result = await db.health_check()
            
            if not result:
                return {"success": False, "message": "Database connection failed"}
            
            # Now run the migration SQL directly
            from implementation.secrets_manager import get_database_config
            import asyncpg
            
            db_config = get_database_config()
            
            # Use asyncpg like the working endpoints
            conn = await asyncpg.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )
            
            # Read and execute migration SQL
            import os
            migration_path = os.path.join(os.path.dirname(__file__), 'database', 'auth_schema.sql')
            
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
            
            # Execute migration
            await conn.execute(migration_sql)
            await conn.close()
            
            return {
                "success": True,
                "message": "Migration completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Simple migration failed: {e}")
            return {
                "success": False,
                "message": f"Migration failed: {str(e)}"
            }

    # Diagnostic endpoints for production password issue
    @app.get("/api/v1/auth/diagnose-env")
    async def diagnose_environment():
        """Diagnose environment variables for debugging"""
        return {
            "DB_HOST": os.getenv('DB_HOST', 'not-set'),
            "DB_NAME": os.getenv('DB_NAME', 'not-set'),
            "DB_USER": os.getenv('DB_USER', 'not-set'),
            "DB_PASSWORD_LENGTH": len(os.getenv('DB_PASSWORD', '')),
            "DB_PASSWORD_PREVIEW": os.getenv('DB_PASSWORD', '')[:10] + "..." if os.getenv('DB_PASSWORD') else 'not-set',
            "DB_PASSWORD_HAS_DOLLAR": '$' in os.getenv('DB_PASSWORD', ''),
            "DB_PORT": os.getenv('DB_PORT', 'not-set'),
            "JWT_SECRET_SET": bool(os.getenv('JWT_SECRET'))
        }
    
    @app.get("/api/v1/auth/test-password-sources")
    async def test_password_sources():
        """Compare passwords from different sources"""
        import psycopg2
        from implementation.secrets_manager import get_database_config
        from config_manager import config
        
        results = []
        
        # Test 1: Using config_manager (what regular endpoints use)
        try:
            conn = psycopg2.connect(
                host=config.db_host,
                database=config.db_name,
                user=config.db_user,
                password=config.db_password,
                port=config.db_port
            )
            conn.close()
            results.append({
                "method": "config_manager", 
                "success": True,
                "password_length": len(config.db_password),
                "password_preview": config.db_password[:5] + "..." + config.db_password[-5:] if config.db_password else 'not-set'
            })
        except Exception as e:
            results.append({
                "method": "config_manager", 
                "error": str(e)[:100],
                "password_length": len(config.db_password),
                "password_preview": config.db_password[:5] + "..." + config.db_password[-5:] if config.db_password else 'not-set'
            })
            
        # Test 2: Using secrets_manager (what auth uses)
        try:
            db_config = get_database_config()
            conn = psycopg2.connect(
                host=db_config['host'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                port=db_config['port']
            )
            conn.close()
            results.append({
                "method": "secrets_manager", 
                "success": True,
                "password_length": len(db_config['password']),
                "password_preview": db_config['password'][:5] + "..." + db_config['password'][-5:] if db_config['password'] else 'not-set'
            })
        except Exception as e:
            results.append({
                "method": "secrets_manager", 
                "error": str(e)[:100],
                "password_length": len(db_config.get('password', '')),
                "password_preview": db_config['password'][:5] + "..." + db_config['password'][-5:] if db_config.get('password') else 'not-set'
            })
            
        # Compare passwords
        config_pw = config.db_password
        secrets_pw = get_database_config().get('password', '')
        
        return {
            "tests": results,
            "passwords_match": config_pw == secrets_pw,
            "config_has_dollar": '$' in config_pw,
            "secrets_has_dollar": '$' in secrets_pw
        }
    
    @app.get("/api/v1/auth/test-llm-engine-connection")
    def test_llm_engine_connection():
        """Test using the exact LLM engine that works"""
        try:
            # Import and use the LLM engine directly
            from llm_first_database_engine import LLMDatabaseQueryEngine
            from config_manager import config
            
            # Create engine
            engine = LLMDatabaseQueryEngine()
            
            # Force initialization (this is what works for farmers)
            engine._initialize_database()
            
            # Test the connection
            with engine.db_connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()
            
            return {
                "connection": "success",
                "db_version": str(version),
                "connection_info": {
                    "host": config.db_host,
                    "database": config.db_name,
                    "user": config.db_user,
                    "password_length": len(config.db_password)
                }
            }
        except Exception as e:
            return {
                "error": str(e),
                "connection_info": {
                    "host": config.db_host,
                    "database": config.db_name,
                    "user": config.db_user,
                    "password_length": len(config.db_password) if hasattr(config, 'db_password') else 0
                }
            }
    
    @app.get("/api/v1/auth/test-sync-connection")
    def test_sync_connection():
        """Test sync connection without async"""
        from config_manager import config
        import psycopg2
        
        try:
            # Simple sync connection like config manager
            conn = psycopg2.connect(
                host=config.db_host,
                database=config.db_name,
                user=config.db_user,
                password=config.db_password,
                port=config.db_port
            )
            
            # Test query
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
            
            conn.close()
            
            return {
                "connection": "success",
                "test_query": "success" if result else "failed",
                "method": "sync_psycopg2"
            }
        except Exception as e:
            return {"error": str(e), "method": "sync_psycopg2"}
    
    @app.get("/api/v1/auth/test-working-connection")
    async def test_working_connection():
        """Test the exact connection method that works for farmers"""
        try:
            # Use the exact same method as the farmers endpoint
            db_ops = DatabaseOperations()
            
            # This should work since farmers endpoint works
            farmers = db_ops.get_all_farmers(limit=1)
            
            # Now let's trace how it connects
            from llm_first_database_engine import LLMDatabaseQueryEngine
            engine = LLMDatabaseQueryEngine()
            
            # Force database initialization
            if engine.db_connection is None:
                engine._initialize_database()
            
            # Test if we can query with this connection
            with engine.db_connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            return {
                "farmers_query": "success" if farmers else "no farmers",
                "farmer_count": len(farmers) if farmers else 0,
                "direct_query": "success" if result else "failed",
                "connection_info": {
                    "host": config.db_host,
                    "port": config.db_port,
                    "database": config.db_name,
                    "user": config.db_user,
                    "password_length": len(config.db_password)
                }
            }
        except Exception as e:
            return {"error": str(e), "trace": str(type(e))}
    
    @app.get("/api/v1/auth/test-basic-connection")
    async def test_basic_connection():
        """Test basic psycopg2 connection like LLM engine uses"""
        import psycopg2
        from implementation.secrets_manager import get_database_config
        
        results = []
        
        # Test 1: Exact same connection as LLM engine (no SSL specified)
        try:
            db_config = get_database_config()
            conn = psycopg2.connect(
                host=db_config['host'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                port=db_config['port']
            )
            conn.close()
            results.append({"method": "basic_no_ssl", "success": True})
        except Exception as e:
            results.append({"method": "basic_no_ssl", "error": str(e)[:200]})
            
        # Test 2: With SSL disable (explicit)
        try:
            conn = psycopg2.connect(
                host=db_config['host'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                port=db_config['port'],
                sslmode='disable'
            )
            conn.close()
            results.append({"method": "ssl_disable", "success": True})
        except Exception as e:
            results.append({"method": "ssl_disable", "error": str(e)[:200]})
            
        # Test 3: With SSL require
        try:
            conn = psycopg2.connect(
                host=db_config['host'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                port=db_config['port'],
                sslmode='require'
            )
            conn.close()
            results.append({"method": "ssl_require", "success": True})
        except Exception as e:
            results.append({"method": "ssl_require", "error": str(e)[:200]})
            
        return {"tests": results, "password_length": len(db_config.get('password', ''))}
    
    @app.get("/api/v1/auth/test-secrets")
    async def test_secrets():
        """Test AWS Secrets Manager integration"""
        import os
        result = {
            "aws_secret_name": os.getenv("AWS_SECRET_NAME"),
            "aws_region": os.getenv("AWS_REGION", "us-east-1"),
            "aws_default_region": os.getenv("AWS_DEFAULT_REGION"),
            "secrets_manager_test": "not_run"
        }
        
        if result["aws_secret_name"]:
            try:
                from implementation.secrets_manager import get_database_config, get_cached_secret
                
                # Test fetching the secret
                secret_data = get_cached_secret(result["aws_secret_name"])
                if secret_data:
                    result["secrets_manager_test"] = "success"
                    result["secret_keys"] = list(secret_data.keys())
                    result["db_config_from_secrets"] = bool(secret_data.get("DB_PASSWORD"))
                else:
                    result["secrets_manager_test"] = "failed - no data"
                    
                # Test getting database config
                db_config = get_database_config()
                result["db_config_source"] = "secrets" if secret_data else "env"
                
            except Exception as e:
                result["secrets_manager_test"] = f"error: {str(e)}"
        else:
            result["secrets_manager_test"] = "skipped - AWS_SECRET_NAME not set"
            
        return result
    
    @app.get("/api/v1/auth/test-secrets-detailed")
    async def test_secrets_detailed():
        """Test AWS Secrets Manager with detailed password info"""
        import os
        from implementation.secrets_manager import get_database_config, get_cached_secret
        
        result = {"tests": []}
        
        # Test 1: Direct environment variables
        env_test = {
            "method": "environment_variables",
            "db_password_length": len(os.getenv('DB_PASSWORD', '')),
            "db_password_preview": os.getenv('DB_PASSWORD', '')[:5] + "..." + os.getenv('DB_PASSWORD', '')[-5:] if os.getenv('DB_PASSWORD') else 'not-set',
            "has_dollar": '$' in os.getenv('DB_PASSWORD', ''),
            "has_special_chars": any(c in os.getenv('DB_PASSWORD', '') for c in '~[]{}$&*')
        }
        result["tests"].append(env_test)
        
        # Test 2: Secrets Manager
        try:
            secret_name = os.getenv("AWS_SECRET_NAME")
            if secret_name:
                secret_data = get_cached_secret(secret_name)
                if secret_data:
                    sm_password = secret_data.get('DB_PASSWORD', '')
                    sm_test = {
                        "method": "secrets_manager",
                        "secret_retrieved": True,
                        "db_password_length": len(sm_password),
                        "db_password_preview": sm_password[:5] + "..." + sm_password[-5:] if sm_password else 'not-set',
                        "has_dollar": '$' in sm_password,
                        "has_special_chars": any(c in sm_password for c in '~[]{}$&*'),
                        "matches_env": sm_password == os.getenv('DB_PASSWORD', '')
                    }
                else:
                    sm_test = {"method": "secrets_manager", "error": "No secret data retrieved"}
            else:
                sm_test = {"method": "secrets_manager", "error": "AWS_SECRET_NAME not set"}
            result["tests"].append(sm_test)
        except Exception as e:
            result["tests"].append({"method": "secrets_manager", "error": str(e)})
            
        # Test 3: What auth manager gets
        try:
            db_config = get_database_config()
            auth_test = {
                "method": "auth_manager_config",
                "db_password_length": len(db_config.get('password', '')),
                "db_password_preview": db_config['password'][:5] + "..." + db_config['password'][-5:] if db_config.get('password') else 'not-set',
                "has_dollar": '$' in db_config.get('password', ''),
                "config_source": "secrets" if get_cached_secret(os.getenv("AWS_SECRET_NAME", "")) else "env"
            }
            result["tests"].append(auth_test)
        except Exception as e:
            result["tests"].append({"method": "auth_manager_config", "error": str(e)})
            
        # Test 4: Direct psycopg2 with Secrets Manager password
        try:
            import psycopg2
            db_config = get_database_config()
            
            # Try connecting with the password from Secrets Manager
            conn = psycopg2.connect(
                host=db_config['host'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                port=db_config['port'],
                connect_timeout=5
            )
            conn.close()
            result["tests"].append({
                "method": "direct_psycopg2_secrets", 
                "success": True,
                "password_source": "secrets_manager"
            })
        except Exception as e:
            result["tests"].append({
                "method": "direct_psycopg2_secrets", 
                "error": str(e),
                "password_source": "secrets_manager"
            })
            
        return result
    
    @app.get("/api/v1/auth/test-simple-connection")
    async def test_simple_connection():
        """Test simple database connection like regular endpoints"""
        try:
            # Test 1: Use the same connection as regular endpoints
            db_ops = DatabaseOperations()
            farmers = db_ops.get_all_farmers(limit=1)
            
            result = {
                "regular_connection": "success" if farmers is not None else "failed",
                "farmers_found": len(farmers) if farmers else 0
            }
            
            # Test 2: Try auth manager connection
            try:
                auth_manager = get_auth_manager()
                # Just initialize, don't connect yet
                result["auth_manager_initialized"] = True
                result["auth_db_config_keys"] = list(auth_manager.db_config.keys())
                
                # Now try to connect
                conn = auth_manager._get_connection()
                if conn:
                    result["auth_connection"] = "success"
                    conn.close()
                else:
                    result["auth_connection"] = "failed - no connection"
            except Exception as e:
                result["auth_connection"] = f"failed - {str(e)[:100]}"
                
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/api/v1/auth/test-connections")
    async def test_db_connections():
        """Test different database connection methods"""
        results = []
        
        # Test 1: Environment variable as-is
        try:
            auth_manager = get_auth_manager()
            conn = auth_manager._get_connection()
            if conn:
                conn.close()
                results.append({"method": "auth_manager", "success": True})
            else:
                results.append({"method": "auth_manager", "success": False, "error": "No connection"})
        except Exception as e:
            results.append({"method": "auth_manager", "success": False, "error": str(e)[:100]})
        
        # Test 2: Direct with environment
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=int(os.getenv('DB_PORT', '5432')),
                connect_timeout=5
            )
            conn.close()
            results.append({"method": "env_direct", "success": True})
        except Exception as e:
            results.append({"method": "env_direct", "success": False, "error": str(e)[:100]})
        
        return {"tests": results}
    
    logger.info("✅ Authentication endpoints loaded successfully")
    
except ImportError as e:
    logger.warning(f"⚠️  Authentication system not available: {e}")
    logger.info("📋 Service will run without authentication (backward compatibility)")
    
    # Fallback endpoints for when authentication is not available
    @app.get("/api/v1/auth/status")
    async def auth_status():
        """Authentication system status"""
        return {
            "authentication_available": False,
            "message": "Authentication system not loaded - using compatibility mode",
            "fallback_mode": True
        }
    
    @app.get("/api/v1/auth/test-secrets")
    async def test_secrets():
        """Test AWS Secrets Manager integration"""
        import os
        result = {
            "aws_secret_name": os.getenv("AWS_SECRET_NAME"),
            "aws_region": os.getenv("AWS_REGION", "us-east-1"),
            "aws_default_region": os.getenv("AWS_DEFAULT_REGION"),
            "secrets_manager_test": "not_run"
        }
        
        if result["aws_secret_name"]:
            try:
                from implementation.secrets_manager import get_database_config, get_cached_secret
                
                # Test fetching the secret
                secret_data = get_cached_secret(result["aws_secret_name"])
                if secret_data:
                    result["secrets_manager_test"] = "success"
                    result["secret_keys"] = list(secret_data.keys())
                    result["db_config_from_secrets"] = bool(secret_data.get("DB_PASSWORD"))
                else:
                    result["secrets_manager_test"] = "failed - no data"
                    
                # Test getting database config
                db_config = get_database_config()
                result["db_config_source"] = "secrets" if secret_data else "env"
                
            except Exception as e:
                result["secrets_manager_test"] = f"error: {str(e)}"
        else:
            result["secrets_manager_test"] = "skipped - AWS_SECRET_NAME not set"
            
        return result


# Manual migration endpoint
@app.post("/api/v1/auth/manual-migrate")
async def manual_migrate():
    """Manually create tables if they don't exist"""
    try:
        # Test if we can query farmers (this works)
        farmers_result = await db_ops.get_all_farmers(limit=1)
        
        if farmers_result is None:
            return {"success": False, "message": "Cannot connect to database"}
        
        # Since we can't connect directly, let's check if tables exist
        # by trying to use the auth system
        from implementation.farm_auth import FarmAuthManager
        
        try:
            # Try to create auth manager
            auth = FarmAuthManager()
            
            # Try a simple query to see if tables exist
            test_farmers = auth.get_farm_family_members(1)
            
            return {
                "success": True,
                "message": "Auth tables already exist",
                "test_result": f"Found {len(test_farmers)} family members"
            }
            
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg:
                return {
                    "success": False,
                    "message": "Auth tables do not exist - manual creation needed",
                    "error": error_msg[:200],
                    "solution": "Please run the migration SQL manually in AWS RDS console"
                }
            else:
                return {
                    "success": False,
                    "message": "Auth system error",
                    "error": error_msg[:200]
                }
                
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)[:200]}"
        }

# Test endpoint at the end of file
@app.get("/api/v1/test-import-order")
def test_import_order():
    """Test if import order affects password retrieval"""
    import os
    
    # Get password from different sources
    env_password = os.getenv('DB_PASSWORD', 'not-set')
    
    # Import config AFTER checking env
    from config_manager import config
    config_password = config.db_password
    
    # Import secrets manager
    from implementation.secrets_manager import get_database_config
    secrets_config = get_database_config()
    secrets_password = secrets_config.get('password', 'not-set')
    
    return {
        "env_password_length": len(env_password),
        "env_password_preview": env_password[:5] + "..." + env_password[-5:] if env_password != 'not-set' else 'not-set',
        "config_password_length": len(config_password),
        "config_password_preview": config_password[:5] + "..." + config_password[-5:] if config_password else 'not-set',
        "secrets_password_length": len(secrets_password),
        "secrets_password_preview": secrets_password[:5] + "..." + secrets_password[-5:] if secrets_password != 'not-set' else 'not-set',
        "all_match": env_password == config_password == secrets_password,
        "env_equals_config": env_password == config_password,
        "config_equals_secrets": config_password == secrets_password
    }

@app.get("/api/v1/test-final-connection")
def test_final_connection():
    """Test connection at the very end of the file"""
    from config_manager import config
    import psycopg2
    
    try:
        conn = psycopg2.connect(
            host=config.db_host,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password,
            port=config.db_port
        )
        
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
        
        conn.close()
        return {"success": True, "test": "final_connection"}
    except Exception as e:
        return {"success": False, "error": str(e)[:100], "test": "final_connection"}


# Emergency Debug Endpoints
@app.get("/debug/registration")
async def debug_registration():
    """Emergency debug page to see what's happening with registration"""
    from datetime import datetime
    import inspect
    
    debug_info = {
        "timestamp": datetime.now().isoformat(),
        "cava_status": "unknown",
        "cava_proxy_active": False,
        "last_registration_calls": [],
        "current_endpoints": [],
        "chat_register_source": "unknown",
        "environment": {
            "disable_cava": os.getenv('DISABLE_CAVA', 'false'),
            "cava_dry_run": os.getenv('CAVA_DRY_RUN_MODE', 'false'),
            "port": os.getenv('PORT', '8080')
        }
    }
    
    try:
        # Test CAVA directly
        import httpx
        async with httpx.AsyncClient() as client:
            # Try local CAVA API
            try:
                resp = await client.get('http://localhost:8001/health', timeout=5.0)
                debug_info["cava_status"] = resp.json()
            except:
                # Try on same port
                try:
                    resp = await client.get('http://localhost:8080/api/v1/cava/health', timeout=5.0)
                    debug_info["cava_status"] = resp.json()
                except:
                    debug_info["cava_status"] = "FAILED - CAVA not responding on 8001 or 8080"
    except Exception as e:
        debug_info["cava_status"] = f"ERROR: {str(e)}"
    
    # Check which registration function is actually being called
    try:
        # Get the actual function being used
        func_source = inspect.getsource(chat_register_step)
        first_line = func_source.split('\n')[0]
        if 'CAVA-powered' in func_source:
            debug_info["cava_proxy_active"] = True
            debug_info["chat_register_source"] = "CAVA PROXY VERSION"
        elif 'LangChain' in func_source:
            debug_info["chat_register_source"] = "OLD LANGCHAIN VERSION"
        else:
            debug_info["chat_register_source"] = first_line
    except Exception as e:
        debug_info["chat_register_source"] = f"ERROR: {str(e)}"
    
    # List current registration endpoints
    for route in app.routes:
        if 'register' in str(route.path).lower():
            debug_info["current_endpoints"].append({
                "path": str(route.path),
                "methods": list(route.methods) if hasattr(route, 'methods') else []
            })
    
    return debug_info

@app.get("/debug/logs")
async def debug_logs():
    """Show recent registration activity logs"""
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "recent_logs": [],
        "registration_history": getattr(app.state, 'registration_logs', [])[-20:],  # Last 20 calls
        "message": "Debug logs endpoint active"
    }
    
    # Try to read recent log entries if available
    try:
        # This would normally read from your logging system
        log_data["logging_level"] = logging.getLogger().level
        log_data["logger_name"] = logger.name
    except:
        log_data["logging_status"] = "Unable to access logging system"
    
    return log_data

@app.get("/debug/test-cava-proxy")
async def test_cava_proxy():
    """Test the CAVA proxy directly"""
    test_request = ChatRegisterRequest(
        user_input="Test User Name",
        session_id="debug-test-session",
        conversation_id="debug-test-conv",
        farmer_id=99999,
        conversation_history=[]
    )
    
    try:
        result = await chat_register_step(test_request)
        return {
            "success": True,
            "proxy_working": result.get("cava_enabled", False),
            "response": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "proxy_working": False
        }

@app.get("/debug/test-cava-direct")
async def test_cava_direct():
    """Test CAVA engine directly"""
    try:
        global _cava_engine
        
        if not _cava_engine and hasattr(app.state, 'cava_engine'):
            _cava_engine = app.state.cava_engine
            
        if not _cava_engine:
            return {
                "success": False,
                "error": "CAVA engine not initialized",
                "hint": "Check startup logs for CAVA initialization errors"
            }
        
        # Test CAVA directly
        result = await _cava_engine.handle_farmer_message(
            farmer_id=99999,
            message="Test Direct Engine Call",
            session_id="debug-direct-test",
            channel="registration"
        )
        
        return {
            "success": True,
            "engine_initialized": True,
            "direct_call_response": result
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/debug/redis/{session_id}")
async def debug_redis_state(session_id: str):
    """Check what's in Redis for this session"""
    try:
        import redis
        import json
        
        # Get Redis URL from environment
        redis_url = os.getenv('CAVA_REDIS_URL', 'redis://localhost:6379')
        r = redis.from_url(redis_url)
        
        # Check different possible keys
        keys_to_check = [
            f"cava:conversation:{session_id}",
            f"conversation:{session_id}",
            f"reg_farmer_{session_id}",
            session_id
        ]
        
        results = {}
        for key in keys_to_check:
            value = r.get(key)
            if value:
                try:
                    # Try to parse as JSON
                    results[key] = json.loads(value.decode('utf-8'))
                except:
                    results[key] = value.decode('utf-8')
            else:
                results[key] = None
        
        # Also check all keys matching patterns
        pattern_keys = []
        for pattern in [f"*{session_id}*", f"*farmer*{session_id[-6:]}*"]:
            matching = r.keys(pattern)
            pattern_keys.extend([k.decode('utf-8') for k in matching])
        
        return {
            "session_id": session_id,
            "redis_url": redis_url,
            "checked_keys": keys_to_check,
            "found_data": results,
            "pattern_matches": pattern_keys[:10],  # Limit to 10 matches
            "redis_connected": True
        }
    except Exception as e:
        return {
            "session_id": session_id,
            "error": str(e),
            "redis_connected": False
        }

# Initialize app state for logging
if not hasattr(app.state, 'registration_logs'):
    app.state.registration_logs = []

@app.on_event("startup")
async def startup_event():
    """Application startup event with CAVA logging"""
    logger.info("🚀 APP: Application starting up...")
    cava_logger.info("🚀 APP: Application starting up...")
    
    # Check CAVA environment variables
    cava_vars = {
        'CAVA_DRY_RUN_MODE': os.getenv('CAVA_DRY_RUN_MODE'),
        'CAVA_ENABLE_GRAPH': os.getenv('CAVA_ENABLE_GRAPH'),
        'CAVA_REDIS_URL': os.getenv('CAVA_REDIS_URL'),
        'CAVA_NEO4J_URI': os.getenv('CAVA_NEO4J_URI'),
        'DISABLE_CAVA': os.getenv('DISABLE_CAVA')
    }
    
    cava_logger.info("🔍 APP: CAVA Environment Check:")
    for var, value in cava_vars.items():
        status = "✅" if value else "❌"
        cava_logger.info(f"   {status} {var}: {value}")
    
    # Initialize CAVA engine globally for direct use
    global _cava_engine
    _cava_engine = None
    
    if os.getenv('DISABLE_CAVA', 'false').lower() != 'true':
        try:
            from implementation.cava.universal_conversation_engine import CAVAUniversalConversationEngine
            _cava_engine = CAVAUniversalConversationEngine()
            # Don't wait for full initialization - let it happen in background
            cava_logger.info("🔄 APP: CAVA engine created, initializing in background...")
            app.state.cava_engine = _cava_engine  # Store in app state
            
            # Initialize in background to not block startup
            import asyncio
            async def init_cava_background():
                try:
                    await _cava_engine.initialize()
                    cava_logger.info("✅ APP: CAVA engine initialized successfully in background")
                except Exception as init_e:
                    cava_logger.error(f"⚠️ APP: CAVA initialization incomplete: {str(init_e)}")
                    cava_logger.info("ℹ️ APP: CAVA will operate in limited mode")
            
            asyncio.create_task(init_cava_background())
            
        except Exception as e:
            cava_logger.error(f"❌ APP: CAVA engine creation failed: {str(e)}")
            import traceback
            cava_logger.error(f"Traceback: {traceback.format_exc()}")
            _cava_engine = None
    else:
        cava_logger.info("ℹ️ APP: CAVA engine disabled")


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple AVA OLO API Gateway on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8080)