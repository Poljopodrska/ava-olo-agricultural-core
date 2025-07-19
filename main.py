#!/usr/bin/env python3
"""
🚨 BULLETPROOF DEPLOYMENT - Shared verification system
Deployment fix: 2025-07-19 21:00 CEST
CACHE_BUST_SIGNATURE: bulletproof_main_py
Version: 3.2.5-bulletproof
DEPLOYMENT_TIMESTAMP: 20250719210000
"""
import os
import sys
import traceback
from datetime import datetime
import hashlib

# Import shared deployment manager
sys.path.append('../ava-olo-shared/shared')
try:
    from deployment_manager import DeploymentManager
except ImportError:
    # Fallback if shared folder not available
    class DeploymentManager:
        def __init__(self, service_name):
            self.service_name = service_name
        def generate_deployment_manifest(self, version):
            return {"service": self.service_name, "version": version}
        def verify_deployment(self):
            return {"valid": False, "error": "Deployment manager not available"}

# Service-specific deployment tracking
SERVICE_NAME = "agricultural-core"
DEPLOYMENT_TIMESTAMP = '20250719204116'  # Updated by deploy script
BUILD_ID = hashlib.md5(f"{SERVICE_NAME}-{DEPLOYMENT_TIMESTAMP}".encode()).hexdigest()[:8]
VERSION = f"v3.2.5-bulletproof-{BUILD_ID}"

deployment_manager = DeploymentManager(SERVICE_NAME)

def emergency_log(message):
    """Emergency logging that goes to stdout (shows in AWS logs)"""
    timestamp = datetime.now().isoformat()
    print(f"🚨 EMERGENCY LOG {timestamp}: {message}", flush=True)
    sys.stdout.flush()

emergency_log(f"=== BULLETPROOF DEPLOYMENT STARTUP {VERSION} ===")
emergency_log(f"Build ID: {BUILD_ID}")
emergency_log(f"Python version: {sys.version}")
emergency_log(f"Working directory: {os.getcwd()}")
emergency_log("Attempting to import api_gateway_constitutional_ui...")

try:
    from api_gateway_constitutional_ui import app
    emergency_log("✅ Successfully imported app from api_gateway_constitutional_ui")
except Exception as e:
    emergency_log(f"❌ Failed to import api_gateway_constitutional_ui: {e}")
    sys.exit(1)

# Expose app variable for uvicorn main:app
# This is required for AWS App Runner to find the FastAPI app

if __name__ == "__main__":
    import uvicorn
    emergency_log("Starting uvicorn server from main.py...")
    port = int(os.getenv("PORT", 8080))
    emergency_log(f"Using port: {port}")
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        emergency_log(f"❌ Uvicorn failed to start: {e}")
        traceback.print_exc()
        sys.exit(1)