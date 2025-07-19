#!/usr/bin/env python3
"""
🚨 EMERGENCY CACHE-BUSTING FILE - New entry point to force AWS rebuild
Emergency deployment fix: 2025-07-19 07:59 CEST
CACHE_BUST_SIGNATURE: b7791d2_emergency_main_py
"""
import os
import sys
import traceback
from datetime import datetime

def emergency_log(message):
    """Emergency logging that goes to stdout (shows in AWS logs)"""
    timestamp = datetime.now().isoformat()
    print(f"🚨 EMERGENCY LOG {timestamp}: {message}", flush=True)
    sys.stdout.flush()

emergency_log("=== CACHE-BUSTING MAIN.PY STARTUP ===")
emergency_log(f"Python version: {sys.version}")
emergency_log(f"Working directory: {os.getcwd()}")
emergency_log("Attempting to import api_gateway_minimal...")

try:
    from api_gateway_minimal import app
    emergency_log("✅ Successfully imported app from api_gateway_minimal")
except Exception as e:
    emergency_log(f"❌ Failed to import api_gateway_minimal: {e}")
    sys.exit(1)

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