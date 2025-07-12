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

# Try to import the main constitutional app
try:
    logger.info("Attempting to import constitutional API gateway...")
    from api_gateway_constitutional import app as constitutional_app
    app = constitutional_app
    logger.info("✅ Constitutional API gateway imported successfully")
    
except ImportError as e:
    logger.warning(f"Constitutional gateway import failed: {e}")
    logger.info("Falling back to simple API gateway...")
    
    try:
        from api_gateway_simple import app as simple_app
        app = simple_app
        logger.info("✅ Simple API gateway imported successfully")
        
    except ImportError as e2:
        logger.error(f"Simple gateway import also failed: {e2}")
        logger.info("Creating minimal fallback app...")
        
        # Create minimal fallback app
        app = FastAPI(
            title="AVA OLO Agricultural System - Fallback",
            description="Minimal fallback application",
            version="1.0.0"
        )
        
        @app.get("/")
        def root():
            return {
                "status": "operational",
                "message": "AVA OLO Agricultural System - Fallback Mode",
                "note": "Main application modules failed to import",
                "constitutional_compliance": False,
                "import_errors": [str(e), str(e2)]
            }
        
        @app.get("/health")
        def health():
            return {
                "status": "degraded",
                "service": "ava-olo-fallback",
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