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
        "version": "aws-v1.2",
        "deployment_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "DEPLOYED",
        "environment": "AWS App Runner",
        "platform": "FastAPI"
    }

def check_database_simple():
    """
    Simple database check - just test connection
    """
    try:
        import psycopg2
        import os
        
        # Get environment variables
        db_host = os.getenv('DB_HOST')
        if not db_host:
            return {
                "status": "FAILED",
                "error": "DB_HOST environment variable not found",
                "connection": "Not configured"
            }
        
        # Test basic connection
        conn = psycopg2.connect(
            host=db_host,
            database=os.getenv('DB_NAME', 'farmer_crm'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432'),
            connect_timeout=5  # Quick timeout
        )
        
        # Simple test query
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        conn.close()
        
        return {
            "status": "CONNECTED",
            "database": "farmer_crm",
            "connection": "AWS RDS",
            "test_query": "SUCCESS"
        }
        
    except Exception as e:
        return {
            "status": "FAILED",
            "database": "farmer_crm",
            "connection": "AWS RDS Connection Failed",
            "error": str(e)[:100]  # Limit error length
        }

@app.get("/")
def root():
    return {"message": "AVA OLO Health Dashboard", "version": "1.2"}

@app.get("/health/", response_class=HTMLResponse)
def health():
    """Simple HTML health page"""
    deployment = get_deployment_info()
    database = check_database_simple()  # Add this line
    
    # Update status based on database
    overall_status = "HEALTHY" if database["status"] == "CONNECTED" else "WARNING"
    
    # Update HTML to include database info
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AVA OLO Health Check Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .status {{ font-size: 24px; font-weight: bold; margin: 20px 0; }}
            .healthy {{ color: green; }}
            .warning {{ color: orange; }}
            .section {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .deployment {{ background: #e6f3ff; }}
            .database {{ background: #f0fff0; }}
        </style>
    </head>
    <body>
        <h1>🏥 AVA OLO Health Check Dashboard</h1>
        
        <div class="status {'healthy' if overall_status == 'HEALTHY' else 'warning'}">
            System Status: {overall_status}
        </div>
        
        <div class="section deployment">
            <h3>🚀 Deployment Information</h3>
            <p><strong>Version:</strong> {deployment['version']}</p>
            <p><strong>Deployed:</strong> {deployment['deployment_time']}</p>
            <p><strong>Environment:</strong> {deployment['environment']}</p>
            <p><strong>Status:</strong> {deployment['status']}</p>
        </div>
        
        <div class="section database">
            <h3>🗄️ Database Status</h3>
            <p><strong>Status:</strong> <span style="color: {'green' if database['status'] == 'CONNECTED' else 'red'}">{database['status']}</span></p>
            <p><strong>Database:</strong> {database['database']}</p>
            <p><strong>Connection:</strong> {database['connection']}</p>
            {f"<p><strong>Error:</strong> {database['error']}</p>" if database['status'] == 'FAILED' else ""}
        </div>
        
        <p><small>Last updated: {deployment['deployment_time']}</small></p>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/api/health")
def api_health():
    deployment = get_deployment_info()
    database = check_database_simple()
    return {
        "status": "healthy" if database["status"] == "CONNECTED" else "warning",
        "service": "health-dashboard",
        "deployment": deployment,
        "database": database
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', '8080'))
    print(f"Starting AVA OLO Health Dashboard on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)