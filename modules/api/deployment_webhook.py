"""
Deployment Webhook Handler
Automatically verifies deployments and sends alerts on failures
"""
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import httpx
import json
import os

router = APIRouter(prefix="/api/deployment", tags=["deployment-webhook"])

# Service configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "monitoring-dashboards")
ALB_URL = os.getenv("ALB_URL", "http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com")
DEPLOYMENT_ALERTS_FILE = "/tmp/deployment-alerts.json"

class DeploymentPayload(BaseModel):
    """CodeBuild deployment notification"""
    version: str
    build_id: str
    service: str
    build_status: str
    timestamp: Optional[str] = None

class DeploymentAlert(BaseModel):
    """Deployment failure alert"""
    service: str
    expected_version: str
    actual_version: str
    build_id: str
    timestamp: str
    error: Optional[str] = None

async def check_deployed_version() -> str:
    """Check the currently deployed version"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ALB_URL}/version")
            if response.status_code == 200:
                data = response.json()
                return data.get("version", "unknown")
    except Exception as e:
        return f"error: {str(e)}"
    return "unknown"

async def send_deployment_alert(alert: DeploymentAlert):
    """Send deployment failure alert"""
    # For now, write to file - in production, send to SNS/Slack/Email
    try:
        alerts = []
        if os.path.exists(DEPLOYMENT_ALERTS_FILE):
            with open(DEPLOYMENT_ALERTS_FILE, 'r') as f:
                alerts = json.load(f)
        
        alerts.append(alert.dict())
        
        # Keep only last 100 alerts
        alerts = alerts[-100:]
        
        with open(DEPLOYMENT_ALERTS_FILE, 'w') as f:
            json.dump(alerts, f, indent=2)
        
        # Log to console
        print(f"DEPLOYMENT ALERT: {json.dumps(alert.dict(), indent=2)}")
        
    except Exception as e:
        print(f"Failed to send alert: {e}")

@router.post("/webhook")
async def deployment_webhook(payload: DeploymentPayload, background_tasks: BackgroundTasks):
    """
    Webhook called by CodeBuild after deployment
    Verifies the deployment succeeded and alerts on failure
    """
    # Only process successful builds
    if payload.build_status != "SUCCEEDED":
        return {
            "acknowledged": True,
            "action": "skipped",
            "reason": f"Build status: {payload.build_status}"
        }
    
    # Only process our service
    if payload.service != SERVICE_NAME:
        return {
            "acknowledged": True,
            "action": "skipped",
            "reason": f"Different service: {payload.service}"
        }
    
    # Wait a bit for deployment to propagate
    import asyncio
    await asyncio.sleep(30)
    
    # Check deployed version
    actual_version = await check_deployed_version()
    expected_version = payload.version
    
    # Verify deployment
    verified = actual_version == expected_version
    
    result = {
        "service": SERVICE_NAME,
        "expected_version": expected_version,
        "actual_version": actual_version,
        "verified": verified,
        "build_id": payload.build_id,
        "timestamp": datetime.now().isoformat()
    }
    
    # Send alert if verification failed
    if not verified:
        alert = DeploymentAlert(
            service=SERVICE_NAME,
            expected_version=expected_version,
            actual_version=actual_version,
            build_id=payload.build_id,
            timestamp=datetime.now().isoformat(),
            error="Version mismatch after deployment"
        )
        background_tasks.add_task(send_deployment_alert, alert)
    
    return result

@router.get("/alerts")
async def get_deployment_alerts(limit: int = 10):
    """Get recent deployment alerts"""
    try:
        if os.path.exists(DEPLOYMENT_ALERTS_FILE):
            with open(DEPLOYMENT_ALERTS_FILE, 'r') as f:
                alerts = json.load(f)
                return {
                    "alerts": alerts[-limit:],
                    "total": len(alerts)
                }
    except Exception as e:
        return {"alerts": [], "error": str(e)}
    
    return {"alerts": [], "total": 0}

@router.delete("/alerts")
async def clear_deployment_alerts():
    """Clear all deployment alerts"""
    try:
        if os.path.exists(DEPLOYMENT_ALERTS_FILE):
            os.remove(DEPLOYMENT_ALERTS_FILE)
        return {"status": "cleared"}
    except Exception as e:
        return {"status": "error", "error": str(e)}