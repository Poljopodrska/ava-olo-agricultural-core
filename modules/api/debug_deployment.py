#!/usr/bin/env python3
"""
Debug deployment endpoints to verify actual running code
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os
from datetime import datetime
from modules.core.config import VERSION, BUILD_ID, DEPLOYMENT_TIMESTAMP

router = APIRouter(prefix="/api/debug", tags=["debug"])

@router.get("/deployment/code-check")
async def code_check():
    """Check if specific code features exist"""
    
    # Check what code features are present
    features = {
        "pure_chat_exists": False,
        "validation_removed": False,
        "old_registration_exists": False,
        "version_string": VERSION,
        "build_id": BUILD_ID,
        "deployment_timestamp": DEPLOYMENT_TIMESTAMP
    }
    
    # Check if pure_chat module exists
    try:
        import modules.cava.pure_chat
        features["pure_chat_exists"] = True
    except ImportError:
        pass
    
    # Check if old validation code exists
    try:
        from modules.cava.registration_flow import RegistrationFlow
        flow = RegistrationFlow()
        # If this exists, old code is still there
        if hasattr(flow, 'validate_input'):
            features["old_registration_exists"] = True
    except:
        features["validation_removed"] = True
    
    # Check environment
    features["environment"] = {
        "aws_execution_env": os.getenv("AWS_EXECUTION_ENV"),
        "ecs_container_metadata": os.getenv("ECS_CONTAINER_METADATA_URI_V4") is not None,
        "task_arn": os.getenv("ECS_TASK_ARN", "Not in ECS"),
        "container_name": os.getenv("ECS_CONTAINER_NAME", "Unknown")
    }
    
    # Check file timestamps
    features["file_checks"] = {}
    
    files_to_check = [
        "/app/modules/cava/pure_chat.py",
        "/app/templates/pure_chat.html",
        "/app/modules/cava/registration_flow.py"
    ]
    
    for filepath in files_to_check:
        if os.path.exists(filepath):
            stat = os.stat(filepath)
            features["file_checks"][filepath] = {
                "exists": True,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size": stat.st_size
            }
        else:
            features["file_checks"][filepath] = {"exists": False}
    
    return JSONResponse(content={
        "deployment_debug": features,
        "expected_version": "v3.3.31-CAVA-step-1-pure",
        "validation_should_be_gone": True,
        "timestamp": datetime.utcnow().isoformat()
    })

@router.get("/deployment/endpoints")
async def check_endpoints():
    """List all available endpoints"""
    
    endpoints = {
        "chat_endpoints": [
            "/api/v1/registration/chat",
            "/api/v1/registration/cava", 
            "/api/v1/registration/cava/natural",
            "/api/v1/registration/cava/true"
        ],
        "ui_endpoints": [
            "/auth/register",
            "/auth/register/chat",
            "/auth/register/pure",
            "/auth/register/true"
        ],
        "verified_working": []
    }
    
    # Check which chat implementations are loaded
    implementations = []
    
    try:
        import modules.cava.pure_chat
        implementations.append("pure_chat")
    except:
        pass
        
    try:
        import modules.cava.simple_chat
        implementations.append("simple_chat")
    except:
        pass
        
    try:
        import modules.cava.registration_flow
        implementations.append("registration_flow (OLD)")
    except:
        pass
    
    endpoints["loaded_implementations"] = implementations
    
    return JSONResponse(content=endpoints)