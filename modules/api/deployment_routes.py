#!/usr/bin/env python3
"""
Deployment API routes for AVA OLO Agricultural Core
Handles deployment verification and health checks
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os
import traceback
from datetime import datetime

from ..core.config import VERSION, BUILD_ID, DEPLOYMENT_TIMESTAMP, CAVA_VERSION, emergency_log
from ..core.deployment_manager import get_deployment_manager, verify_deployment, get_deployment_info

router = APIRouter(tags=["deployment"])

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    try:
        return JSONResponse({
            "status": "healthy",
            "version": VERSION,
            "cava_version": CAVA_VERSION,
            "build_id": BUILD_ID,
            "service": "agricultural-core",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        emergency_log(f"Health check failed: {e}")
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e),
            "version": VERSION
        }, status_code=503)

@router.get("/api/deployment/verify")
async def deployment_verify():
    """Verify deployment and return version information"""
    try:
        deployment_info = get_deployment_info()
        verification = verify_deployment()
        
        return JSONResponse({
            "status": "operational",
            "version": VERSION,
            "cava_version": CAVA_VERSION,
            "build_id": BUILD_ID,
            "deployment_timestamp": DEPLOYMENT_TIMESTAMP,
            "verification": verification,
            "deployment_info": deployment_info,
            "environment": "production" if os.getenv('AWS_EXECUTION_ENV') else "local"
        })
    except Exception as e:
        emergency_log(f"Deployment verify failed: {e}")
        return JSONResponse({
            "status": "error",
            "version": VERSION,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

@router.get("/api/deployment/health")
async def deployment_health():
    """Health check endpoint for deployment verification"""
    try:
        manager = get_deployment_manager()
        manifest_exists = manager._check_manifest_exists()
        
        return JSONResponse({
            "status": "healthy",
            "version": VERSION,
            "cava_version": CAVA_VERSION,
            "build_id": BUILD_ID,
            "service": "agricultural-core",
            "timestamp": datetime.now().isoformat(),
            "manifest_exists": manifest_exists,
            "deployment_valid": True
        })
    except Exception as e:
        emergency_log(f"Deployment health check failed: {e}")
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e),
            "version": VERSION
        }, status_code=503)

@router.get("/api/v1/deployment/verify")
async def v1_deployment_verify():
    """V1 API deployment verification endpoint"""
    return await deployment_verify()

@router.get("/api/test-llm")
async def test_llm():
    """Test LLM connectivity"""
    try:
        # Import LLM service
        from implementation.language_processor import get_assistant_response
        
        # Test with a simple query
        test_response = await get_assistant_response(
            "What crops grow in Bulgaria?",
            farmer_id="test_farmer",
            language="en"
        )
        
        return JSONResponse({
            "status": "success",
            "llm_available": True,
            "test_query": "What crops grow in Bulgaria?",
            "response_preview": test_response[:100] if test_response else None,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        emergency_log(f"LLM test failed: {e}")
        return JSONResponse({
            "status": "error",
            "llm_available": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=500)