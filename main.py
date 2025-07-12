#!/usr/bin/env python3
"""
Emergency minimal main.py for constitutional deployment
Only includes health dashboard with constitutional compliance
"""
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import datetime
import os

app = FastAPI(title="AVA OLO Constitutional Health Check")

def get_deployment_info():
    """Safe deployment info - constitutional approach"""
    return {
        "version": "constitutional-emergency-v1.0",
        "deployment_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "DEPLOYED",
        "environment": "AWS App Runner",
        "platform": "FastAPI Constitutional"
    }

def check_database_constitutional():
    """Constitutional database check with maximum safety"""
    try:
        import psycopg2
        
        # Constitutional approach: safe connection
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME', 'farmer_crm'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432'),
            connect_timeout=5
        )
        
        cursor = conn.cursor()
        
        # Constitutional: Only safe basic queries
        cursor.execute("SELECT COUNT(*) FROM farmers")
        farmer_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "status": "CONNECTED",
            "database": "farmer_crm",
            "farmers": farmer_count,
            "tables": table_count,
            "constitutional_compliance": farmer_count > 0 and table_count > 0
        }
        
    except Exception as e:
        return {
            "status": "FAILED",
            "error": str(e)[:100],
            "constitutional_compliance": False
        }

@app.get("/")
async def root():
    return {
        "message": "AVA OLO Constitutional Emergency Dashboard", 
        "status": "operational",
        "constitutional_compliance": True,
        "health_endpoint": "/health/",
        "note": "Emergency deployment - full dashboard loading"
    }

@app.get("/health/")
async def health():
    """Constitutional health dashboard"""
    deployment = get_deployment_info()
    database = check_database_constitutional()
    
    overall_status = "HEALTHY" if database.get("constitutional_compliance", False) else "WARNING"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AVA OLO Constitutional Health Check</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .status {{ font-size: 24px; font-weight: bold; margin: 20px 0; text-align: center; }}
            .healthy {{ color: #28a745; }}
            .warning {{ color: #ffc107; }}
            .section {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 AVA OLO Constitutional Health Check</h1>
            
            <div class="status {'healthy' if overall_status == 'HEALTHY' else 'warning'}">
                System Status: {overall_status}
                {'✅' if overall_status == 'HEALTHY' else '⚠️'}
            </div>
            
            <div class="section">
                <h3>🚀 Emergency Deployment Info</h3>
                <p><strong>Version:</strong> {deployment['version']}</p>
                <p><strong>Environment:</strong> {deployment['environment']}</p>
                <p><strong>Deployed:</strong> {deployment['deployment_time']}</p>
                <p><strong>Status:</strong> {deployment['status']}</p>
            </div>
            
            <div class="section">
                <h3>🗄️ Database Status</h3>
                <p><strong>Connection:</strong> <span style="color: {'green' if database['status'] == 'CONNECTED' else 'red'}">{database['status']}</span></p>
                {f"<p><strong>Farmers:</strong> {database.get('farmers', 'N/A')}</p>" if database['status'] == 'CONNECTED' else ""}
                {f"<p><strong>Tables:</strong> {database.get('tables', 'N/A')}</p>" if database['status'] == 'CONNECTED' else ""}
                {f"<p><strong>Constitutional Compliance:</strong> {'✅ COMPLIANT' if database.get('constitutional_compliance') else '⚠️ CHECK NEEDED'}</p>" if database['status'] == 'CONNECTED' else ""}
                {f"<p style='color: red;'><strong>Error:</strong> {database.get('error', 'Unknown error')}</p>" if database['status'] == 'FAILED' else ""}
            </div>
            
            <div style="text-align: center; margin-top: 30px; color: #6c757d;">
                <p>🥭 Mango Rule Compliant | 🧠 LLM-First Architecture</p>
                <p>Emergency Constitutional Deployment</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/api/health")
async def api_health():
    deployment = get_deployment_info()
    database = check_database_constitutional()
    return {
        "status": "healthy" if database.get("constitutional_compliance", False) else "warning",
        "service": "constitutional-emergency-health",
        "deployment": deployment,
        "database": database
    }

if __name__ == "__main__":
    print("🚨 Starting AVA OLO Constitutional Emergency Deployment")
    uvicorn.run(app, host="0.0.0.0", port=8080)