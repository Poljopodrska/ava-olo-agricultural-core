#!/usr/bin/env python3
"""
Emergency minimal API for debugging AWS deployment
"""
print("🚀 EMERGENCY STARTUP: Starting application...")
import sys
import traceback

try:
    print("🚀 STARTUP: Basic imports...")
    from fastapi import FastAPI
    print("✅ FastAPI imported")
    
    from pydantic import BaseModel
    print("✅ Pydantic imported")
    
    import os
    print("✅ OS imported")
    
    import uvicorn
    print("✅ Uvicorn imported")
    
    print("🚀 STARTUP: Creating FastAPI app...")
    app = FastAPI(title="AVA OLO Emergency API", version="0.0.1")
    print("✅ FastAPI app created")
    
except Exception as e:
    print(f"❌ STARTUP CRASH during imports: {e}")
    traceback.print_exc()
    sys.exit(1)

# Basic health endpoint only
@app.get("/")
async def basic_health():
    return {"status": "emergency_app_working", "message": "Minimal app started successfully"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ava-olo-emergency", "version": "0.0.1"}

print("✅ STARTUP: Application setup complete")

if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 8080))
        print(f"🚀 Starting server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        print(f"❌ STARTUP CRASH during server start: {e}")
        traceback.print_exc()
        sys.exit(1)