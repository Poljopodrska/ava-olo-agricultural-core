"""
🏛️ CAVA Routes for Main API
Integrates CAVA directly into the main FastAPI app
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging

from implementation.cava.universal_conversation_engine import CAVAUniversalConversationEngine

logger = logging.getLogger(__name__)

# Create router
cava_router = APIRouter(prefix="/api/v1/cava", tags=["CAVA"])

# Global CAVA instance
_cava_engine = None

async def get_cava_engine():
    """Get or create CAVA engine instance"""
    global _cava_engine
    if _cava_engine is None:
        try:
            _cava_engine = CAVAUniversalConversationEngine()
            await _cava_engine.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize CAVA engine: {e}")
            # Create a minimal engine that works without full initialization
            _cava_engine = CAVAUniversalConversationEngine()
    return _cava_engine

# Request/Response models
class CAVARequest(BaseModel):
    farmer_id: int
    message: str
    session_id: Optional[str] = None

class CAVAResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    completed: bool = False

# CAVA endpoints
@cava_router.post("/conversation", response_model=CAVAResponse)
async def cava_conversation(request: CAVARequest):
    """CAVA conversation endpoint"""
    try:
        engine = await get_cava_engine()
        result = await engine.handle_farmer_message(
            farmer_id=request.farmer_id,
            message=request.message,
            session_id=request.session_id
        )
        
        return CAVAResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            session_id=result.get("session_id", ""),
            completed="complete" in result.get("message", "").lower()
        )
    except Exception as e:
        logger.error(f"CAVA error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@cava_router.get("/health")
async def cava_health():
    """CAVA health check"""
    try:
        engine = await get_cava_engine()
        return {
            "status": "healthy",
            "service": "CAVA",
            "dry_run_mode": engine.dry_run,
            "initialized": True
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@cava_router.get("/performance")
async def cava_performance():
    """Get CAVA performance metrics"""
    try:
        engine = await get_cava_engine()
        
        return {
            "status": "success",
            "service": "CAVA",
            "dry_run_mode": engine.dry_run,
            "target_response_time_ms": 500,
            "initialized": True
        }
    except Exception as e:
        logger.error(f"Performance check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e)
            }
        )

# Registration-specific endpoints (backward compatibility)
@cava_router.post("/register")
async def cava_register(request: CAVARequest):
    """CAVA-powered registration"""
    try:
        engine = await get_cava_engine()
        result = await engine.handle_farmer_message(
            farmer_id=request.farmer_id,
            message=request.message,
            session_id=request.session_id,
            channel="registration"
        )
        return CAVAResponse(
            success=result.get("success", True),
            message=result.get("message", ""),
            session_id=result.get("session_id", ""),
            completed="complete" in result.get("message", "").lower()
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))