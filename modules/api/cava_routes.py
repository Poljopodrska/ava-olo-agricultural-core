#!/usr/bin/env python3
"""
CAVA Registration API routes for AVA OLO Agricultural Core
Handles CAVA registration and conversation endpoints
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..core.config import CAVA_VERSION, emergency_log

logger = logging.getLogger(__name__)

# Request/Response models
class RegistrationRequest(BaseModel):
    message: str
    farmer_id: str = "anonymous"
    language: str = "en"

class RegistrationResponse(BaseModel):
    response: str
    extracted_data: Dict[str, Any]
    registration_complete: bool
    missing_fields: List[str]
    session_id: str
    cava_version: str = CAVA_VERSION

router = APIRouter(prefix="/api/v1", tags=["cava"])

@router.post("/registration/cava", response_model=RegistrationResponse)
async def cava_registration(request: RegistrationRequest):
    """CAVA registration endpoint - handles farmer registration via chat"""
    try:
        # Import CAVA registration engine
        from cava_registration_llm import get_llm_registration_engine
        
        # Process registration message
        llm_engine = await get_llm_registration_engine()
        
        # Create session ID from farmer ID
        session_id = f"cava_{request.farmer_id}_{datetime.now().timestamp()}"
        
        # Process the message
        result = await llm_engine.process_registration_message(
            message=request.message,
            session_id=session_id,
            conversation_history=[]
        )
        
        # Prepare response
        response = RegistrationResponse(
            response=result.get('response', 'Hello! I can help you register.'),
            extracted_data=result.get('extracted_data', {}),
            registration_complete=result.get('registration_complete', False),
            missing_fields=result.get('missing_fields', []),
            session_id=session_id,
            cava_version=CAVA_VERSION
        )
        
        logger.info(f"CAVA registration processed for session {session_id}")
        return response
        
    except ImportError as e:
        emergency_log(f"CAVA import error: {e}")
        raise HTTPException(
            status_code=503,
            detail="CAVA registration service not available"
        )
    except Exception as e:
        emergency_log(f"CAVA registration error: {e}")
        logger.error(f"CAVA registration failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Registration processing failed: {str(e)}"
        )

@router.get("/cava/status")
async def cava_status():
    """Check CAVA service status"""
    try:
        # Try to import CAVA
        from cava_registration_llm import get_llm_registration_engine
        
        # Check if we can create an engine
        engine = await get_llm_registration_engine()
        
        return JSONResponse({
            "status": "operational",
            "cava_version": CAVA_VERSION,
            "engine_available": True,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "cava_version": CAVA_VERSION,
            "engine_available": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=503)

@router.get("/cava/test")
async def cava_test():
    """Test CAVA with Bulgarian mango farmer scenario"""
    try:
        from cava_registration_llm import get_llm_registration_engine
        
        # Test message
        test_message = "Здравейте, аз съм Петър и отглеждам манго в България"
        
        # Process test message
        engine = await get_llm_registration_engine()
        result = await engine.process_registration_message(
            message=test_message,
            session_id="test_bulgarian_mango",
            conversation_history=[]
        )
        
        return JSONResponse({
            "test": "bulgarian_mango_farmer",
            "input": test_message,
            "response": result.get('response'),
            "extracted": result.get('extracted_data'),
            "cava_version": CAVA_VERSION,
            "test_passed": bool(result.get('extracted_data', {}).get('first_name') == 'Петър'),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "test": "bulgarian_mango_farmer",
            "error": str(e),
            "test_passed": False,
            "timestamp": datetime.now().isoformat()
        }, status_code=500)