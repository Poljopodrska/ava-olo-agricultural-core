from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime

router = APIRouter(prefix="/api/v1/health", tags=["health"])

@router.get("")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={
        "status": "healthy",
        "service": "agricultural-core",
        "timestamp": datetime.now().isoformat()
    })

@router.get("/detailed")
async def health_detailed():
    """Detailed health check"""
    return JSONResponse(content={
        "status": "healthy",
        "service": "agricultural-core",
        "components": {
            "api": "operational",
            "auth": "operational",
            "chat": "operational"
        },
        "timestamp": datetime.now().isoformat()
    })