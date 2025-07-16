"""
🏛️ CAVA Routes for Main API
Integrates CAVA directly into the main FastAPI app
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging
import uuid

from implementation.cava.universal_conversation_engine import CAVAUniversalConversationEngine

logger = logging.getLogger(__name__)

# Create router
cava_router = APIRouter(prefix="/api/v1/cava", tags=["CAVA"])

# Global CAVA instance
_cava_engine = None

async def get_cava_engine():
    """Get or create CAVA engine instance"""
    global _cava_engine
    
    # Try to get from app state first (shared with main app)
    try:
        from fastapi import FastAPI
        app = FastAPI()
        if hasattr(app.state, 'cava_engine') and app.state.cava_engine:
            _cava_engine = app.state.cava_engine
            logger.info("✅ CAVA Routes: Using shared engine from app state")
            return _cava_engine
    except:
        pass
    
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
    # CRITICAL LOGGING
    logger.error(f"🔥🔥🔥 CAVA DIRECT /register CALLED! Message: '{request.message}'")
    logger.info(f"📨 CAVA Route: Received registration request - farmer_id: {request.farmer_id}, message: '{request.message}', session_id: {request.session_id}")
    try:
        engine = await get_cava_engine()
        logger.info("✅ CAVA Route: Engine obtained successfully")
        result = await engine.handle_farmer_message(
            farmer_id=request.farmer_id,
            message=request.message,
            session_id=request.session_id,
            channel="registration"
        )
        logger.info(f"✅ CAVA Route: Message handled successfully - result: {result}")
        return CAVAResponse(
            success=result.get("success", True),
            message=result.get("message", ""),
            session_id=result.get("session_id", ""),
            completed="complete" in result.get("message", "").lower()
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Provide more specific error messages based on error type
        error_str = str(e).lower()
        error_type = type(e).__name__
        
        # ENHANCED ERROR REPORTING FOR DEBUGGING
        logger.error(f"🔥🔥🔥 CAVA ERROR TYPE: {error_type}")
        logger.error(f"🔥🔥🔥 CAVA ERROR MSG: {str(e)}")
        
        if "connection" in error_str or "redis" in error_str:
            error_message = f"I'm having connection issues. Let me try again. What's your full name? [Debug: {error_type}]"
        elif "openai" in error_str or "api" in error_str:
            error_message = f"I'm having trouble with my AI service. Please tell me your full name. [Debug: {str(e)[:100]}]"
        else:
            # Include actual error in response for debugging
            error_message = f"I'm having trouble processing your message. What's your full name? [Debug: {error_type}: {str(e)[:150]}]"
        
        # Return a valid response even on error
        return CAVAResponse(
            success=False,
            message=error_message,
            session_id=request.session_id or str(uuid.uuid4()),
            completed=False
        )