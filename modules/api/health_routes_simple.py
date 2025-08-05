#!/usr/bin/env python3
"""
Simple health API routes for AVA OLO Agricultural Core
Minimal dependencies for Phase 2 deployment
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from ..core.config import VERSION, BUILD_ID

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/health", tags=["health"])

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    try:
        return JSONResponse({
            "status": "healthy",
            "version": VERSION,
            "build_id": BUILD_ID,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e),
            "version": VERSION
        }, status_code=503)

@router.get("/simple")
async def simple_health():
    """Very simple health check"""
    return JSONResponse({
        "status": "ok",
        "version": VERSION
    })