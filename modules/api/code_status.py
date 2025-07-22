#!/usr/bin/env python3
"""
Code Status API - Shows actual running code characteristics
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime
import os
from modules.core.config import VERSION, BUILD_ID, DEPLOYMENT_TIMESTAMP

router = APIRouter(prefix="/api/v1", tags=["status"])

@router.get("/code-status")
async def get_code_status():
    """Return actual code characteristics and features"""
    
    # Detect which features are actually present
    features = {
        "pure_llm_chat": False,
        "validation_enabled": False,
        "hardcoded_questions": False,
        "natural_responses": False,
        "old_registration_flow": False,
        "simple_chat": False,
        "true_cava": False
    }
    
    # Check which modules exist
    try:
        import modules.cava.pure_chat
        features["pure_llm_chat"] = True
        features["natural_responses"] = True
    except ImportError:
        pass
    
    try:
        import modules.cava.simple_chat
        features["simple_chat"] = True
    except ImportError:
        pass
    
    try:
        import modules.cava.true_cava_registration
        features["true_cava"] = True
    except ImportError:
        pass
    
    try:
        from modules.cava.registration_flow import RegistrationFlow
        flow = RegistrationFlow()
        # If old flow exists with validation
        if hasattr(flow, 'validate_input'):
            features["validation_enabled"] = True
            features["hardcoded_questions"] = True
            features["old_registration_flow"] = True
    except:
        pass
    
    # Format deployment time
    try:
        dt = datetime.strptime(DEPLOYMENT_TIMESTAMP, '%Y%m%d%H%M%S')
        deployment_display = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        deployment_display = DEPLOYMENT_TIMESTAMP
    
    # Determine implementation type based on version
    implementation = "Unknown"
    if "pure" in VERSION:
        implementation = "Pure LLM Chat (No Validation)"
    elif "step-1" in VERSION:
        implementation = "Step 1 - Simple Chat"
    elif "true-cava" in VERSION:
        implementation = "True CAVA Registration"
    elif "natural" in VERSION:
        implementation = "Natural Registration Flow"
    else:
        implementation = "Standard Registration"
    
    return JSONResponse(content={
        "version": VERSION,
        "implementation": implementation,
        "features": features,
        "build_id": BUILD_ID,
        "deployment_timestamp": DEPLOYMENT_TIMESTAMP,
        "deployment_display": deployment_display,
        "environment": {
            "in_ecs": os.getenv("ECS_CONTAINER_METADATA_URI_V4") is not None,
            "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
            "has_weather_key": bool(os.getenv("OPENWEATHER_API_KEY"))
        },
        "feature_summary": _get_feature_summary(features, VERSION)
    })

def _get_feature_summary(features: dict, version: str) -> list:
    """Generate human-readable feature summary"""
    summary = []
    
    if features.get("pure_llm_chat"):
        summary.append("✅ Pure LLM Chat")
    else:
        summary.append("❌ Pure LLM Chat")
    
    if features.get("validation_enabled"):
        summary.append("⚠️ Validation: ON")
    else:
        summary.append("✅ Validation: OFF")
    
    if features.get("natural_responses"):
        summary.append("✅ Natural Responses")
    else:
        summary.append("❌ Natural Responses")
    
    if features.get("hardcoded_questions"):
        summary.append("⚠️ Hardcoded Questions")
    else:
        summary.append("✅ Dynamic Questions")
    
    # Add version-specific features
    if "v3.3.31" in version:
        summary.append("🎯 Target: Pure Chat")
    elif "v3.3.30" in version:
        summary.append("🎯 Target: Step 1")
    elif "v3.3.29" in version:
        summary.append("🎯 Target: True CAVA")
    
    return summary