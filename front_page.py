#!/usr/bin/env python3
"""
AVA OLO Dashboard Hub - Front Page
Central landing page for all dashboards
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from datetime import datetime
import os

app = FastAPI(
    title="AVA OLO Dashboard Hub",
    description="Central hub for all AVA OLO dashboards",
    version="1.0.0"
)

# Get the base URL from environment or use default
BASE_URL = os.getenv('BASE_URL', 'https://ava-olo-monitoring-dashboards.eu-central-1.awsapprunner.com')

@app.get("/", response_class=HTMLResponse)
async def dashboard_hub():
    """Main landing page with dashboard selection"""
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌾 AVA OLO Dashboard Hub</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .logo {{
            font-size: 3rem;
            font-weight: 700;
            color: #2e7d32;
            margin-bottom: 0.5rem;
        }}
        
        .tagline {{
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 1rem;
        }}
        
        .status {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: #e8f5e9;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            color: #2e7d32;
        }}
        
        .status-dot {{
            width: 8px;
            height: 8px;
            background: #4caf50;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        
        .container {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }}
        
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
            max-width: 900px;
            width: 100%;
        }}
        
        .dashboard-card {{
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
        }}
        
        .dashboard-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        }}
        
        .dashboard-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #2e7d32, #4caf50);
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }}
        
        .dashboard-card:hover::before {{
            transform: scaleX(1);
        }}
        
        .card-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
        
        .card-title {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #333;
        }}
        
        .card-description {{
            color: #666;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }}
        
        .card-features {{
            list-style: none;
            margin-bottom: 1.5rem;
        }}
        
        .card-features li {{
            padding: 0.5rem 0;
            color: #555;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .card-features li::before {{
            content: '✓';
            color: #4caf50;
            font-weight: bold;
        }}
        
        .card-action {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: #2e7d32;
            font-weight: 600;
            font-size: 1.1rem;
        }}
        
        .footer {{
            background: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }}
        
        .tech-stack {{
            display: flex;
            gap: 2rem;
            justify-content: center;
            margin-top: 1rem;
            flex-wrap: wrap;
        }}
        
        .tech-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .principles {{
            background: #f5f7fa;
            padding: 2rem;
            text-align: center;
            margin-top: 2rem;
        }}
        
        .principles h3 {{
            color: #2e7d32;
            margin-bottom: 1rem;
        }}
        
        .principles-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            max-width: 1200px;
            margin: 0 auto;
            margin-top: 1.5rem;
        }}
        
        .principle {{
            background: white;
            padding: 1rem;
            border-radius: 8px;
            font-size: 0.9rem;
            color: #555;
        }}
        
        @media (max-width: 768px) {{
            .dashboard-grid {{
                grid-template-columns: 1fr;
            }}
            
            .logo {{
                font-size: 2rem;
            }}
            
            .tech-stack {{
                flex-direction: column;
                gap: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1 class="logo">🌾 AVA OLO Dashboard Hub</h1>
        <p class="tagline">Agricultural Intelligence & Business Analytics Platform</p>
        <div class="status">
            <span class="status-dot"></span>
            <span>All Systems Operational</span>
        </div>
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
                    Open Database Dashboard 
                    <span style="font-size: 1.2rem;">→</span>
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
                    Open Business Dashboard 
                    <span style="font-size: 1.2rem;">→</span>
                </div>
            </a>
        </div>
    </div>
    
    <div class="principles">
        <h3>🏛️ Constitutional Principles</h3>
        <p style="color: #666; margin-bottom: 1rem;">Built with privacy, sustainability, and farmer-centricity at its core</p>
        <div class="principles-grid">
            <div class="principle">🔒 Privacy-First</div>
            <div class="principle">🌍 Global-Ready</div>
            <div class="principle">👨‍🌾 Farmer-Centric</div>
            <div class="principle">🤖 AI-Powered</div>
            <div class="principle">⚡ Production-Ready</div>
            <div class="principle">🥭 Mango Compliant</div>
        </div>
    </div>
    
    <div class="footer">
        <p>© 2024 AVA OLO Agricultural Intelligence Platform</p>
        <div class="tech-stack">
            <div class="tech-item">
                <span>⚡</span>
                <span>Powered by FastAPI</span>
            </div>
            <div class="tech-item">
                <span>🐘</span>
                <span>PostgreSQL Database</span>
            </div>
            <div class="tech-item">
                <span>🤖</span>
                <span>OpenAI GPT-4</span>
            </div>
            <div class="tech-item">
                <span>☁️</span>
                <span>AWS App Runner</span>
            </div>
        </div>
        <p style="margin-top: 1rem; font-size: 0.8rem; color: #999;">
            Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
        </p>
    </div>
</body>
</html>
"""
    
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {{
        "status": "healthy",
        "service": "Dashboard Hub",
        "timestamp": datetime.now().isoformat()
    }}

if __name__ == "__main__":
    import uvicorn
    print("🌾 Starting AVA OLO Dashboard Hub")
    uvicorn.run(app, host="0.0.0.0", port=8000)