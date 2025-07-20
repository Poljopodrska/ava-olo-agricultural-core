#!/usr/bin/env python3
"""
Web UI routes for AVA OLO Agricultural Core
Handles web interface endpoints (register, login, chat, dashboard)
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import logging
from datetime import datetime

from ..core.config import VERSION, CAVA_VERSION

logger = logging.getLogger(__name__)

router = APIRouter(tags=["web"])

def get_base_template(title: str, content: str) -> str:
    """Get base HTML template"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - AVA OLO</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
                color: #333;
            }}
            .navbar {{
                background-color: #2e7d32;
                color: white;
                padding: 1rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .navbar h1 {{
                margin: 0;
                font-size: 1.5rem;
            }}
            .container {{
                max-width: 1200px;
                margin: 2rem auto;
                padding: 0 1rem;
            }}
            .card {{
                background: white;
                border-radius: 8px;
                padding: 2rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }}
            .version-info {{
                background: #e8f5e9;
                padding: 1rem;
                border-radius: 4px;
                margin-bottom: 1rem;
                font-size: 0.9rem;
            }}
            .btn {{
                background-color: #4caf50;
                color: white;
                padding: 0.75rem 1.5rem;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 0.5rem;
            }}
            .btn:hover {{
                background-color: #45a049;
            }}
            input, textarea {{
                width: 100%;
                padding: 0.75rem;
                margin: 0.5rem 0;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
            }}
        </style>
    </head>
    <body>
        <div class="navbar">
            <h1>🌾 AVA OLO Agricultural Assistant</h1>
        </div>
        <div class="container">
            {content}
        </div>
    </body>
    </html>
    """

@router.get("/", response_class=HTMLResponse)
async def home():
    """Home page"""
    content = f"""
    <div class="card">
        <h2>Welcome to AVA OLO</h2>
        <div class="version-info">
            <strong>System Version:</strong> {VERSION}<br>
            <strong>CAVA Version:</strong> {CAVA_VERSION}
        </div>
        <p>Your AI-powered agricultural assistant for Eastern Europe.</p>
        
        <h3>Available Services:</h3>
        <a href="/register" class="btn">🌱 Register as Farmer</a>
        <a href="/login" class="btn">🔐 Login</a>
        <a href="/chat" class="btn">💬 Chat with AVA</a>
        <a href="/dashboard" class="btn">📊 Dashboard</a>
        
        <h3>API Endpoints:</h3>
        <a href="/health" class="btn">Health Check</a>
        <a href="/api/deployment/verify" class="btn">Deployment Info</a>
        <a href="/docs" class="btn">API Documentation</a>
    </div>
    """
    return HTMLResponse(content=get_base_template("Home", content))

@router.get("/register", response_class=HTMLResponse)
async def register_page():
    """CAVA Registration page"""
    content = """
    <div class="card">
        <h2>🌱 Farmer Registration</h2>
        <div class="version-info">
            <strong>CAVA Registration System:</strong> v""" + CAVA_VERSION + """
        </div>
        <p>Hello! I'm CAVA, your registration assistant. Let's get you registered!</p>
        
        <div id="chat-container">
            <div id="messages" style="height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 1rem; margin-bottom: 1rem; background: #fafafa;">
                <div class="message bot">👋 Hello! I'm CAVA. What's your name?</div>
            </div>
            
            <form id="chat-form" onsubmit="sendMessage(event)">
                <input type="text" id="message-input" placeholder="Type your message..." required>
                <button type="submit" class="btn">Send</button>
            </form>
        </div>
        
        <script>
            let sessionId = 'web_' + Date.now();
            
            async function sendMessage(event) {
                event.preventDefault();
                
                const input = document.getElementById('message-input');
                const message = input.value.trim();
                if (!message) return;
                
                // Add user message
                addMessage(message, 'user');
                input.value = '';
                
                try {
                    // Send to CAVA
                    const response = await fetch('/api/v1/registration/cava', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            message: message,
                            farmer_id: sessionId,
                            language: 'en'
                        })
                    });
                    
                    const data = await response.json();
                    
                    // Add bot response
                    addMessage(data.response, 'bot');
                    
                    // Check if registration complete
                    if (data.registration_complete) {
                        setTimeout(() => {
                            addMessage('✅ Registration complete! Redirecting to dashboard...', 'system');
                            setTimeout(() => window.location.href = '/dashboard', 2000);
                        }, 1000);
                    }
                } catch (error) {
                    addMessage('Sorry, there was an error. Please try again.', 'error');
                }
            }
            
            function addMessage(text, type) {
                const messages = document.getElementById('messages');
                const div = document.createElement('div');
                div.className = 'message ' + type;
                div.style.margin = '0.5rem 0';
                div.style.padding = '0.5rem';
                
                if (type === 'user') {
                    div.style.textAlign = 'right';
                    div.style.backgroundColor = '#e3f2fd';
                    div.innerHTML = '👤 ' + text;
                } else if (type === 'bot') {
                    div.style.backgroundColor = '#f1f8e9';
                    div.innerHTML = '🤖 ' + text;
                } else if (type === 'system') {
                    div.style.backgroundColor = '#fff3cd';
                    div.style.textAlign = 'center';
                    div.innerHTML = text;
                } else if (type === 'error') {
                    div.style.backgroundColor = '#ffebee';
                    div.style.color = '#c62828';
                    div.innerHTML = '❌ ' + text;
                }
                
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            }
        </script>
    </div>
    """
    return HTMLResponse(content=get_base_template("Register", content))

@router.get("/login", response_class=HTMLResponse)
async def login_page():
    """Login page"""
    content = """
    <div class="card">
        <h2>🔐 Farmer Login</h2>
        <form action="/dashboard" method="get">
            <label>Phone Number:</label>
            <input type="tel" name="phone" placeholder="+1234567890" required>
            
            <label>Password:</label>
            <input type="password" name="password" placeholder="Enter your password" required>
            
            <button type="submit" class="btn">Login</button>
        </form>
        
        <p>Don't have an account? <a href="/register">Register here</a></p>
    </div>
    """
    return HTMLResponse(content=get_base_template("Login", content))

@router.get("/chat", response_class=HTMLResponse)
async def chat_page():
    """Chat interface"""
    content = """
    <div class="card">
        <h2>💬 Chat with AVA</h2>
        <p>Ask me anything about farming, crops, weather, or agricultural practices!</p>
        
        <form method="post" action="/web/query">
            <label>Your Question:</label>
            <textarea name="query" rows="4" placeholder="What would you like to know?" required></textarea>
            
            <button type="submit" class="btn">Ask AVA</button>
        </form>
        
        <div style="margin-top: 2rem; padding: 1rem; background: #f5f5f5; border-radius: 4px;">
            <h4>Example Questions:</h4>
            <ul>
                <li>What crops grow best in Bulgaria?</li>
                <li>How do I deal with tomato blight?</li>
                <li>When should I plant corn in Eastern Europe?</li>
                <li>What's the weather forecast for farming?</li>
            </ul>
        </div>
    </div>
    """
    return HTMLResponse(content=get_base_template("Chat", content))

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Dashboard page"""
    content = f"""
    <div class="card">
        <h2>📊 Farmer Dashboard</h2>
        <div class="version-info">
            <strong>Welcome back!</strong> Last login: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin: 2rem 0;">
            <div style="background: #e8f5e9; padding: 1.5rem; border-radius: 8px; text-align: center;">
                <h3>🌾 Your Fields</h3>
                <p style="font-size: 2rem; margin: 0;">5</p>
                <p>Total: 25.5 hectares</p>
            </div>
            
            <div style="background: #fff3cd; padding: 1.5rem; border-radius: 8px; text-align: center;">
                <h3>📅 Active Tasks</h3>
                <p style="font-size: 2rem; margin: 0;">3</p>
                <p>Due this week</p>
            </div>
            
            <div style="background: #e3f2fd; padding: 1.5rem; border-radius: 8px; text-align: center;">
                <h3>🌤️ Weather</h3>
                <p style="font-size: 2rem; margin: 0;">22°C</p>
                <p>Partly cloudy</p>
            </div>
            
            <div style="background: #fce4ec; padding: 1.5rem; border-radius: 8px; text-align: center;">
                <h3>💰 Revenue</h3>
                <p style="font-size: 2rem; margin: 0;">€12,450</p>
                <p>This season</p>
            </div>
        </div>
        
        <h3>Quick Actions:</h3>
        <a href="/chat" class="btn">💬 Ask AVA</a>
        <a href="/register" class="btn">🌱 Add Field</a>
        <a href="#" class="btn">📋 View Tasks</a>
        <a href="#" class="btn">📊 Reports</a>
    </div>
    """
    return HTMLResponse(content=get_base_template("Dashboard", content))