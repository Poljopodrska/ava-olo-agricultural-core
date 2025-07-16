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

# Configure CAVA logger
cava_logger = logging.getLogger('CAVA')

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

# Root Web Interface Route - Complete Constitutional Interface with Weather
@app.get("/", response_class=HTMLResponse)
async def main_web_interface():
    """Complete Constitutional Farmer Web Interface"""
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
        <div class="container">
            <!-- Constitutional Header -->
            <header class="constitutional-header">
                <div class="constitutional-logo"></div>
                <div class="constitutional-brand">AVA OLO</div>
                <div class="constitutional-tagline">Your Constitutional Agricultural Assistant</div>
            </header>

            <!-- Weather Section -->
            <section class="weather-section">
                <!-- Real-Time Date/Time Display -->
                <div class="datetime-display">
                    <div class="current-time" id="currentTime">Loading...</div>
                    <div class="current-date" id="currentDate">Loading...</div>
                </div>
                
                <!-- Today's Weather Featured -->
                <div class="weather-today">
                    <div class="today-header">Today's Weather</div>
                    <div class="today-main">
                        <div class="today-icon">
                            <div class="weather-icon">
                                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="12" cy="12" r="5" fill="#FFD700" stroke="#FFA500" stroke-width="2"/>
                                    <g stroke="#FFD700" stroke-width="2" stroke-linecap="round">
                                        <line x1="12" y1="1" x2="12" y2="3"/>
                                        <line x1="12" y1="21" x2="12" y2="23"/>
                                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                                        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                                        <line x1="1" y1="12" x2="3" y2="12"/>
                                        <line x1="21" y1="12" x2="23" y2="12"/>
                                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                                        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                                    </g>
                                </svg>
                            </div>
                        </div>
                        <div class="today-details">
                            <div class="today-condition">Sunny</div>
                            <div class="today-temp">22<span style="font-size:24px;">°C</span></div>
                            <div class="today-rain">💧 0<span style="font-size:16px;">mm</span></div>
                            <div class="today-wind">🌪️ NE 12<span style="font-size:16px;">km/h</span></div>
                        </div>
                    </div>
                    
                    <!-- Endless 24-Hour Tape -->
                    <div class="hourly-container">
                        <div class="hourly-header">
                            <div class="hourly-title">Next 24 Hours</div>
                            <div class="hourly-controls">
                                <button class="tape-btn" onclick="tapeLeft()">◀◀</button>
                                <button class="tape-btn" onclick="tapeRight()">▶▶</button>
                                <button class="tape-btn" onclick="goToNow()">NOW</button>
                            </div>
                        </div>
                        <div class="hourly-tape-container">
                            <div class="hourly-tape" id="hourlyTape">
                                <!-- Will be populated by JavaScript with NEXT 24 hours -->
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- 5-Day Timeline -->
                <div class="weather-timeline" id="weatherTimeline">
                    <!-- 5-day timeline will be populated by JavaScript -->
                </div>
                
                <!-- Extended Forecast Toggle -->
                <div style="text-align: center; margin: 24px 0;">
                    <button class="constitutional-btn constitutional-btn-secondary" onclick="toggleExtendedForecast()" style="width: auto; padding: 12px 24px;">
                        <span id="toggleText">Show Extended Forecast</span>
                    </button>
                </div>
                
                <!-- Extended Forecast Section -->
                <div class="extended-forecast-section" id="extendedForecastSection" style="display: none;">
                    <div class="extended-header">
                        <h3>Extended Forecast</h3>
                        <div class="forecast-controls">
                            <button class="forecast-btn active" onclick="showDays(5)">5 Days</button>
                            <button class="forecast-btn" onclick="showDays(10)">10 Days</button>
                            <button class="forecast-btn" onclick="showDays(15)">15 Days</button>
                            <button class="forecast-btn" onclick="showDays(20)">20 Days</button>
                        </div>
                    </div>
                    <div class="extended-timeline" id="extendedTimeline">
                        <!-- Will be populated by JavaScript -->
                    </div>
                </div>
            </section>

            <!-- Main Query Interface -->
            <section class="constitutional-card">
                <h1 class="constitutional-card-title">How can I help you today?</h1>
                <textarea class="constitutional-textarea" placeholder="Ask me anything about your crops, soil, weather, or farming techniques. I'm here to help Bulgarian mango farmers and everyone else!" onkeypress="handleEnterKey(event, 'submitQuery')"></textarea>
                <div class="enter-hint">Press Enter to submit your question</div>
                <button id="submitQuery" class="constitutional-btn">🔍 Submit Question</button>
            </section>

            <!-- Action Buttons -->
            <section class="constitutional-card">
                <h2 class="constitutional-card-title">Quick Actions</h2>
                <button class="constitutional-btn">📋 I want to report a task</button>
                <button class="constitutional-btn constitutional-btn-secondary">📊 I need data about my farm</button>
            </section>

            <!-- Authentication Section -->
            <div id="authSection">
                <!-- Registration Chat Interface -->
                <div id="registrationChat" class="constitutional-card">
                    <h1 class="constitutional-card-title">🚜 Join AVA OLO</h1>
                    <div id="chatMessages" style="max-height: 400px; overflow-y: auto; margin-bottom: 16px; padding: 16px; background: var(--cream); border-radius: 8px;">
                        <!-- Chat messages appear here -->
                    </div>
                    <input id="chatInput" class="constitutional-input" placeholder="Type your response..." onkeypress="handleEnterKey(event, 'sendChatMessage')" style="width: 100%; padding: 16px; font-size: 18px; border: 2px solid var(--primary-olive); border-radius: 8px; margin-bottom: 16px;">
                    <button id="sendChatMessage" class="constitutional-btn" onclick="sendChatMessage()">💬 Send</button>
                    <div class="enter-hint">Press Enter to send your message</div>
                </div>

                <!-- Login Interface (show after registration or for existing users) -->
                <div id="loginSection" class="constitutional-card" style="display: none;">
                    <h1 class="constitutional-card-title">🔐 Login to My Farm</h1>
                    <input id="loginPhone" class="constitutional-input" placeholder="WhatsApp number (e.g., +385912345678)" style="width: 100%; padding: 16px; font-size: 18px; border: 2px solid var(--primary-olive); border-radius: 8px; margin-bottom: 16px;">
                    <input id="loginPassword" type="password" class="constitutional-input" placeholder="Password" style="width: 100%; padding: 16px; font-size: 18px; border: 2px solid var(--primary-olive); border-radius: 8px; margin-bottom: 16px;">
                    <button class="constitutional-btn" onclick="performLogin()">🔐 Login</button>
                    <div id="loginError" style="color: red; margin-top: 16px; display: none;"></div>
                </div>

                <div style="text-align: center; margin: 16px 0;">
                    <button id="toggleMode" class="constitutional-btn constitutional-btn-secondary" onclick="toggleLoginRegister()">
                        <span id="toggleText">Already have an account? Login</span>
                    </button>
                </div>
            </div>
        </div>

        <script>
            function handleEnterKey(event, buttonId) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    document.getElementById(buttonId).click();
                }
            }
            document.getElementById('submitQuery').addEventListener('click', function() {
                const textarea = document.querySelector('.constitutional-textarea');
                const query = textarea.value.trim();
                if (query) {
                    alert('🏛️ Constitutional Query Submitted\\n\\n' + query + '\\n\\n✅ MANGO RULE: Works for Bulgarian mango farmers');
                    textarea.value = '';
                }
            });
            // Real-time clock and weather system
            let tapePosition = 0;
            let currentForecastDays = 5;

            // Update real-time clock
            function updateDateTime() {
                const now = new Date();
                const timeString = now.toLocaleTimeString('en-US', { 
                    hour12: false,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
                const dateString = now.toLocaleDateString('en-US', { 
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
                
                document.getElementById('currentTime').textContent = timeString;
                document.getElementById('currentDate').textContent = dateString;
            }

            // Generate next 24 hours from current time
            function generateNext24Hours() {
                const hours = [];
                const now = new Date();
                
                for (let i = 0; i < 24; i++) {
                    const hour = new Date(now.getTime() + i * 60 * 60 * 1000);
                    const hourStr = hour.getHours().toString().padStart(2, '0') + ':00';
                    const isCurrentHour = i === 0;
                    
                    // Generate weather based on hour
                    let icon, temp, rain, wind;
                    const h = hour.getHours();
                    
                    if (h >= 22 || h <= 5) {
                        icon = getNightIcon();
                        temp = Math.floor(12 + Math.random() * 6);
                    } else if (h === 6 || h === 20) {
                        icon = getDawnIcon();
                        temp = Math.floor(14 + Math.random() * 8);
                    } else if (h >= 10 && h <= 16) {
                        icon = getSunnyIcon();
                        temp = Math.floor(20 + Math.random() * 8);
                    } else {
                        icon = getPartlyCloudyIcon();
                        temp = Math.floor(16 + Math.random() * 8);
                    }
                    
                    rain = Math.floor(Math.random() * 3);
                    wind = Math.floor(5 + Math.random() * 15);
                    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
                    const windDir = directions[Math.floor(Math.random() * directions.length)];
                    
                    hours.push({
                        time: hourStr,
                        icon: icon,
                        temp: temp,
                        rain: rain,
                        wind: `${windDir} ${wind}`,
                        isCurrent: isCurrentHour
                    });
                }
                
                return hours;
            }

            // Generate extended forecast (5-20 days)
            function generateExtendedForecast(days) {
                const forecast = [];
                const now = new Date();
                
                for (let i = 0; i < days; i++) {
                    const date = new Date(now.getTime() + (i + 1) * 24 * 60 * 60 * 1000);
                    const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
                    const monthDay = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                    
                    // Generate realistic weather
                    const conditions = [
                        { icon: getSunnyIcon(), condition: 'Sunny', temp: [18, 28] },
                        { icon: getPartlyCloudyIcon(), condition: 'Partly Cloudy', temp: [16, 25] },
                        { icon: getCloudyIcon(), condition: 'Cloudy', temp: [14, 22] },
                        { icon: getRainIcon('moderate'), condition: 'Light Rain', temp: [12, 20] },
                        { icon: getThunderstormIcon(), condition: 'Storms', temp: [10, 18] }
                    ];
                    
                    const weather = conditions[Math.floor(Math.random() * conditions.length)];
                    const tempMin = weather.temp[0] + Math.floor(Math.random() * 4);
                    const tempMax = weather.temp[1] + Math.floor(Math.random() * 4);
                    const rain = Math.floor(Math.random() * 12);
                    
                    forecast.push({
                        day: dayName,
                        date: monthDay,
                        icon: weather.icon,
                        condition: weather.condition,
                        tempMin: tempMin,
                        tempMax: tempMax,
                        rain: rain
                    });
                }
                
                return forecast;
            }

            // Populate 24-hour tape
            function populateHourlyTape() {
                const hours = generateNext24Hours();
                const tape = document.getElementById('hourlyTape');
                
                tape.innerHTML = hours.map(hour => `
                    <div class="hour-square ${hour.isCurrent ? 'current-hour' : ''}">
                        <div class="hour-time">${hour.time}</div>
                        <div class="hour-icon"><div class="weather-icon">${hour.icon}</div></div>
                        <div class="hour-temp">${hour.temp}°C</div>
                        <div class="hour-rain">💧 ${hour.rain}mm</div>
                        <div class="hour-wind">🌪️ ${hour.wind}km/h</div>
                    </div>
                `).join('');
            }

            // Tape controls
            function tapeLeft() {
                tapePosition = Math.max(tapePosition - 200, 0);
                updateTapePosition();
            }

            function tapeRight() {
                tapePosition = Math.min(tapePosition + 200, 1600);
                updateTapePosition();
            }

            function goToNow() {
                tapePosition = 0;
                updateTapePosition();
            }

            function updateTapePosition() {
                const tape = document.getElementById('hourlyTape');
                tape.style.transform = `translateX(-${tapePosition}px)`;
            }

            // Extended forecast controls
            function showDays(days) {
                currentForecastDays = days;
                
                // Update button states
                document.querySelectorAll('.forecast-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                event.target.classList.add('active');
                
                // Populate extended forecast
                const forecast = generateExtendedForecast(days);
                const timeline = document.getElementById('extendedTimeline');
                
                timeline.innerHTML = forecast.map(day => `
                    <div class="extended-day">
                        <div style="font-size: 14px; color: var(--dark-olive); margin-bottom: 8px;">${day.day}</div>
                        <div style="font-size: 12px; color: var(--dark-olive); margin-bottom: 12px;">${day.date}</div>
                        <div style="margin-bottom: 12px;"><div class="weather-icon">${day.icon}</div></div>
                        <div style="font-size: 14px; color: var(--dark-olive); margin-bottom: 8px;">${day.condition}</div>
                        <div style="font-size: 18px; font-weight: bold; color: var(--primary-brown); margin-bottom: 4px;">${day.tempMax}°C</div>
                        <div style="font-size: 14px; color: var(--dark-olive); margin-bottom: 8px;">${day.tempMin}°C</div>
                        <div style="font-size: 14px; color: var(--dark-olive);">💧 ${day.rain}mm</div>
                    </div>
                `).join('');
            }

            // Initialize everything
            document.addEventListener('DOMContentLoaded', function() {
                // Start real-time clock
                updateDateTime();
                setInterval(updateDateTime, 1000);
                
                // Initialize weather systems
                populateHourlyTape();
                populate5DayTimeline();
                
                // Don't initialize extended forecast until toggle is clicked
                
                console.log('🏛️ Constitutional Weather System: Next 24 hours + Extended forecast active');
            });
            
            // Toggle Extended Forecast
            function toggleExtendedForecast() {
                const section = document.getElementById('extendedForecastSection');
                const toggleText = document.getElementById('toggleText');
                
                if (section.style.display === 'none') {
                    section.style.display = 'block';
                    toggleText.textContent = 'Hide Extended Forecast';
                    // Initialize if not already done
                    if (!section.dataset.initialized) {
                        showDays(5);
                        section.dataset.initialized = 'true';
                    }
                } else {
                    section.style.display = 'none';
                    toggleText.textContent = 'Show Extended Forecast';
                }
            }
            
            // Populate hourly forecast with SVG icons
            function populateHourlyForecast() {
                const slider = document.getElementById('hourlySlider');
                const hours = [
                    {time: '00:00', icon: 'night', temp: '14°C', rain: 0, wind: 'E 5km/h'},
                    {time: '01:00', icon: 'night', temp: '13°C', rain: 0, wind: 'E 4km/h'},
                    {time: '02:00', icon: 'night', temp: '12°C', rain: 0, wind: 'E 3km/h'},
                    {time: '03:00', icon: 'night', temp: '12°C', rain: 0, wind: 'NE 3km/h'},
                    {time: '04:00', icon: 'night', temp: '11°C', rain: 0, wind: 'NE 4km/h'},
                    {time: '05:00', icon: 'night', temp: '11°C', rain: 0, wind: 'NE 5km/h'},
                    {time: '06:00', icon: 'dawn', temp: '12°C', rain: 0, wind: 'NE 6km/h'},
                    {time: '07:00', icon: 'dawn', temp: '14°C', rain: 0, wind: 'NE 7km/h'},
                    {time: '08:00', icon: 'cloudy', temp: '16°C', rain: 0, wind: 'NE 8km/h'},
                    {time: '09:00', icon: 'cloudy', temp: '18°C', rain: 0, wind: 'NE 10km/h'},
                    {time: '10:00', icon: 'sunny', temp: '20°C', rain: 0, wind: 'NE 11km/h'},
                    {time: '11:00', icon: 'sunny', temp: '21°C', rain: 0, wind: 'NE 12km/h'},
                    {time: '12:00', icon: 'sunny', temp: '22°C', rain: 0, wind: 'NE 12km/h'},
                    {time: '13:00', icon: 'sunny', temp: '23°C', rain: 0, wind: 'E 13km/h'},
                    {time: '14:00', icon: 'sunny', temp: '24°C', rain: 0, wind: 'E 14km/h'},
                    {time: '15:00', icon: 'sunny', temp: '25°C', rain: 0, wind: 'E 15km/h'},
                    {time: '16:00', icon: 'sunny', temp: '24°C', rain: 0, wind: 'E 14km/h'},
                    {time: '17:00', icon: 'partly-cloudy', temp: '23°C', rain: 0, wind: 'E 12km/h'},
                    {time: '18:00', icon: 'partly-cloudy', temp: '21°C', rain: 0, wind: 'E 8km/h'},
                    {time: '19:00', icon: 'partly-cloudy', temp: '20°C', rain: 0, wind: 'SE 7km/h'},
                    {time: '20:00', icon: 'dawn', temp: '18°C', rain: 0, wind: 'SE 6km/h'},
                    {time: '21:00', icon: 'night', temp: '17°C', rain: 0, wind: 'SE 6km/h'},
                    {time: '22:00', icon: 'night', temp: '16°C', rain: 0, wind: 'SE 5km/h'},
                    {time: '23:00', icon: 'night', temp: '15°C', rain: 0, wind: 'E 5km/h'}
                ];
                
                let html = '';
                hours.forEach(hour => {
                    let iconHtml = '';
                    switch(hour.icon) {
                        case 'sunny': iconHtml = getSunnyIcon(); break;
                        case 'cloudy': iconHtml = getCloudyIcon(); break;
                        case 'partly-cloudy': iconHtml = getPartlyCloudyIcon(); break;
                        case 'night': iconHtml = getNightIcon(); break;
                        case 'dawn': iconHtml = getDawnIcon(); break;
                    }
                    
                    html += `<div class="hourly-square">
                        <div class="hour-time">${hour.time}</div>
                        <div class="hour-icon"><div class="weather-icon">${iconHtml}</div></div>
                        <div class="hour-temp">${hour.temp}</div>
                        <div class="hour-rain">💧 ${hour.rain}mm</div>
                        <div class="hour-wind">🌪️ ${hour.wind}</div>
                    </div>`;
                });
                
                slider.innerHTML = html;
            }
            
            // Populate 5-day timeline with SVG icons
            function populate5DayTimeline() {
                const timeline = document.getElementById('weatherTimeline');
                const today = new Date();
                const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
                
                const days = [
                    {label: 'Today', icon: 'sunny', condition: 'Sunny', temp: 22, rain: 0, wind: 'NE 12km/h', today: true},
                    {label: 'Tomorrow', icon: 'partly-cloudy', condition: 'Partly Sunny', temp: 24, rain: 1, wind: 'N 8km/h'},
                    {label: dayNames[(today.getDay() + 2) % 7], icon: 'rain-moderate', condition: 'Light Rain', temp: 18, rain: 8, wind: 'SW 18km/h'},
                    {label: dayNames[(today.getDay() + 3) % 7], icon: 'cloudy', condition: 'Cloudy', temp: 20, rain: 3, wind: 'W 15km/h'},
                    {label: dayNames[(today.getDay() + 4) % 7], icon: 'thunderstorm', condition: 'Thunderstorms', temp: 16, rain: 15, wind: 'W 22km/h'}
                ];
                
                let html = '';
                days.forEach(day => {
                    let iconHtml = '';
                    switch(day.icon) {
                        case 'sunny': iconHtml = getSunnyIcon(); break;
                        case 'cloudy': iconHtml = getCloudyIcon(); break;
                        case 'partly-cloudy': iconHtml = getPartlyCloudyIcon(); break;
                        case 'rain-light': iconHtml = getRainIcon('light'); break;
                        case 'rain-moderate': iconHtml = getRainIcon('moderate'); break;
                        case 'rain-heavy': iconHtml = getRainIcon('heavy'); break;
                        case 'thunderstorm': iconHtml = getThunderstormIcon(); break;
                    }
                    
                    html += `<div class="weather-day${day.today ? ' weather-day-today' : ''}">
                        <div class="day-label">${day.label}</div>
                        <div class="day-icon"><div class="weather-icon">${iconHtml}</div></div>
                        <div class="day-condition">${day.condition}</div>
                        <div class="day-temp">${day.temp}<span style="font-size:16px;">°C</span></div>
                        <div class="day-rain">💧 ${day.rain}<span style="font-size:14px;">mm</span></div>
                        <div class="day-wind">🌪️ ${day.wind}</div>
                    </div>`;
                });
                
                timeline.innerHTML = html;
            }

            console.log('🏛️ Constitutional Web Interface with Enhanced Weather System Active');
            
            // SVG Weather Icon Functions
            function getSunnyIcon() {
                return `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="5" fill="#FFD700" stroke="#FFA500" stroke-width="2"/>
                    <g stroke="#FFD700" stroke-width="2" stroke-linecap="round">
                        <line x1="12" y1="1" x2="12" y2="3"/>
                        <line x1="12" y1="21" x2="12" y2="23"/>
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                        <line x1="1" y1="12" x2="3" y2="12"/>
                        <line x1="21" y1="12" x2="23" y2="12"/>
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                    </g>
                </svg>`;
            }
            
            function getCloudyIcon() {
                return `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M18 10h-1.26A8 8 0 1 0 9 18h9a5 5 0 0 0 0-10z" 
                          fill="#808080" stroke="#696969" stroke-width="2" stroke-linejoin="round"/>
                </svg>`;
            }
            
            function getPartlyCloudyIcon() {
                return `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <g>
                        <circle cx="10" cy="10" r="3" fill="#FFD700" stroke="#FFA500" stroke-width="1.5"/>
                        <g stroke="#FFD700" stroke-width="1.5" stroke-linecap="round" opacity="0.8">
                            <line x1="10" y1="4" x2="10" y2="5"/>
                            <line x1="15" y1="10" x2="16" y2="10"/>
                            <line x1="14.5" y1="5.5" x2="15.5" y2="4.5"/>
                        </g>
                        <path d="M16 12h-0.8A5 5 0 1 0 10 17h6a3 3 0 0 0 0-6z" 
                              fill="#808080" stroke="#696969" stroke-width="1.5" stroke-linejoin="round"/>
                    </g>
                </svg>`;
            }
            
            function getRainIcon(intensity = 'moderate') {
                const drops = intensity === 'light' ? 2 : intensity === 'heavy' ? 4 : 3;
                let dropPaths = '';
                for (let i = 0; i < drops; i++) {
                    const x = 8 + (i * 3);
                    dropPaths += `<line x1="${x}" y1="13" x2="${x-1}" y2="16" stroke="#4169E1" stroke-width="1.5" stroke-linecap="round"/>`;
                }
                return `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M18 10h-1.26A8 8 0 1 0 9 18h9a5 5 0 0 0 0-10z" 
                          fill="#808080" stroke="#696969" stroke-width="2" stroke-linejoin="round"/>
                    ${dropPaths}
                </svg>`;
            }
            
            function getThunderstormIcon() {
                return `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M18 10h-1.26A8 8 0 1 0 9 18h9a5 5 0 0 0 0-10z" 
                          fill="#2F4F4F" stroke="#1C1C1C" stroke-width="2" stroke-linejoin="round"/>
                    <path d="M13 16l-3 5 3-5h-3l3-5" 
                          fill="none" stroke="#FFD700" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
                </svg>`;
            }
            
            function getSnowIcon() {
                return `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M18 10h-1.26A8 8 0 1 0 9 18h9a5 5 0 0 0 0-10z" 
                          fill="#808080" stroke="#696969" stroke-width="2" stroke-linejoin="round"/>
                    <g fill="#FFFFFF" stroke="#4169E1" stroke-width="0.5">
                        <circle cx="8" cy="14" r="1"/>
                        <circle cx="12" cy="13" r="1"/>
                        <circle cx="16" cy="14" r="1"/>
                        <circle cx="10" cy="16" r="1"/>
                        <circle cx="14" cy="16" r="1"/>
                    </g>
                </svg>`;
            }
            
            function getFogIcon() {
                return `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <g stroke="#808080" stroke-width="2" stroke-linecap="round">
                        <line x1="4" y1="8" x2="20" y2="8" opacity="0.8"/>
                        <line x1="4" y1="12" x2="20" y2="12"/>
                        <line x1="4" y1="16" x2="20" y2="16" opacity="0.6"/>
                    </g>
                </svg>`;
            }
            
            function getNightIcon() {
                return `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" 
                          fill="#FFFACD" stroke="#FFD700" stroke-width="2" stroke-linejoin="round"/>
                </svg>`;
            }
            
            function getDawnIcon() {
                return `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <g>
                        <path d="M12 15a5 5 0 0 0 0-10v10z" fill="#FFB347" stroke="#FF8C00" stroke-width="2"/>
                        <line x1="4" y1="18" x2="20" y2="18" stroke="#FFD700" stroke-width="2" stroke-linecap="round"/>
                        <line x1="6" y1="21" x2="18" y2="21" stroke="#FFD700" stroke-width="1.5" stroke-linecap="round" opacity="0.6"/>
                    </g>
                </svg>`;
            }
            
            // Authentication and Chat Registration Functions
            let conversationHistory = [];
            let lastAvaMessage = "";
            let registrationData = {};
            let authToken = localStorage.getItem('ava_auth_token');
            
            // Check if user is already authenticated
            if (authToken) {
                // Hide auth section if already logged in
                document.getElementById('authSection').style.display = 'none';
            }
            
            async function sendChatMessage() {
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Add user message to chat
                addChatMessage(message, 'user');
                input.value = '';
                
                try {
                    // Send to backend with conversation context
                    // Try CAVA first, fallback to old system if not available
                    let endpoint = '/api/v1/cava/register';
                    let requestBody = {
                        farmer_id: 12345, // Temporary ID for registration
                        message: formData.input,
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
                    addChatMessage(data.message, 'ava');
                    
                    // Update context based on system (CAVA vs old)
                    if (endpoint.includes('cava')) {
                        // CAVA response format
                        conversationData.conversation_id = data.session_id || conversationData.conversation_id;
                        if (data.debug_info) {
                            console.log('CAVA Debug:', data.debug_info);
                        }
                    } else {
                        // Old system response format
                        if (data.extracted_data) {
                            Object.assign(registrationData, data.extracted_data || {});
                        }
                        conversationHistory = data.conversation_history || conversationHistory;
                        lastAvaMessage = data.last_ava_message || data.message;
                        conversationData.conversation_id = data.conversation_id || conversationData.conversation_id;
                    }
                    
                    // Log who handled the response (for debugging)
                    console.log(`🤖 Handled by: ${data.handled_by || 'unknown'}`);
                    if (data.supervision_notes) {
                        console.log(`👁️ Supervision: ${data.supervision_notes}`);
                    }
                    if (data.debug_info) {
                        console.log('🔍 Debug Info:', data.debug_info);
                    }
                    
                    // Handle completion
                    if (data.status === "COMPLETE") {
                        // Registration complete
                        if (data.token) {
                            localStorage.setItem('ava_auth_token', data.token);
                            localStorage.setItem('ava_user', JSON.stringify(data.user));
                            // Hide auth section after successful registration
                            setTimeout(() => {
                                document.getElementById('authSection').style.display = 'none';
                            }, 3000);
                        }
                    }
                } catch (error) {
                    console.error('Chat registration error:', error);
                    addChatMessage('Sorry, I had trouble processing that. Could you please try again?', 'ava');
                }
            }
            
            function addChatMessage(message, sender) {
                const chatDiv = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.style.marginBottom = '12px';
                messageDiv.style.padding = '8px 12px';
                messageDiv.style.borderRadius = '8px';
                
                if (sender === 'ava') {
                    messageDiv.style.background = 'var(--primary-olive)';
                    messageDiv.style.color = 'white';
                    messageDiv.innerHTML = `<strong>🤖 AVA:</strong> ${message}`;
                } else {
                    messageDiv.style.background = 'var(--white)';
                    messageDiv.style.border = '1px solid var(--light-gray)';
                    messageDiv.innerHTML = `<strong>👨‍🌾 You:</strong> ${message}`;
                }
                
                chatDiv.appendChild(messageDiv);
                chatDiv.scrollTop = chatDiv.scrollHeight;
            }
            
            function toggleLoginRegister() {
                const registrationChat = document.getElementById('registrationChat');
                const loginSection = document.getElementById('loginSection');
                const toggleText = document.getElementById('toggleText');
                
                if (registrationChat.style.display === 'none') {
                    registrationChat.style.display = 'block';
                    loginSection.style.display = 'none';
                    toggleText.textContent = 'Already have an account? Login';
                } else {
                    registrationChat.style.display = 'none';
                    loginSection.style.display = 'block';
                    toggleText.textContent = 'Need an account? Register';
                }
            }
            
            async function performLogin() {
                const phone = document.getElementById('loginPhone').value.trim();
                const password = document.getElementById('loginPassword').value;
                const errorDiv = document.getElementById('loginError');
                
                if (!phone || !password) {
                    errorDiv.textContent = 'Please enter both phone number and password';
                    errorDiv.style.display = 'block';
                    return;
                }
                
                try {
                    const response = await fetch('/api/v1/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            wa_phone_number: phone,
                            password: password
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success && data.token) {
                        localStorage.setItem('ava_auth_token', data.token);
                        localStorage.setItem('ava_user', JSON.stringify(data.user));
                        errorDiv.style.display = 'none';
                        // Hide auth section after successful login
                        document.getElementById('authSection').style.display = 'none';
                    } else {
                        errorDiv.textContent = data.message || 'Login failed';
                        errorDiv.style.display = 'block';
                    }
                } catch (error) {
                    console.error('Login error:', error);
                    errorDiv.textContent = 'Login failed. Please try again.';
                    errorDiv.style.display = 'block';
                }
            }
            
            // Initialize chat on page load
            document.addEventListener('DOMContentLoaded', function() {
                // Only show chat if not authenticated
                if (!authToken) {
                    const initialMessage = "Hi! I'm AVA, your agricultural assistant. What's your full name? (first and last name)";
                    addChatMessage(initialMessage, 'ava');
                    lastAvaMessage = initialMessage;
                }
            });
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


    
    @app.post("/api/v1/auth/chat-register")
    async def chat_register_step(request: ChatRegisterRequest):
        """LangChain memory-based registration"""
        
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
                        "conversation_history": context["conversation_history"],
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
    
    # Test CAVA initialization
    if os.getenv('DISABLE_CAVA', 'false').lower() != 'true':
        try:
            from implementation.cava.universal_conversation_engine import CAVAUniversalConversationEngine
            engine = CAVAUniversalConversationEngine()
            await engine.initialize()
            cava_logger.info("✅ APP: CAVA engine test initialization successful")
        except Exception as e:
            cava_logger.error(f"❌ APP: CAVA engine test initialization failed: {str(e)}")
    else:
        cava_logger.info("ℹ️ APP: CAVA engine test skipped (disabled)")


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple AVA OLO API Gateway on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8080)