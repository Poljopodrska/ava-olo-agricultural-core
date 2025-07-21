#!/usr/bin/env python3
"""
Feature Status Dashboard
Real-time monitoring of feature functionality, not just deployment status
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import logging
import httpx
from datetime import datetime
from typing import Dict, Any

from ..core.feature_verification import FeatureVerifier, get_feature_verification_report
from ..core.config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards/features", tags=["feature-monitoring"])

# Service URLs
AGRICULTURAL_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"
MONITORING_URL = "http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com"

@router.get("/api/verify-all")
async def verify_all_features():
    """Verify features across all services"""
    results = {}
    
    # Verify agricultural-core features
    try:
        agricultural_report = await get_feature_verification_report(
            "agricultural-core", 
            AGRICULTURAL_URL
        )
        results["agricultural_core"] = agricultural_report
    except Exception as e:
        logger.error(f"Failed to verify agricultural features: {e}")
        results["agricultural_core"] = {
            "status": "error",
            "error": str(e),
            "all_features_working": False
        }
    
    # Verify monitoring-dashboards features (self)
    try:
        monitoring_report = await get_feature_verification_report(
            "monitoring-dashboards",
            "http://localhost:8080"
        )
        results["monitoring_dashboards"] = monitoring_report
    except Exception as e:
        logger.error(f"Failed to verify monitoring features: {e}")
        results["monitoring_dashboards"] = {
            "status": "error", 
            "error": str(e),
            "all_features_working": False
        }
    
    # Overall status
    all_services_healthy = all(
        service.get("all_features_working", False) 
        for service in results.values()
    )
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "all_services_healthy": all_services_healthy,
        "services": results,
        "alert_needed": not all_services_healthy
    }

@router.get("/api/verify/{service}")
async def verify_service_features(service: str):
    """Verify features for a specific service"""
    if service == "agricultural":
        url = AGRICULTURAL_URL
    elif service == "monitoring":
        url = "http://localhost:8080"
    else:
        return {"error": "Invalid service name"}
    
    try:
        report = await get_feature_verification_report(service, url)
        return report
    except Exception as e:
        logger.error(f"Feature verification failed for {service}: {e}")
        return {
            "service": service,
            "status": "error",
            "error": str(e),
            "all_features_working": False
        }

@router.get("/", response_class=HTMLResponse)
async def feature_status_dashboard(request: Request):
    """Feature status dashboard page"""
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    # Get feature status for both services
    verification_results = await verify_all_features()
    
    return templates.TemplateResponse("feature_status_dashboard.html", {
        "request": request,
        "verification": verification_results,
        "agricultural": verification_results["services"].get("agricultural_core", {}),
        "monitoring": verification_results["services"].get("monitoring_dashboards", {}),
        "alert_active": verification_results.get("alert_needed", False)
    })

@router.post("/webhook/deployment-complete")
async def deployment_complete_webhook(payload: Dict[str, Any]):
    """Webhook to verify features and run smoke tests after deployment"""
    service = payload.get("service")
    version = payload.get("version")
    
    # Map service name to URL
    service_urls = {
        "agricultural-core": AGRICULTURAL_URL,
        "agricultural_core": AGRICULTURAL_URL,
        "monitoring-dashboards": MONITORING_URL,
        "monitoring_dashboards": MONITORING_URL
    }
    
    service_url = service_urls.get(service, AGRICULTURAL_URL)
    
    # Wait a bit for service to stabilize
    import asyncio
    await asyncio.sleep(15)
    
    # Run comprehensive verification
    from ..core.deployment_smoke_tests import verify_deployment_with_smoke_tests
    
    try:
        comprehensive_results = await verify_deployment_with_smoke_tests(
            service_name=service,
            version=version,
            base_url=service_url
        )
        
        deployment_verified = comprehensive_results.get("deployment_verified", False)
        
        if not deployment_verified:
            # Extract details of what failed
            feature_failures = extract_failed_features(
                comprehensive_results.get("feature_verification", {})
            )
            smoke_test_failures = comprehensive_results.get("smoke_test_results", {}).get("failed_test_names", [])
            
            # Send detailed alert
            await send_feature_failure_alert({
                "service": service,
                "version": version,
                "failed_features": feature_failures,
                "failed_smoke_tests": smoke_test_failures,
                "message": f"Deployment of {service} v{version} completed but verification failed!",
                "details": comprehensive_results
            })
        
        return {
            "acknowledged": True,
            "deployment_version": version,
            "deployment_verified": deployment_verified,
            "comprehensive_results": comprehensive_results
        }
        
    except Exception as e:
        logger.error(f"Deployment verification failed: {e}")
        
        # Even verification failure is important to know
        await send_feature_failure_alert({
            "service": service,
            "version": version,
            "message": f"Could not verify deployment of {service} v{version}",
            "error": str(e)
        })
        
        return {
            "acknowledged": True,
            "deployment_version": version,
            "deployment_verified": False,
            "error": str(e)
        }

def extract_failed_features(verification: Dict[str, Any]) -> list:
    """Extract list of failed features from verification report"""
    failed = []
    
    features = verification.get("features", {})
    for feature_name, feature_data in features.items():
        if feature_data.get("status") != "healthy":
            failed.append({
                "name": feature_name,
                "status": feature_data.get("status"),
                "message": feature_data.get("message", "Unknown failure")
            })
    
    return failed

async def send_feature_failure_alert(alert_data: Dict[str, Any]):
    """Send alert for feature failures"""
    logger.error(f"FEATURE FAILURE ALERT: {alert_data}")
    # In production, this would send to Slack/email/etc
    
    # Store in alert history
    try:
        from ..core.database_manager import get_db_manager
        db = get_db_manager()
        
        await db.execute_query("""
            INSERT INTO deployment_alerts (
                service, version, alert_type, 
                failed_features, message, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """, (
            alert_data.get("service"),
            alert_data.get("version"),
            "FEATURE_FAILURE",
            str(alert_data.get("failed_features")),
            alert_data.get("message"),
            datetime.utcnow()
        ))
    except Exception as e:
        logger.error(f"Failed to store alert: {e}")