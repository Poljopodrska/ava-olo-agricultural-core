"""
Main entry point for AVA OLO Monitoring Dashboards
Combines all 4 dashboards into one App Runner service
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

# Import all dashboard apps
from agronomic_approval import app as agronomic_app
from business_dashboard import app as business_app
from database_explorer import app as database_app
from health_check_dashboard import app as health_app

# Create main FastAPI app
app = FastAPI(
    title="AVA OLO Constitutional Monitoring Suite",
    description="Unified constitutional monitoring dashboards for AVA OLO agricultural system",
    version="2.0.0-constitutional"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all dashboard apps on different paths
app.mount("/agronomic", agronomic_app)
app.mount("/business", business_app)
app.mount("/database", database_app)
app.mount("/health", health_app)

# Root endpoint that lists all available dashboards
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>AVA OLO Monitoring Suite</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                h1 {
                    color: #2e7d32;
                    text-align: center;
                }
                .dashboard-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-top: 30px;
                }
                .dashboard-card {
                    background: white;
                    border-radius: 8px;
                    padding: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    transition: transform 0.2s;
                }
                .dashboard-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                }
                .dashboard-card h2 {
                    color: #1976d2;
                    margin-top: 0;
                }
                .dashboard-card a {
                    display: inline-block;
                    margin-top: 10px;
                    padding: 10px 20px;
                    background-color: #2e7d32;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    transition: background-color 0.2s;
                }
                .dashboard-card a:hover {
                    background-color: #1b5e20;
                }
            </style>
        </head>
        <body>
            <h1>🌾 AVA OLO Constitutional Monitoring Suite</h1>
            <p style="text-align: center; color: #666;">Select a dashboard to monitor your constitutional agricultural system</p>
            <p style="text-align: center; color: #ff6b35; font-weight: bold;">🥭 Mango Rule Compliant | 🧠 LLM-First Architecture</p>
            
            <div class="dashboard-grid">
                <div class="dashboard-card">
                    <h2>📊 Business Dashboard</h2>
                    <p>Monitor business metrics, conversations, and farmer engagement</p>
                    <a href="/business/">Open Dashboard</a>
                </div>
                
                <div class="dashboard-card">
                    <h2>🗄️ Database Explorer</h2>
                    <p>Explore and manage your agricultural database</p>
                    <a href="/database/">Open Explorer</a>
                </div>
                
                <div class="dashboard-card">
                    <h2>🏥 Constitutional Health Monitor</h2>
                    <p>Check system health, constitutional compliance, and service status</p>
                    <a href="/health/">Open Monitor</a>
                </div>
                
                <div class="dashboard-card">
                    <h2>✅ Agronomic Approval</h2>
                    <p>Review and approve agricultural recommendations</p>
                    <a href="/agronomic/">Open Approval System</a>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 40px; color: #666; border-top: 1px solid #ddd; padding-top: 20px;">
                <p style="margin: 5px 0;"><strong>AVA OLO Constitutional Agricultural Intelligence System</strong></p>
                <p style="margin: 5px 0; font-size: 14px;">🥭 Mango Rule: Works universally for any crop in any country</p>
                <p style="margin: 5px 0; font-size: 14px;">🧠 LLM-First: Constitutional compliance with intelligent fallbacks</p>
                <p style="margin: 5px 0; font-size: 14px;">🔒 Privacy Protected | 🌍 Universal Agriculture | ⚖️ Constitutional Framework</p>
            </div>
        </body>
    </html>
    """

# Redirect /docs to main app docs
@app.get("/docs")
async def redirect_docs():
    return RedirectResponse(url="/docs")

# Health check endpoint for App Runner
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "constitutional-monitoring-suite", 
        "dashboards": 4,
        "version": "2.0.0-constitutional",
        "constitutional_compliance": True,
        "mango_rule_compliant": True
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AVA OLO Constitutional Monitoring Suite v2.0.0 on port 8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)