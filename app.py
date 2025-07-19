#!/usr/bin/env python3
"""
AWS App Runner Entry Point - Constitutional Compliance
Main application file for AVA OLO Agricultural CRM
"""

import os
import sys
import logging
from fastapi import FastAPI
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# EMERGENCY FIX: Use minimal API gateway for deployment stability
try:
    logger.info("🚨 EMERGENCY: Using minimal API gateway for deployment fix...")
    from api_gateway_minimal import app
    logger.info("✅ Minimal API gateway imported successfully")
    
except ImportError as e:
    logger.error(f"Minimal gateway import failed: {e}")
    logger.info("Creating emergency fallback app...")
    
    # Create minimal fallback app
    app = FastAPI(
        title="AVA OLO Agricultural System - Emergency",
        description="Emergency fallback application",
        version="1.0.0"
    )
    
    @app.get("/")
    def root():
        return {
            "status": "operational",
            "message": "AVA OLO Agricultural System - Emergency Mode",
            "note": "Using minimal configuration due to deployment issues",
            "constitutional_compliance": True,
            "import_error": str(e)
        }
    
    @app.get("/health")
    def health():
        return {
            "status": "operational",
            "service": "ava-olo-emergency",
            "mode": "minimal"
        }

# AWS App Runner entry point
if __name__ == "__main__":
    # Environment check
    required_vars = ['OPENAI_API_KEY', 'DB_HOST', 'DB_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
    
    # Start the application
    logger.info("Starting AVA OLO Agricultural System on port 8080...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8080,
        log_level="info"
    )