# main.py - Gradual restoration of health dashboard
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import datetime
import os

app = FastAPI(title="AVA OLO Health Dashboard")

def get_deployment_info():
    """
    Safe deployment info - no subprocess calls
    """
    return {
        "version": "aws-v1.1",
        "deployment_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "DEPLOYED",
        "environment": "AWS",
        "platform": "App Runner"
    }

@app.get("/")
def root():
    return {"message": "AVA OLO Health Dashboard", "version": "1.1"}

@app.get("/health/", response_class=HTMLResponse)
def health():
    """Simple HTML health page"""
    deployment = get_deployment_info()
    
    html_content = f"""
    <html>
        <head>
            <title>AVA OLO Health Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .status {{ color: green; font-weight: bold; }}
                .info {{ background: #f0f0f0; padding: 10px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>🏥 AVA OLO Health Dashboard</h1>
            <div class="info">
                <h2>System Status: <span class="status">HEALTHY</span></h2>
                <h3>Deployment Info:</h3>
                <ul>
                    <li>Version: {deployment['version']}</li>
                    <li>Deployed: {deployment['deployment_time']}</li>
                    <li>Environment: {deployment['environment']}</li>
                    <li>Platform: {deployment['platform']}</li>
                </ul>
            </div>
        </body>
    </html>
    """
    return html_content

@app.get("/api/health")
def api_health():
    deployment = get_deployment_info()
    return {
        "status": "healthy",
        "service": "health-dashboard",
        "deployment": deployment
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', '8080'))
    print(f"Starting AVA OLO Health Dashboard on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)