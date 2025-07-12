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
        "version": "aws-v1.3",
        "deployment_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "DEPLOYED",
        "environment": "AWS App Runner",
        "platform": "FastAPI + Constitutional Framework"
    }

def check_database_with_data():
    """
    Constitutional database check - verify farmer data exists
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
                "constitutional_compliance": False
            }
        
        # Connect to database
        conn = psycopg2.connect(
            host=db_host,
            database=os.getenv('DB_NAME', 'farmer_crm'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432'),
            connect_timeout=5
        )
        
        cursor = conn.cursor()
        
        # Constitutional checks - get actual counts
        cursor.execute("SELECT COUNT(*) FROM farmers")
        farmer_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fields")
        field_count = cursor.fetchone()[0]
        
        # Check if system has data (constitutional compliance)
        has_farmers = farmer_count > 0
        has_tables = table_count > 30  # Reasonable table count
        has_fields = field_count >= 0  # Can be 0 for new system
        
        constitutional_compliance = has_farmers and has_tables
        
        conn.close()
        
        return {
            "status": "CONNECTED",
            "database": "farmer_crm",
            "connection": "AWS RDS",
            "farmers": farmer_count,
            "tables": table_count,
            "fields": field_count,
            "constitutional_compliance": constitutional_compliance,
            "data_health": "HEALTHY" if constitutional_compliance else "WARNING"
        }
        
    except Exception as e:
        return {
            "status": "FAILED",
            "database": "farmer_crm",
            "connection": "AWS RDS Connection Failed",
            "error": str(e)[:100],
            "constitutional_compliance": False
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
    return {
        "message": "AVA OLO Health Dashboard", 
        "version": "1.3",
        "health_endpoint": "/health/",
        "note": "Visit /health/ for the full dashboard"
    }

@app.get("/health/", response_class=HTMLResponse)
def health():
    """Simple HTML health page"""
    deployment = get_deployment_info()
    database = check_database_with_data()  # Use enhanced function
    
    # Update overall status
    overall_status = "HEALTHY" if database.get("constitutional_compliance", False) else "WARNING"
    
    # Enhanced HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AVA OLO Health Check Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .status {{ font-size: 28px; font-weight: bold; margin: 20px 0; text-align: center; }}
            .healthy {{ color: #28a745; }}
            .warning {{ color: #ffc107; }}
            .failed {{ color: #dc3545; }}
            .section {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .deployment {{ border-left: 4px solid #007bff; }}
            .database {{ border-left: 4px solid #28a745; }}
            .metric {{ display: inline-block; margin: 5px 15px 5px 0; }}
            .footer {{ text-align: center; color: #6c757d; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 AVA OLO Health Check Dashboard</h1>
            
            <div class="status {'healthy' if overall_status == 'HEALTHY' else 'warning'}">
                System Status: {overall_status}
                {'✅' if overall_status == 'HEALTHY' else '⚠️'}
            </div>
            
            <div class="section deployment">
                <h3>🚀 Deployment Information</h3>
                <div class="metric"><strong>Version:</strong> {deployment['version']}</div>
                <div class="metric"><strong>Environment:</strong> {deployment['environment']}</div>
                <div class="metric"><strong>Deployed:</strong> {deployment['deployment_time']}</div>
                <div class="metric"><strong>Status:</strong> {deployment['status']}</div>
            </div>
            
            <div class="section database">
                <h3>🗄️ Database Status</h3>
                <div class="metric">
                    <strong>Connection:</strong> 
                    <span class="{'healthy' if database['status'] == 'CONNECTED' else 'failed'}">
                        {database['status']} {'✅' if database['status'] == 'CONNECTED' else '❌'}
                    </span>
                </div>
                <div class="metric"><strong>Database:</strong> {database['database']}</div>
                
                {f'''
                <div class="metric"><strong>Farmers:</strong> {database.get('farmers', 'N/A')}</div>
                <div class="metric"><strong>Tables:</strong> {database.get('tables', 'N/A')}</div>
                <div class="metric"><strong>Fields:</strong> {database.get('fields', 'N/A')}</div>
                <div class="metric">
                    <strong>Constitutional Compliance:</strong> 
                    <span class="{'healthy' if database.get('constitutional_compliance') else 'warning'}">
                        {'✅ COMPLIANT' if database.get('constitutional_compliance') else '⚠️ CHECK NEEDED'}
                    </span>
                </div>
                ''' if database['status'] == 'CONNECTED' else f'<div class="metric" style="color: red;"><strong>Error:</strong> {database.get("error", "Unknown error")}</div>'}
            </div>
            
            <div class="footer">
                <p>Constitutional Health Dashboard | Last updated: {deployment['deployment_time']}</p>
                <p>🥭 Mango Rule Compliant | 🧠 LLM-First Architecture | 🔒 Privacy Protected</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/api/health")
def api_health():
    deployment = get_deployment_info()
    database = check_database_with_data()
    return {
        "status": "healthy" if database.get("constitutional_compliance", False) else "warning",
        "service": "health-dashboard",
        "deployment": deployment,
        "database": database
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', '8080'))
    print(f"Starting AVA OLO Health Dashboard on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)