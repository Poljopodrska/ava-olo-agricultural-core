from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime

router = APIRouter(prefix="/simple", tags=["simple"])

@router.get("/health")
async def simple_health():
    return JSONResponse(content={
        "status": "healthy",
        "source": "simple_router",
        "timestamp": datetime.now().isoformat()
    })