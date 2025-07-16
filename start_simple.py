#!/usr/bin/env python3
"""
Minimal startup script for AWS App Runner
Starts the API without CAVA or complex dependencies
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Setup logging immediately
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Disable CAVA for stable deployment
os.environ['DISABLE_CAVA'] = 'true'
os.environ['CAVA_DRY_RUN_MODE'] = 'true'

logger.info("🚀 Starting Simple API Gateway...")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
logger.info(f"Files in directory: {os.listdir('.')}")

try:
    # Import after setting environment variables
    import uvicorn
    from api_gateway_minimal import app
    
    logger.info("✅ Successfully imported FastAPI app")
    
    # Get port from environment or default
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"🌐 Starting server on port {port}")
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
    
except Exception as e:
    logger.error(f"❌ Failed to start application: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)