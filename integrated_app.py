#!/usr/bin/env python3
"""
Integrated AVA OLO Application
Combines all dashboards into a single application
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
import subprocess
import os
import sys
import threading
import time
from datetime import datetime

app = FastAPI(
    title="AVA OLO Integrated Platform",
    description="All dashboards in one application",
    version="1.0.0"
)

# Front page HTML (simplified)
FRONT_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌾 AVA OLO Dashboard Hub</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .logo {
            font-size: 3rem;
            font-weight: 700;
            color: #2e7d32;
            margin-bottom: 0.5rem;
        }
        
        .tagline {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 1rem;
        }
        
        .container {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
            max-width: 900px;
            width: 100%;
        }
        
        .dashboard-card {
            background: white;
            border-radius: 16px;
            padding: 2.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            cursor: pointer;
            text-decoration: none;
            color: inherit;
            position: relative;
            overflow: hidden;
        }
        
        .dashboard-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        }
        
        .card-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .card-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #333;
        }
        
        .card-description {
            color: #666;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }
        
        .card-features {
            list-style: none;
            margin-bottom: 1.5rem;
        }
        
        .card-features li {
            padding: 0.5rem 0;
            color: #555;
        }
        
        .card-features li::before {
            content: '✓ ';
            color: #4caf50;
            font-weight: bold;
        }
        
        .card-action {
            color: #2e7d32;
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .footer {
            background: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1 class="logo">🌾 AVA OLO Dashboard Hub</h1>
        <p class="tagline">Agricultural Intelligence & Business Analytics Platform</p>
    </div>
    
    <div class="container">
        <div class="dashboard-grid">
            <!-- Database Dashboard -->
            <a href="/database-dashboard" class="dashboard-card">
                <div class="card-icon">🗄️</div>
                <h2 class="card-title">Database Dashboard</h2>
                <p class="card-description">
                    Interactive agricultural database explorer with AI-powered natural language queries
                </p>
                <ul class="card-features">
                    <li>Natural language SQL queries</li>
                    <li>Real-time data exploration</li>
                    <li>Save frequently used queries</li>
                    <li>GPT-4 powered insights</li>
                </ul>
                <div class="card-action">
                    Open Database Dashboard →
                </div>
            </a>
            
            <!-- Business Dashboard -->
            <a href="/business-dashboard" class="dashboard-card">
                <div class="card-icon">📊</div>
                <h2 class="card-title">Business Dashboard</h2>
                <p class="card-description">
                    Comprehensive KPIs and metrics for agricultural business intelligence
                </p>
                <ul class="card-features">
                    <li>Real-time business metrics</li>
                    <li>Growth trends & analytics</li>
                    <li>Interactive data charts</li>
                    <li>Activity monitoring</li>
                </ul>
                <div class="card-action">
                    Open Business Dashboard →
                </div>
            </a>
        </div>
    </div>
    
    <div class="footer">
        <p>© 2024 AVA OLO Agricultural Intelligence Platform</p>
        <p style="margin-top: 0.5rem; color: #999;">
            Select a dashboard to continue
        </p>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    """Main landing page"""
    return HTMLResponse(content=FRONT_PAGE_HTML)

@app.get("/database-dashboard")
async def database_dashboard():
    """Redirect to database dashboard (main.py)"""
    # In production, this would be handled by a reverse proxy
    # For now, provide instructions
    return HTMLResponse(content="""
    <html>
    <head>
        <meta http-equiv="refresh" content="3;url=/">
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: #f5f5f5;
            }
            .message {
                text-align: center;
                padding: 2rem;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        <div class="message">
            <h2>🗄️ Database Dashboard</h2>
            <p>The database dashboard runs on the main application.</p>
            <p>In production, this would be handled by the load balancer.</p>
            <p><a href="/">← Back to Hub</a></p>
        </div>
    </body>
    </html>
    """)

@app.get("/business-dashboard")
async def business_dashboard():
    """Redirect to business dashboard"""
    return HTMLResponse(content="""
    <html>
    <head>
        <meta http-equiv="refresh" content="3;url=/">
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: #f5f5f5;
            }
            .message {
                text-align: center;
                padding: 2rem;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        <div class="message">
            <h2>📊 Business Dashboard</h2>
            <p>The business dashboard is available separately.</p>
            <p>Run: <code>python run_business_dashboard.py</code></p>
            <p><a href="/">← Back to Hub</a></p>
        </div>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AVA OLO Integrated Platform",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv
    load_dotenv()
    
    print("🌾 Starting AVA OLO Integrated Platform")
    print("📍 Access at: http://localhost:8080")
    print("\nNote: In production, use a reverse proxy to route:")
    print("  / -> This integrated app")
    print("  /database-dashboard -> main.py app") 
    print("  /business-dashboard -> business_dashboard_updated.py app")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)